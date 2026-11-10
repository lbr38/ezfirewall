# coding: utf-8

# Import libraries
from pathlib import Path
import ipaddress
from colorama import Fore, Style
from tabulate import tabulate
from typing import Optional

# Import classes
from src.controllers.Yaml import Yaml

class Source:
    def __init__(self):
        self.sources_dir = '/opt/ezfirewall/sources'
        self.yamlController = Yaml()

        # Sources loaded from the source files (loaded once, on first use)
        self.sources = None

        # Create sources directory if it does not exist
        if not Path(self.sources_dir).exists():
            print('Creating sources directory: ', end = '')
            Path(self.sources_dir).mkdir(parents = True, exist_ok = True)
            print(Fore.GREEN + '✔' + Style.RESET_ALL)


    #-----------------------------------------------------------------------------------------------
    #
    #   Check that a string is a valid IPv4/IPv6 address or CIDR range
    #
    #-----------------------------------------------------------------------------------------------
    def is_valid_ip(self, ip: str) -> bool:
        """Return True if ip is a valid IPv4/IPv6 address or CIDR network (compressed forms included)"""
        try:
            if '/' in ip:
                ipaddress.ip_network(ip, strict=False)
            else:
                ipaddress.ip_address(ip)
            return True
        except ValueError:
            return False


    #-----------------------------------------------------------------------------------------------
    #
    #   Get source files (hidden files, like editor swap files, and directories are ignored)
    #
    #-----------------------------------------------------------------------------------------------
    def get_files(self):
        return sorted(file for file in Path(self.sources_dir).iterdir() if file.is_file() and not file.name.startswith('.'))


    #-----------------------------------------------------------------------------------------------
    #
    #   Load a source file
    #
    #-----------------------------------------------------------------------------------------------
    def load_file(self, file: Path) -> dict:
        # Source files are YAML files, so check if it is readable and parseable
        try:
            sources = self.yamlController.load(file)
        except Exception as e:
            raise Exception('source file ' + str(file) + ' is not a valid YAML file: ' + str(e))

        # The file is empty (or only contains comments)
        if sources is None:
            return {}

        if not isinstance(sources, dict):
            raise Exception('source file ' + str(file) + ' must contain a list of "name: IP address" entries')

        return sources


    #-----------------------------------------------------------------------------------------------
    #
    #   Load and check all sources from the source files
    #
    #-----------------------------------------------------------------------------------------------
    def load(self) -> dict:
        # Sources are only loaded once
        if self.sources is not None:
            return self.sources

        # Sources dictionary, it will contain all sources and their IP addresses
        # This will be used to check for duplicates
        sources_list = {}

        for file in self.get_files():
            sources = self.load_file(file)

            for s in sources:
                # If the source is already in the sources dictionary, then raise an exception because it is a duplicate
                if str(s) in sources_list:
                    raise Exception('found duplicate source "' + str(s) + '" in source file ' + str(file))

                # Retrieve IP address
                ip = sources[s]

                # Check that IP is not empty
                if not ip:
                    raise Exception('IP address of source "' + str(s) + '" is empty')

                # Check that IP is a valid IP address (v4 or v6)
                if not isinstance(ip, str) or not self.is_valid_ip(ip):
                    raise Exception('IP address "' + str(ip) + '" of source "' + str(s) + '" is not a valid IP address')

                # Add the source to the sources dictionary
                sources_list[str(s)] = ip

        self.sources = sources_list

        return self.sources


    #-----------------------------------------------------------------------------------------------
    #
    #   Get source IP address
    #   If ip_version is specified ('ipv4' or 'ipv6'), check that the IP address matches it
    #
    #-----------------------------------------------------------------------------------------------
    def getIp(self, source: str, ip_version: Optional[str] = None):
        source = str(source)

        # 'any' means any source IP address
        if source == 'any':
            return source

        # If source is an IP address, return it directly
        if self.is_valid_ip(source):
            ip = source

        else:
            # If no source files are present, return
            if not self.get_files():
                raise Exception('source named ' + source + ' was not found (no source files were found)')

            sources = self.load()

            # If no IP was returned, then it means that the source was not found in any source file
            if source not in sources:
                raise Exception('source named ' + source + ' was not found in any source file')

            ip = sources[source]

        # Check that the IP address version matches the rule IP version
        if ip_version:
            version = ipaddress.ip_network(ip, strict=False).version
            if 'ipv' + str(version) != ip_version:
                raise Exception('source "' + source + '" (' + ip + ') is an IPv' + str(version) + ' address and cannot be used in an ' + ip_version + ' section')

        return ip


    #-----------------------------------------------------------------------------------------------
    #
    #   List all sources and their IP addresses
    #
    #-----------------------------------------------------------------------------------------------
    def list(self, search: Optional[str] = None):
        table = []

        print(' ▪ Listing sources')

        # If no source files are present, return
        if not self.get_files():
            raise Exception('No source files were found')

        # Check source files
        for file in self.get_files():
            table.append([Style.BRIGHT + 'Source file ' + Fore.GREEN + file.name + Style.RESET_ALL, ''])

            sources = self.load_file(file)

            for source in sources:
                # If a search term is provided, then only display the group that contains the search term
                if search and search not in str(source):
                    continue

                # Append source name to table
                table.append([source, sources[source]])

        print(tabulate(table, tablefmt = 'fancy_grid'), end='\n')
