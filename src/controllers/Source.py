# coding: utf-8

# Import libraries
from colorama import Fore, Style
from pathlib import Path
import yaml
import re
from tabulate import tabulate

class Source:
    def __init__(self):
        self.sources_dir = '/opt/ezfirewall/sources'

        # Create sources directory if it does not exist
        if not Path(self.sources_dir).exists():
            print('Creating sources directory: ', end = '')
            Path(self.sources_dir).mkdir(parents = True, exist_ok = True)
            print(Fore.GREEN + '✔' + Style.RESET_ALL)


    #-----------------------------------------------------------------------------------------------
    #
    #   Get source IP address
    #
    #-----------------------------------------------------------------------------------------------
    def getIp(self, source: str):
        # Initialize sources dictionary, it will contain all sources and their IP addresses
        # This will be used to check for duplicates
        sources_list = {}

        # If no source files are present, return
        if not list(Path(self.sources_dir).iterdir()):
            raise Exception('No source files were found')

        # Check source files
        for file in Path(self.sources_dir).iterdir():
            # If the file is empty, then ignore it
            if file.stat().st_size == 0:
                continue

            # Source files are YAML files, so check if it is readable and parseable
            try:
                with open(file, 'r') as f:
                    sources = yaml.safe_load(f)
            except Exception as e:
                raise Exception('Source file ' + str(file) + ' is not a valid YAML file: ' + str(e))

            # Loop through every source group to find the source
            for group in sources:
                # If nothing is declared in the group, then ignore it
                if not sources[group]:
                    continue

                for s in sources[group]:
                    # If the source is already in the sources dictionary, then raise an exception because it is a duplicate
                    if s in sources_list:
                        raise Exception('Found duplicate source "' + s + '" in source file ' + str(file))
                    
                    # Retrieve IP address
                    ip = sources[group][s]
                    
                    # Check that IP is not empty
                    if not ip:
                        raise Exception('IP address of source "' + s + '" is empty')
                    
                    # Check that IP is a valid IP address
                    # If can either be xxx.xxx.xxx.xxx or xxx.xxx.xxx.xxx/xx
                    if not re.match(r'^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}(\/\d{1,2})?$', ip):
                        raise Exception('IP address "' + ip + '" of source "' + s + '" is not a valid IP address')

                    # Add the source to the sources dictionary
                    sources_list[s] = sources[group][s]

        # If the source was found, return the IP address
        if source in sources_list:
            return sources_list[source]
        
        # If no IP was returned, then it means that the source was not found in any source file
        raise Exception('Source named ' + source + ' was not found in any source file')


    #-----------------------------------------------------------------------------------------------
    #
    #   List all sources and their IP addresses
    #
    #-----------------------------------------------------------------------------------------------
    def list(self, search: str = None):
        table = []

        # If no source files are present, return
        if not list(Path(self.sources_dir).iterdir()):
            raise Exception('No source files were found')

        # Check source files
        for file in Path(self.sources_dir).iterdir():
            # Source files are YAML files, so check if it is readable and parseable
            try:
                with open(file, 'r') as f:
                    content = yaml.safe_load(f)
            except Exception as e:
                raise Exception('Source file ' + str(file) + ' is not a valid YAML file: ' + str(e))

            for group in content:
                if not content:
                    continue

                # If a search term is provided, then only display the group that contains the search term
                if search and search not in group:
                    continue

                # Append group name to table
                table.append([Fore.GREEN + group + Style.RESET_ALL, ''])

                # Append sources to table
                for source in content[group]:
                    table.append([source, content[group][source]])


        print(tabulate(table, tablefmt = 'fancy_grid'))
