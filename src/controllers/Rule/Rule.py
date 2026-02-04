# coding: utf-8

# Import libraries
import re
import sys
import glob
import subprocess
from pathlib import Path
import yaml
from colorama import Fore, Style
from tabulate import tabulate

# Import classes
from src.controllers.Rule.Merge import Merge
from src.controllers.Nftables.Nftables import Nftables
from src.controllers.Nftables.Input import Input
from src.controllers.Source import Source

class Rule:
    def __init__(self):
        self.rules_dir = '/opt/ezfirewall/rules'
        self.mergeController = Merge()
        self.nftablesController = Nftables()
        self.nftablesInputController = Input()
        self.sourceController = Source()

        # Create rules directory if it does not exist
        if not Path(self.rules_dir).exists():
            print('Creating ' + self.rules_dir + ' directory: ', end = '')
            Path(self.rules_dir).mkdir(parents = True, exist_ok = True)
            print(Fore.GREEN + '✔' + Style.RESET_ALL)


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

        # Generate the summary table
        self.generate_summary_table(content)

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
                                    # Collect IPs for drop set
                                    self.nftablesInputController.generate_drop_rules(ip_version, interface, sources, protocol, ports)
                                    
                                    # Store rule data for later drop rule creation
                                    rules_data.append({
                                        'ip_version': ip_version,
                                        'interface': interface,
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
            if interface != 'any':
                result = subprocess.run(
                    ["/usr/sbin/route -n | awk '{print $NF}' | grep -q '" + interface + "'"],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    universal_newlines=True,
                    shell=True
                )

                if result.returncode != 0:
                    if not quiet:
                        print('\n' + Fore.YELLOW + ' ▪ Interface ' + interface + ' does not exist on this system' + Style.RESET_ALL)
                    continue

            for ip_version in ["ipv4", "ipv6"]:
                if ip_version not in content[interface]:
                    continue

                # Ignore this interface if it has no 'input' or 'output' rules
                if 'input' not in content[interface][ip_version] and 'output' not in content[interface][ip_version]:
                    continue

                # Process input rules
                for input_output in ['input', 'output']:
                    # If 'input' or 'output' rules are present in the interface
                    if input_output in content[interface][ip_version]:
                        # Process allow rules only (drops already handled above)
                        for rule_name in content[interface][ip_version][input_output]:
                            if 'allow' in content[interface][ip_version][input_output][rule_name]:
                                # Retrieve port, protocol, allow values
                                protocol = content[interface][ip_version][input_output][rule_name]['protocol']
                                ports = content[interface][ip_version][input_output][rule_name]['ports'] if 'ports' in content[interface][ip_version][input_output][rule_name] else []
                                sources = content[interface][ip_version][input_output][rule_name]['allow']
                                
                                if input_output == 'input':
                                    # Create individual allow rules (after drops for proper priority)
                                    self.nftablesInputController.generate_allow_rules(ip_version, interface, sources, protocol, ports)

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
    def generate_summary_table(self, content):
        table = []

        # In the rules file, loop through every interface to apply their rules
        for interface in content:
            # First check that this interface exists on the system
            # Ignore this check if the interface is 'any'
            if interface != 'any':
                result = subprocess.run(
                    ["/usr/sbin/route -n | awk '{print $NF}' | grep -q '" + interface + "'"],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    universal_newlines=True,
                    shell=True
                )

                # If interface does not exist, raise an exception
                if result.returncode != 0:
                    raise Exception('Interface ' + interface + ' does not exist on this system')

            # Loop through ipv4 and ipv6 sections
            for ip_version in ["ipv4", "ipv6"]:
                if ip_version not in content[interface]:
                    continue

                # Ignore this interface if it has no 'input' or 'output' rules
                if 'input' not in content[interface][ip_version] and 'output' not in content[interface][ip_version]:
                    continue

                # Add interface to the table
                if interface == 'any':
                    table.append([Style.BRIGHT + Fore.GREEN + 'any (all interfaces)' + Style.RESET_ALL + ' (IPv' + ip_version[-1] + ')', '', '', '', ''])
                else:
                    table.append([Style.BRIGHT + 'Interface ' + Fore.GREEN + interface + Style.RESET_ALL + ' (IPv' + ip_version[-1] + ')', '', '', '', ''])

                # Apply input rules of the interface
                if 'input' in content[interface][ip_version]:
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

        if not table:
            raise Exception('No rules to apply')

        print('\n The following rules will be applied:')
        print(tabulate(table, tablefmt="fancy_grid"), end='\n')
