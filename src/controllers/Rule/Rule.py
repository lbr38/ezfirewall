# coding: utf-8

# Import libraries
from colorama import Fore, Style
from pathlib import Path
import subprocess
import yaml
import glob
from tabulate import tabulate

# Import classes
from src.controllers.Rule.Merge import Merge
from src.controllers.Iptables.Iptables import Iptables
from src.controllers.Iptables.Input import Input
from src.controllers.Source import Source

class Rule:
    def __init__(self):
        self.rules_dir = '/opt/ezfirewall/rules'
        self.mergeController = Merge()
        self.iptablesController = Iptables()
        self.iptablesInputController = Input()
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
        # Apply the rules
        #

        # First, initialize (reset) iptables
        # Only if it is not a dry run
        if not dry_run:
            self.iptablesController.initialize(config)

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
        # Apply rules
        #

        # In the rules file, loop through every interface to apply their rules
        for interface in content:
            # Print an error if the ip version is not defined
            if 'ip_version' not in content[interface]:
                raise Exception('ip_version (v4 or v6) is not defined for interface ' + interface)
            
            # Check that the ip_version is valid
            if content[interface]['ip_version'] not in ['v4', 'v6']:
                raise Exception('ip_version must be either v4 or v6')
            
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

                            # Check if every required key is present
                            if 'port' not in content[interface][input_output][rule_name]:
                                raise Exception("'port' key is missing in input rule " + rule_name + ' of interface ' + interface)
                            if 'protocols' not in content[interface][input_output][rule_name]:
                                raise Exception("'protocols' key is missing in input rule " + rule_name + ' of interface ' + interface)

                            # Retrieve port, protocols, allow and drop values
                            ports = content[interface][input_output][rule_name]['port']
                            protocols = content[interface][input_output][rule_name]['protocols']
                            sources = content[interface][input_output][rule_name][allow_drop]

                            # Apply rule only if it is not a dry run
                            if not dry_run:
                                if input_output == 'input':
                                    if allow_drop == 'allow':
                                        self.iptablesInputController.allow(ip_version, interface, sources, protocols, ports)

                                    if allow_drop == 'drop':
                                        self.iptablesInputController.drop(ip_version, interface, sources, protocols, ports)


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
            # Ignore this check if the interface is 'all'
            if interface != 'all':
                result = subprocess.run(
                    ["/usr/sbin/route -n | awk '{print $NF}' | grep -q '" + interface + "'"],
                    capture_output = True,
                    text = True,
                    shell = True
                )

                # If interface does not exist, raise an exception
                if result.returncode != 0:
                    raise Exception('Interface ' + interface + ' does not exist on this system')

            # Ignore this interface if it has no 'input' or 'output' rules
            if 'input' not in content[interface] and 'output' not in content[interface]:
                continue

            # Add interface to the table
            if interface == 'all':
                table.append([Fore.GREEN + 'any (all interfaces)' + Style.RESET_ALL, '', '', '', ''])
            else:
                table.append(['Interface ' + Fore.GREEN + interface + Style.RESET_ALL, '', '', '', ''])

            # Apply input rules of the interface
            if 'input' in content[interface]:
                table.append(["Rule name", "Port(s)", "Protocol(s)", "Allow input packets from", "Drop input packets from"])

                for rule_name in content[interface]['input']:
                    allow = []
                    drop = []
                    allow_formatted = []
                    drop_formatted = []

                    # Check if every required key is present
                    if 'port' not in content[interface]['input'][rule_name]:
                        raise Exception("'port' key is missing in input rule " + rule_name + ' of interface ' + interface)
                    if 'protocols' not in content[interface]['input'][rule_name]:
                        raise Exception("'protocols' key is missing in input rule " + rule_name + ' of interface ' + interface)
                    if 'allow' not in content[interface]['input'][rule_name] and 'drop' not in content[interface]['input'][rule_name]:
                        raise Exception("Neither 'allow' nor 'drop' key is present in input rule " + rule_name + ' of interface ' + interface)

                    # Retrieve port, protocols, allow and drop values
                    ports = content[interface]['input'][rule_name]['port']
                    protocols = content[interface]['input'][rule_name]['protocols']
                    if 'allow' in content[interface]['input'][rule_name]:
                        allow = content[interface]['input'][rule_name]['allow']
                    if 'drop' in content[interface]['input'][rule_name]:
                        drop = content[interface]['input'][rule_name]['drop']

                    # Do some formatting for table display
                    for a in allow:
                        # Retrieve the IP addresses from the sources files
                        ip = self.sourceController.getIp(a)
                        # Format allow with colors
                        allow_formatted.append(Fore.GREEN + a + Style.RESET_ALL + Style.DIM + ' (' + ip + ')' + Style.RESET_ALL)
                    for d in drop:
                        # Retrieve the IP addresses from the sources files
                        ip = self.sourceController.getIp(d)
                        # Format drop with colors
                        drop_formatted.append(Fore.YELLOW + d + Style.RESET_ALL + Style.DIM + ' (' + ip + ')' + Style.RESET_ALL)

                    # Add rule to the table
                    table.append([
                        rule_name,
                        '\n' + str(ports),
                        '\n'.join(protocols),
                        '\n'.join(allow_formatted),
                        '\n'.join(drop_formatted),
                    ])

        print(tabulate(table, tablefmt="fancy_grid"), end='\n')  
