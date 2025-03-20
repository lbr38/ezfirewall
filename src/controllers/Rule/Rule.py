# coding: utf-8

# Import libraries
from colorama import Fore, Style
from pathlib import Path
import subprocess
import yaml
import glob
import re
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
    def apply(self, config: dict, dry_run = False, quiet = False):
        # First of all, check that the rules files are valid YAML files
        print(' ▪ Checking rules files ', end = '')

        # Get all rules files
        rules_files = glob.glob(self.rules_dir + '/*.yml')
        
        # If there are no rules files, raise an exception
        if not rules_files:
            raise Exception('There is no rule to apply (no rule files were found)')

        # Check that every rule files are not empty and are valid YAML files
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

        # Loop through every rule files
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

            # Merge data
            content = self.mergeController.merge_interfaces(content, data)

        if not content:
            raise Exception('No rules to apply')

        # Generate the summary table
        self.generate_summary_table(content)

        # Ask for confirmation before applying rules
        if not dry_run:
            if not quiet:
                print(' ▪ Apply rules? [y/N] ', end = '')
                answer = input().lower()

                if answer != 'y':
                    exit(0)

        #
        # Build rules
        #
        print(' ▪ Building rules', end = ' ')

        # In the rules file, loop through every interface to apply their rules
        for interface in content:
            # Get the ip version
            ip_version = content[interface]['ip_version']

            # Ignore this interface if it has no 'input' or 'output' rules
            if 'input' not in content[interface] and 'output' not in content[interface]:
                continue

            # Apply input then output rules of the interface
            for input_output in ['input', 'output']:
                # If 'input' or 'output' rules are present in the interface
                if input_output in content[interface]:
                    # Apply drop rules first, then allow rules
                    for allow_drop in ['drop', 'allow']:
                        for rule_name in content[interface][input_output]:
                            if allow_drop not in content[interface][input_output][rule_name]:
                                continue

                            # Check if protocol key is present
                            # if 'protocol' not in content[interface][input_output][rule_name]:
                            #     raise Exception("'protocol' key is missing in input rule " + rule_name + ' of interface ' + interface)
                            # # Unless the protocol is 'icmp', the 'ports' key is required
                            # if content[interface][input_output][rule_name]['protocol'] != 'icmp':
                            #     if 'ports' not in content[interface][input_output][rule_name]:
                            #         raise Exception("'ports' key is missing in input rule " + rule_name + ' of interface ' + interface)

                            # Retrieve port, protocol, allow and drop values
                            protocol = content[interface][input_output][rule_name]['protocol']
                            ports = content[interface][input_output][rule_name]['ports'] if 'ports' in content[interface][input_output][rule_name] else []
                            sources = content[interface][input_output][rule_name][allow_drop]

                            # Generate rules
                            if input_output == 'input':
                                if allow_drop == 'allow':
                                    self.nftablesInputController.generate_allow_rules(ip_version, interface, sources, protocol, ports)

                                if allow_drop == 'drop':
                                    self.nftablesInputController.generate_drop_rules(ip_version, interface, sources, protocol, ports)

        #
        # Write all rules and config to file
        #
        self.nftablesInputController.write(config)
        print('\r ' + Fore.GREEN + '✔' + Style.RESET_ALL)

        #
        # Check if the rules are valid
        #
        print(' ▪ Checking rules', end = ' ')
        self.nftablesController.check()
        print('\r ' + Fore.GREEN + '✔' + Style.RESET_ALL)

        #
        # Apply rules (if not dry run)
        #
        if not dry_run:
            print(' ▪ Applying rules', end = ' ')
            self.nftablesController.apply()
            print('\r ' + Fore.GREEN + '✔' + Style.RESET_ALL)


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
                    capture_output = True,
                    text = True,
                    shell = True
                )

                # If interface does not exist, raise an exception
                if result.returncode != 0:
                    raise Exception('Interface ' + interface + ' does not exist on this system')
            
            # Print an error if the ip version is not defined
            if 'ip_version' not in content[interface]:
                raise Exception('ip_version (v4 or v6) is not defined for interface ' + interface)
            
            # Check that the ip_version is valid
            if content[interface]['ip_version'] not in [4, 6]:
                raise Exception('ip_version must be either 4 or 6')
            
            # Get the ip version
            ip_version = content[interface]['ip_version']

            # Ignore this interface if it has no 'input' or 'output' rules
            if 'input' not in content[interface] and 'output' not in content[interface]:
                continue

            # Add interface to the table
            if interface == 'any':
                table.append([Fore.GREEN + 'any (all interfaces)' + Style.RESET_ALL + ' (ipv' + str(ip_version) + ')', '', '', '', ''])
            else:
                table.append(['Interface ' + Fore.GREEN + interface + Style.RESET_ALL + ' (ipv' + str(ip_version) + ')', '', '', '', ''])

            # Apply input rules of the interface
            if 'input' in content[interface]:
                table.append(["Rule name", "Port(s)", "Protocol(s)", "Allow input packets from", "Drop input packets from"])

                for rule_name in content[interface]['input']:
                    allow = []
                    drop = []
                    allow_formatted = []
                    drop_formatted = []

                    # Check if protocol key is present
                    if 'protocol' not in content[interface]['input'][rule_name]:
                        raise Exception("'protocol' key is missing in input rule " + rule_name + ' of interface ' + interface)
                    # Unless the protocol is 'icmp', the 'ports' key is required
                    if content[interface]['input'][rule_name]['protocol'] != 'icmp':
                        if 'ports' not in content[interface]['input'][rule_name]:
                            raise Exception("'ports' key is missing in input rule " + rule_name + ' of interface ' + interface)
                    if 'allow' not in content[interface]['input'][rule_name] and 'drop' not in content[interface]['input'][rule_name]:
                        raise Exception("Neither 'allow' nor 'drop' key is present in input rule " + rule_name + ' of interface ' + interface)

                    # Retrieve port, protocol, allow and drop values
                    protocol = content[interface]['input'][rule_name]['protocol']
                    ports = content[interface]['input'][rule_name]['ports'] if 'ports' in content[interface]['input'][rule_name] else []
                    if 'allow' in content[interface]['input'][rule_name]:
                        allow = content[interface]['input'][rule_name]['allow']
                    if 'drop' in content[interface]['input'][rule_name]:
                        drop = content[interface]['input'][rule_name]['drop']

                    # Do some formatting for table display
                    for a in allow:
                        # Retrieve the IP addresses from the sources files
                        # ip = self.sourceController.getIp(a)
                        # If source is not an IP address, get the IP address from the sources files
                        if not re.match(r'^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}(\/\d{1,2})?$', a):
                            ip = self.sourceController.getIp(a)
                        else:
                            ip = a

                        # Format allow with colors
                        if (a == ip):
                            allow_formatted.append(Fore.GREEN + a + Style.RESET_ALL)
                        else:
                            allow_formatted.append(Fore.GREEN + a + Style.RESET_ALL + Style.DIM + ' (' + ip + ')' + Style.RESET_ALL)
                    for d in drop:
                        # Retrieve the IP addresses from the sources files
                        # ip = self.sourceController.getIp(d)
                        # If source is not an IP address, get the IP address from the sources files
                        if not re.match(r'^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}(\/\d{1,2})?$', d):
                            ip = self.sourceController.getIp(d)
                        else:
                            ip = d

                        # Format drop with colors
                        if (d == ip):
                            drop_formatted.append(Fore.YELLOW + d + Style.RESET_ALL)
                        else:
                            drop_formatted.append(Fore.YELLOW + d + Style.RESET_ALL + Style.DIM + ' (' + ip + ')' + Style.RESET_ALL)

                    # Add rule to the table
                    table.append([
                        rule_name,
                        '' if 'icmp' in ports else '\n'.join(map(str, ports)),
                        'any (tcp, udp)' if protocol == 'any' else protocol,
                        '\n'.join(allow_formatted),
                        '\n'.join(drop_formatted),
                    ])

        print(tabulate(table, tablefmt="fancy_grid"), end='\n')  
