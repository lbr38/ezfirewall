# coding: utf-8

# Import libraries
from pathlib import Path
import re
from colorama import Fore, Style
import yaml
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

            for s in sources:
                # If the source is already in the sources dictionary, then raise an exception because it is a duplicate
                if s in sources_list:
                    raise Exception('Found duplicate source "' + s + '" in source file ' + str(file))

                # Retrieve IP address
                ip = sources[s]

                # Check that IP is not empty
                if not ip:
                    raise Exception('IP address of source "' + s + '" is empty')

                # Check that IP is a valid IP address (v4 or v6)
                if not re.match(r'^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}(\/\d{1,2})?$|^([0-9a-fA-F]{1,4}:){7}[0-9a-fA-F]{1,4}(\/\d{1,3})?$', ip):
                    raise Exception('IP address "' + ip + '" of source "' + s + '" is not a valid IP address')

                # Add the source to the sources dictionary
                sources_list[s] = ip

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

        print(' ▪ Listing sources')

        # If no source files are present, return
        if not list(Path(self.sources_dir).iterdir()):
            raise Exception('No source files were found')

        # Check source files
        for file in Path(self.sources_dir).iterdir():
            # Source files are YAML files, so check if it is readable and parseable
            try:
                with open(file, 'r') as f:
                    sources = yaml.safe_load(f)
            except Exception as e:
                raise Exception('Source file ' + str(file) + ' is not a valid YAML file: ' + str(e))

            if not sources:
                continue

            for source in sources:
                # If a search term is provided, then only display the group that contains the search term
                if search and search not in source:
                    continue

                # Append source name to table
                table.append([source, sources[source]])

        print(tabulate(table, tablefmt = 'fancy_grid'), end='\n')
