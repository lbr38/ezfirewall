# coding: utf-8

# Import libraries
import sys
import glob
import socket
from pathlib import Path
from colorama import Fore, Style
from tabulate import tabulate

# Import classes
from src.controllers.App import App
from src.controllers.Yaml import Yaml
from src.controllers.Rule.Merge import Merge
from src.controllers.Rule.Validate import Validate
from src.controllers.Nftables.Nftables import Nftables
from src.controllers.Nftables.Input import Input
from src.controllers.Nftables.Forward import Forward
from src.controllers.Nftables.Nat import Nat

class Rule:
    def __init__(self, nftablesController: Nftables):
        self.rules_dir = '/opt/ezfirewall/rules'
        # Tracks whether the live nftables ruleset has actually been modified.
        # Used to decide whether a backup restore is needed on failure.
        self.applied = False
        self.appController = App()
        self.yamlController = Yaml()
        self.mergeController = Merge()
        self.validateController = Validate()
        self.nftablesController = nftablesController
        self.nftablesInputController = Input()
        # Share the same JsonBuilder and Source instances so all rules end up in the same ruleset
        # and the source files are only parsed once
        self.nftablesForwardController = Forward(self.nftablesInputController.jsonBuilder, self.nftablesInputController.sourceController)
        self.nftablesNatController = Nat(self.nftablesInputController.jsonBuilder, self.nftablesInputController.sourceController)

        # Create rules directory if it does not exist
        if not Path(self.rules_dir).exists():
            print('Creating ' + self.rules_dir + ' directory: ', end = '')
            Path(self.rules_dir).mkdir(parents = True, exist_ok = True)
            print(Fore.GREEN + '✔' + Style.RESET_ALL)


    #-----------------------------------------------------------------------------------------------
    #
    #   Check whether a network interface exists on this system
    #
    #-----------------------------------------------------------------------------------------------
    def interface_exists(self, interface: str) -> bool:
        """Return True if the given interface name exists on this system.

        Uses socket.if_nameindex() instead of shelling out, avoiding any
        command injection risk from interface names read from YAML files.
        """
        try:
            return interface in [name for _, name in socket.if_nameindex()]
        except OSError:
            return False


    #-----------------------------------------------------------------------------------------------
    #
    #   Load rules files
    #
    #-----------------------------------------------------------------------------------------------
    def load(self):
        """Load, validate and merge all rules files"""
        print(' ▪ Checking rules files ', end='')

        # Get all rules files
        rules_files = sorted(glob.glob(self.rules_dir + '/*.yml'))

        # If there are no rules files, raise an exception
        if not rules_files:
            raise Exception('There is no rule to apply (no rule files were found)')

        content = {}
        warnings = []

        # Loop through every rule file
        for file in rules_files:
            # Check that every rule file is a valid YAML file
            try:
                data = self.yamlController.load(file)
            except Exception as e:
                raise Exception('Rule file ' + file + ' is not a valid YAML file: ' + str(e))

            # Ignore file if it is empty (or only contains comments)
            if data is None:
                warnings.append('Rule file ' + file + ' is empty, ignoring it')
                continue

            # Validate the rules schema to provide clear error messages
            data = self.validateController.validate(data, file)
            warnings.extend(self.validateController.warnings)

            # Merge data using the Merge class
            content = self.mergeController.merge_interfaces(content, data, file)

        if not content:
            raise Exception('No rules to apply')

        print('\r ' + Fore.GREEN + '✔' + Style.RESET_ALL)

        for warning in warnings:
            print(Fore.YELLOW + ' ▪ ' + warning + Style.RESET_ALL)

        return content


    #-----------------------------------------------------------------------------------------------
    #
    #   Apply rules
    #
    #-----------------------------------------------------------------------------------------------
    def apply(self, config: dict, dry_run=False, quiet=False, no_persist=False):
        # Load and check the rules files
        content = self.load()

        # Generate the summary table
        self.generate_summary_table(content, quiet)

        # Ask for confirmation before applying rules
        if not dry_run:
            if not quiet:
                if not self.appController.confirm(' ▪ Apply rules? [y/N] '):
                    sys.exit(0)

        #
        # Build rules
        #
        print(' ▪ Building rules', end=' ')

        # Prepare sets
        self.nftablesInputController.prepare_sets(content)

        # Build the base ruleset structure
        self.nftablesInputController.write(config)

        # Collect all rule data first for set-based approach
        rules_data = []

        # Input and output rules have the same syntax, they only end up in a different chain
        sections = [('input', 'INPUT'), ('output', 'OUTPUT')]

        # In the rules file, loop through every interface to collect their drop rules
        for interface in content:
            for ip_version in ["ipv4", "ipv6"]:
                for section, chain in sections:
                    for rule_name, rule in content[interface].get(ip_version, {}).get(section, {}).items():
                        # Note: Allow rules will be processed later to ensure proper order (DROP before ALLOW)
                        if not rule['drop']:
                            continue

                        # Collect IPs for drop set (per rule)
                        self.nftablesInputController.generate_drop_rules(ip_version, interface, rule_name, rule['drop'], rule['protocol'], rule['ports'], chain)

                        # Store rule data for later drop rule creation
                        rules_data.append({
                            'ip_version': ip_version,
                            'interface': interface,
                            'rule_name': rule_name,
                            'protocol': rule['protocol'],
                            'ports': rule['ports'],
                            'chain': chain,
                            'type': 'drop'
                        })

        # Now finalize drop sets first (priority blacklist)
        self.nftablesInputController.finalize_sets_and_rules()
        self.nftablesInputController.create_set_based_rules(rules_data)

        # Then process allow rules individually (after drops for proper priority)
        for interface in content:
            for ip_version in ["ipv4", "ipv6"]:
                if ip_version not in content[interface]:
                    continue

                # Process input and output allow rules
                for section, chain in sections:
                    for rule_name, rule in content[interface][ip_version].get(section, {}).items():
                        self.nftablesInputController.generate_allow_rules(ip_version, interface, rule['allow'], rule['protocol'], rule['ports'], chain)

                # Process forward rules
                if 'forward' in content[interface][ip_version]:
                    self.nftablesForwardController.generate_forward_rules(ip_version, content[interface][ip_version]['forward'])

                # Process NAT rules
                if 'nat' in content[interface][ip_version]:
                    self.nftablesNatController.generate_nat_rules(ip_version, content[interface][ip_version]['nat'])

        # Finalize the ruleset by adding final drop/log rules
        self.nftablesInputController.finalize()

        print('\r ' + Fore.GREEN + '✔' + Style.RESET_ALL)

        #
        # Get the built ruleset as JSON
        #
        ruleset_json = self.nftablesInputController.get_ruleset_json()

        #
        # Check if the rules are valid
        #
        print(' ▪ Checking rules', end=' ')
        self.nftablesController.check(ruleset_json)
        print('\r ' + Fore.GREEN + '✔' + Style.RESET_ALL)

        #
        # Apply rules (if not dry run)
        #
        if not dry_run:
            print(' ▪ Applying rules', end=' ')
            self.nftablesController.apply(ruleset_json)
            # The live ruleset has now been modified
            self.applied = True
            print('\r ' + Fore.GREEN + '✔' + Style.RESET_ALL)

            # Save to /etc/nftables.conf for persistence (unless --no-persist is used)
            if not no_persist:
                print(' ▪ Saving to /etc/nftables.conf for persistence', end=' ')
                self.nftablesController.save_to_nftables_conf()
                print('\r ' + Fore.GREEN + '✔' + Style.RESET_ALL)
        else:
            # In dry run mode, show the generated JSON
            print('\n' + Fore.CYAN + '--- Generated nftables JSON ruleset ---' + Style.RESET_ALL)
            print(ruleset_json)
            print(Fore.CYAN + '--- End of ruleset ---' + Style.RESET_ALL + '\n')


    #-----------------------------------------------------------------------------------------------
    #
    #   Protocol label used in the summary tables
    #   'any' means all protocols, or tcp and udp when ports are specified
    #
    #-----------------------------------------------------------------------------------------------
    def protocol_label(self, protocol: str, has_ports: bool) -> str:
        if protocol != 'any':
            return protocol

        return 'any (tcp, udp)' if has_ports else 'any (all protocols)'


    #-----------------------------------------------------------------------------------------------
    #
    #   Generate summary table
    #
    #-----------------------------------------------------------------------------------------------
    def generate_summary_table(self, content, quiet=False):
        table = []
        output_table = []
        forward_table = []
        nat_table = []

        # In the rules file, loop through every interface to apply their rules
        for interface in content:
            # First check that this interface exists on the system
            # Ignore this check if the interface is 'any'
            if interface != 'any' and not self.interface_exists(interface):
                if not quiet:
                    print('\n' + Fore.YELLOW + ' ▪ Interface ' + interface + ' does not exist on this system (rules will still be applied)' + Style.RESET_ALL)

            # Loop through ipv4 and ipv6 sections
            for ip_version in ["ipv4", "ipv6"]:
                if ip_version not in content[interface]:
                    continue

                # Ignore this interface if it has no rules
                if not content[interface][ip_version]:
                    continue

                # Interface label used in the tables
                if interface == 'any':
                    interface_label = Style.BRIGHT + Fore.GREEN + 'any (all interfaces)' + Style.RESET_ALL + ' (IPv' + ip_version[-1] + ')'
                else:
                    interface_label = Style.BRIGHT + 'Interface ' + Fore.GREEN + interface + Style.RESET_ALL + ' (IPv' + ip_version[-1] + ')'

                # Input and output rules of the interface
                for section, section_table, allow_header, drop_header in [
                    ('input', table, "Allow input packets from", "Drop input packets from"),
                    ('output', output_table, "Allow output packets to", "Drop output packets to"),
                ]:
                    if section not in content[interface][ip_version]:
                        continue

                    # Add interface to the table
                    section_table.append([interface_label, '', '', '', ''])

                    section_table.append([Style.BRIGHT + "Rule name", "Port(s)", "Protocol(s)", allow_header, drop_header + Style.RESET_ALL])

                    for rule_name, rule in content[interface][ip_version][section].items():
                        # Retrieve port, protocol, allow and drop values
                        protocol = rule['protocol']
                        ports = rule['ports']
                        allow = rule['allow']
                        drop = rule['drop']

                        # Format allow and drop for table display
                        allow_formatted = [Fore.GREEN + a + Style.RESET_ALL for a in allow]
                        drop_formatted = [Fore.YELLOW + d + Style.RESET_ALL for d in drop]

                        # Add rule to the table
                        section_table.append([
                            rule_name,
                            '' if protocol == 'icmp' else '\n'.join(map(str, ports)),
                            self.protocol_label(protocol, 'any' not in ports),
                            '\n'.join(allow_formatted),
                            '\n'.join(drop_formatted),
                        ])

                # Forward rules of the interface
                if 'forward' in content[interface][ip_version]:
                    # Add interface to the forward table
                    forward_table.append([interface_label, '', '', '', '', '', '', ''])

                    forward_table.append([
                        Style.BRIGHT + "Rule name", "Action", "From interface", "To interface",
                        "From source", "To destination", "Protocol", "Port(s) (src \u2192 dst)" + Style.RESET_ALL
                    ])

                    for rule_name in content[interface][ip_version]['forward']:
                        forward_rule = content[interface][ip_version]['forward'][rule_name]
                        action = forward_rule.get('action', 'accept')
                        rules = forward_rule.get('rules', [])

                        # Format action for table display
                        action_formatted = (Fore.GREEN if action == 'accept' else Fore.YELLOW) + action + Style.RESET_ALL
                        if forward_rule.get('log'):
                            action_formatted += ' (logged)'

                        # A forward group can contain several match rules
                        for rule in rules:
                            from_port = ', '.join(map(str, rule['from_port'])) if isinstance(rule.get('from_port'), list) else rule.get('from_port', '')
                            to_port = ', '.join(map(str, rule['to_port'])) if isinstance(rule.get('to_port'), list) else rule.get('to_port', '')
                            protocol = rule.get('protocol', 'any')

                            # Format the port(s) column as 'src -> dst' (only relevant for tcp/udp)
                            if from_port or to_port:
                                ports_display = str(from_port) if from_port else 'any'
                                ports_display += ' \u2192 '
                                ports_display += str(to_port) if to_port else 'any'
                            else:
                                ports_display = ''

                            forward_table.append([
                                rule_name,
                                action_formatted,
                                rule.get('from_interface', ''),
                                rule.get('to_interface', ''),
                                Fore.GREEN + str(rule.get('from_source', '')) + Style.RESET_ALL if rule.get('from_source') else '',
                                Fore.GREEN + str(rule.get('to_destination', '')) + Style.RESET_ALL if rule.get('to_destination') else '',
                                self.protocol_label(protocol, bool(from_port or to_port)),
                                ports_display,
                            ])

                # NAT rules of the interface
                if 'nat' in content[interface][ip_version]:
                    # Add interface to the NAT table
                    nat_table.append([interface_label, '', '', '', '', '', ''])

                    nat_table.append([
                        Style.BRIGHT + "Rule name", "Chain", "Interface", "Match address", "Protocol", "Port(s)", "Translate to" + Style.RESET_ALL
                    ])

                    for chain in ['prerouting', 'postrouting']:
                        for rule_name, rule in content[interface][ip_version]['nat'].get(chain, {}).items():
                            protocol = rule.get('protocol', 'any')

                            if chain == 'prerouting':
                                nat_interface = rule.get('in_interface', '')
                                address = 'to ' + rule['destination'] if rule.get('destination') else ''
                                ports = ', '.join(map(str, rule['to_port'])) if isinstance(rule.get('to_port'), list) else str(rule.get('to_port', ''))
                                translation = 'dnat to ' + rule['to_destination']
                            else:
                                nat_interface = rule.get('out_interface', '')
                                address = 'from ' + rule['source'] if rule.get('source') else ''
                                ports = ''
                                translation = 'masquerade' if rule.get('masquerade') else 'snat to ' + rule['to_source']

                            nat_table.append([
                                rule_name,
                                chain,
                                nat_interface,
                                Fore.GREEN + address + Style.RESET_ALL if address else '',
                                self.protocol_label(protocol, bool(ports)),
                                ports,
                                Fore.GREEN + translation + Style.RESET_ALL,
                            ])

        if not table and not output_table and not forward_table and not nat_table:
            raise Exception('No rules to apply')

        print('\n The following rules will be applied:')

        # Print the input rules table
        if table:
            print('\n Input rules:')
            print(tabulate(table, tablefmt="fancy_grid"), end='\n')

        # Print the output rules table
        if output_table:
            print('\n Output rules:')
            print(tabulate(output_table, tablefmt="fancy_grid"), end='\n')

        # Print the forward rules table
        if forward_table:
            print('\n Forward rules:')
            print(tabulate(forward_table, tablefmt="fancy_grid"), end='\n')

        # Print the NAT rules table
        if nat_table:
            print('\n NAT rules:')
            print(tabulate(nat_table, tablefmt="fancy_grid"), end='\n')
