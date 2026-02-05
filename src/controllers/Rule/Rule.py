# coding: utf-8

# Import libraries
import re
import sys
import glob
import socket
from pathlib import Path
import yaml
from colorama import Fore, Style
from tabulate import tabulate

# Import classes
from src.controllers.Rule.Merge import Merge
from src.controllers.Nftables.Nftables import Nftables
from src.controllers.Nftables.Input import Input
from src.controllers.Nftables.Forward import Forward
from src.controllers.Nftables.Nat import Nat
from src.controllers.Source import Source

class Rule:
    def __init__(self):
        self.rules_dir = '/opt/ezfirewall/rules'
        # Tracks whether the live nftables ruleset has actually been modified.
        # Used to decide whether a backup restore is needed on failure.
        self.applied = False
        self.mergeController = Merge()
        self.nftablesController = Nftables()
        self.nftablesInputController = Input()
        # Share the same JsonBuilder instance so all rules end up in the same ruleset
        self.nftablesForwardController = Forward(self.nftablesInputController.jsonBuilder)
        self.nftablesNatController = Nat(self.nftablesInputController.jsonBuilder)
        self.sourceController = Source()

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
    #   Validate rules schema
    #
    #-----------------------------------------------------------------------------------------------
    def validate_rules_schema(self, content):
        """Validate the structure of all rules and provide clear error messages for missing fields."""
        
        for interface, iface_data in content.items():
            for ip_version, ip_data in iface_data.items():
                if not isinstance(ip_data, dict):
                    raise Exception(f'{interface}/{ip_version}: must be a mapping (dict)')

                # Validate input/output rules
                for section in ['input', 'output']:
                    if section in ip_data:
                        if not isinstance(ip_data[section], dict):
                            raise Exception(f'{interface}/{ip_version}/{section}: must be a mapping')
                        
                        for rule_name, rule_data in ip_data[section].items():
                            if not isinstance(rule_data, dict):
                                raise Exception(f'{interface}/{ip_version}/{section}/{rule_name}: rule must be a mapping')
                            
                            # Check for required field 'protocol'
                            if 'protocol' not in rule_data:
                                raise Exception(f'{interface}/{ip_version}/{section}/{rule_name}: missing required field "protocol"')
                            
                            # Check that at least 'allow' or 'drop' is present
                            has_allow = 'allow' in rule_data and rule_data['allow']
                            has_drop = 'drop' in rule_data and rule_data['drop']
                            if not (has_allow or has_drop):
                                raise Exception(f'{interface}/{ip_version}/{section}/{rule_name}: must have at least one of "allow" or "drop" (non-empty)')

                # Validate forward rules
                if 'forward' in ip_data:
                    if not isinstance(ip_data['forward'], dict):
                        raise Exception(f'{interface}/{ip_version}/forward: must be a mapping')
                    
                    for rule_name, rule_config in ip_data['forward'].items():
                        if not isinstance(rule_config, dict):
                            raise Exception(f'{interface}/{ip_version}/forward/{rule_name}: rule must be a mapping')
                        
                        # Check for required field 'rules'
                        if 'rules' not in rule_config:
                            raise Exception(f'{interface}/{ip_version}/forward/{rule_name}: missing required field "rules"')
                        
                        rules = rule_config['rules']
                        if not isinstance(rules, list) or len(rules) == 0:
                            raise Exception(f'{interface}/{ip_version}/forward/{rule_name}: "rules" must be a non-empty list')
                        
                        # Validate each rule in the list
                        for i, rule in enumerate(rules):
                            if not isinstance(rule, dict):
                                raise Exception(f'{interface}/{ip_version}/forward/{rule_name}/rules[{i}]: each rule must be a mapping')
                            
                            # Each rule must have at least one of from_interface or to_interface
                            has_from = 'from_interface' in rule
                            has_to = 'to_interface' in rule
                            if not (has_from or has_to):
                                raise Exception(f'{interface}/{ip_version}/forward/{rule_name}/rules[{i}]: must have at least one of "from_interface" or "to_interface"')

                # Validate NAT rules
                if 'nat' in ip_data:
                    if not isinstance(ip_data['nat'], dict):
                        raise Exception(f'{interface}/{ip_version}/nat: must be a mapping')
                    
                    for chain, chain_rules in ip_data['nat'].items():
                        if chain not in ['prerouting', 'postrouting']:
                            raise Exception(f'{interface}/{ip_version}/nat/{chain}: unknown NAT chain (must be "prerouting" or "postrouting")')
                        
                        if not isinstance(chain_rules, dict):
                            raise Exception(f'{interface}/{ip_version}/nat/{chain}: must be a mapping')
                        
                        for rule_name, rule_config in chain_rules.items():
                            if not isinstance(rule_config, dict):
                                raise Exception(f'{interface}/{ip_version}/nat/{chain}/{rule_name}: rule must be a mapping')


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
    #   Apply rules
    #
    #-----------------------------------------------------------------------------------------------
    def apply(self, config: dict, dry_run=False, quiet=False, no_persist=False):
        # First of all, check that the rules files are valid YAML files
        print(' ▪ Checking rules files ', end='')

        # Get all rules files
        rules_files = glob.glob(self.rules_dir + '/*.yml')

        # If there are no rules files, raise an exception
        if not rules_files:
            raise Exception('There is no rule to apply (no rule files were found)')

        # Check that every rule file is not empty and is a valid YAML file
        for file in rules_files:
            # Check that the file is not empty
            if Path(file).stat().st_size == 0:
                raise Exception('Rule file ' + file + ' is empty')

            try:
                with open(file, 'r') as f:
                    yaml.safe_load(f)
            except Exception as e:
                raise Exception('Rule file ' + file + ' is not a valid YAML file: ' + str(e))

        print('\r ' + Fore.GREEN + '✔' + Style.RESET_ALL)

        #
        # Print the rules
        #

        # Loop through every rule file
        content = {}
        for file in sorted(rules_files):
            try:
                with open(file, 'r') as f:
                    data = yaml.safe_load(f)
            except Exception as e:
                raise Exception('Error while loading rule file ' + file + ': ' + str(e))

            # Ignore file if it is empty
            if not data:
                continue

            # Merge data using the Merge class
            content = self.mergeController.merge_interfaces(content, data)

        if not content:
            raise Exception('No rules to apply')

        # Validate the rules schema to provide clear error messages for missing fields
        self.validate_rules_schema(content)

        # Generate the summary table
        self.generate_summary_table(content, quiet)

        # Ask for confirmation before applying rules
        if not dry_run:
            if not quiet:
                print(' ▪ Apply rules? [y/N] ', end='')
                answer = input().lower()

                if answer != 'y':
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

        # In the rules file, loop through every interface to apply their rules
        for interface in content:
            # Loop through ipv4 and ipv6 sections
            for ip_version in ["ipv4", "ipv6"]:
                if ip_version not in content[interface]:
                    continue

                # Ignore this interface if it has no 'input' or 'output' rules
                if 'input' not in content[interface][ip_version] and 'output' not in content[interface][ip_version]:
                    continue

                # Apply input then output rules of the interface
                for input_output in ['input', 'output']:
                    # If 'input' or 'output' rules are present in the interface
                    if input_output in content[interface][ip_version]:
                        # Collect all rule data first
                        for rule_name in content[interface][ip_version][input_output]:
                            # Retrieve port, protocol, allow and drop values
                            protocol = content[interface][ip_version][input_output][rule_name]['protocol']
                            ports = content[interface][ip_version][input_output][rule_name]['ports'] if 'ports' in content[interface][ip_version][input_output][rule_name] else []

                            # Note: Allow rules will be processed later to ensure proper order (DROP before ALLOW)

                            # Collect drop rules - collect IPs for sets
                            if 'drop' in content[interface][ip_version][input_output][rule_name]:
                                sources = content[interface][ip_version][input_output][rule_name]['drop']
                                
                                if input_output == 'input':
                                    # Collect IPs for drop set (per service)
                                    self.nftablesInputController.generate_drop_rules(ip_version, interface, rule_name, sources, protocol, ports)
                                    
                                    # Store rule data for later drop rule creation
                                    rules_data.append({
                                        'ip_version': ip_version,
                                        'interface': interface,
                                        'rule_name': rule_name,
                                        'protocol': protocol,
                                        'ports': ports,
                                        'type': 'drop'
                                    })

        # Now finalize drop sets first (priority blacklist)
        self.nftablesInputController.finalize_sets_and_rules()
        self.nftablesInputController.create_set_based_rules(rules_data)

        # Then process allow rules individually (after drops for proper priority)
        for interface in content:
            # Check that this interface exists on the system
            # Ignore this check if the interface is 'any'
            if interface != 'any' and not self.interface_exists(interface):
                if not quiet:
                    print('\n' + Fore.YELLOW + ' ▪ Interface ' + interface + ' does not exist on this system (rules will still be applied)' + Style.RESET_ALL)

            for ip_version in ["ipv4", "ipv6"]:
                if ip_version not in content[interface]:
                    continue

                # Process input/output allow rules
                for input_output in ['input', 'output']:
                    if input_output in content[interface][ip_version]:
                        for rule_name in content[interface][ip_version][input_output]:
                            if 'allow' in content[interface][ip_version][input_output][rule_name]:
                                protocol = content[interface][ip_version][input_output][rule_name]['protocol']
                                ports = content[interface][ip_version][input_output][rule_name]['ports'] if 'ports' in content[interface][ip_version][input_output][rule_name] else []
                                sources = content[interface][ip_version][input_output][rule_name]['allow']
                                
                                if input_output == 'input':
                                    self.nftablesInputController.generate_allow_rules(ip_version, interface, sources, protocol, ports)

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
            self.nftablesController.apply(ruleset_json)            # The live ruleset has now been modified
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
    #   Generate summary table
    #
    #-----------------------------------------------------------------------------------------------
    def generate_summary_table(self, content, quiet=False):
        table = []
        forward_table = []

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

                # Ignore this interface if it has no 'input', 'output' or 'forward' rules
                if ('input' not in content[interface][ip_version]
                        and 'output' not in content[interface][ip_version]
                        and 'forward' not in content[interface][ip_version]):
                    continue

                # Interface label used in the tables
                if interface == 'any':
                    interface_label = Style.BRIGHT + Fore.GREEN + 'any (all interfaces)' + Style.RESET_ALL + ' (IPv' + ip_version[-1] + ')'
                else:
                    interface_label = Style.BRIGHT + 'Interface ' + Fore.GREEN + interface + Style.RESET_ALL + ' (IPv' + ip_version[-1] + ')'

                # Apply input rules of the interface
                if 'input' in content[interface][ip_version]:
                    # Add interface to the input table
                    table.append([interface_label, '', '', '', ''])

                    table.append([Style.BRIGHT + "Rule name", "Port(s)", "Protocol(s)", "Allow input packets from", "Drop input packets from" + Style.RESET_ALL])

                    for rule_name in content[interface][ip_version]['input']:
                        allow = []
                        drop = []
                        allow_formatted = []
                        drop_formatted = []

                        # Retrieve port, protocol, allow and drop values
                        protocol = content[interface][ip_version]['input'][rule_name]['protocol']
                        ports = content[interface][ip_version]['input'][rule_name]['ports'] if 'ports' in content[interface][ip_version]['input'][rule_name] else []
                        if 'allow' in content[interface][ip_version]['input'][rule_name] and content[interface][ip_version]['input'][rule_name]['allow']:
                            allow = content[interface][ip_version]['input'][rule_name]['allow']
                        if 'drop' in content[interface][ip_version]['input'][rule_name] and content[interface][ip_version]['input'][rule_name]['drop']:
                            drop = content[interface][ip_version]['input'][rule_name]['drop']

                        # Format allow and drop for table display
                        allow_formatted = [Fore.GREEN + a + Style.RESET_ALL for a in allow]
                        drop_formatted = [Fore.YELLOW + d + Style.RESET_ALL for d in drop]

                        # Add rule to the table
                        table.append([
                            rule_name,
                            '' if 'icmp' in ports else '\n'.join(map(str, ports)),
                            'any (tcp, udp)' if protocol == 'any' else protocol,
                            '\n'.join(allow_formatted),
                            '\n'.join(drop_formatted),
                        ])

                # Apply forward rules of the interface
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

                        # A forward group can contain several match rules
                        for rule in rules:
                            from_port = rule.get('from_port', '')
                            to_port = rule.get('to_port', '')
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
                                'any (tcp, udp)' if protocol == 'any' else protocol,
                                ports_display,
                            ])

        if not table and not forward_table:
            raise Exception('No rules to apply')

        print('\n The following rules will be applied:')

        # Print the input/output rules table
        if table:
            print(tabulate(table, tablefmt="fancy_grid"), end='\n')

        # Print the forward rules table
        if forward_table:
            print('\n Forward rules:')
            print(tabulate(forward_table, tablefmt="fancy_grid"), end='\n')
