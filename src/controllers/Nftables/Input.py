# coding: utf-8

# Import libraries
import re

# Import classes
from src.controllers.Nftables.Nftables import Nftables
from src.controllers.Source import Source

class Input:
    def __init__(self):
        self.nftablesController = Nftables()
        self.sourceController = Source()

        self.ipv4_rules = {
            'ipv4': {
                'allow': [],
                'drop': []
            },
            'ipv6': {
                'allow': [],
                'drop': []
            }
        }

        self.ipv6_rules = {
            'ipv4': {
                'allow': [],
                'drop': []
            },
            'ipv6': {
                'allow': [],
                'drop': []
            }
        }

    #-----------------------------------------------------------------------------------------------
    #
    #   Generate allow input rules
    #
    #-----------------------------------------------------------------------------------------------
    def generate_allow_rules(self, ip_version: str, interface: str, sources: list, protocol: str, ports: list, state: str = 'new, related, established'):
        # Default arguments
        interface_arg = ''
        ports_arg = ''
        
        #
        # If interface is not 'any', then set the interface on which the rule will be applied
        #
        if interface != 'any':
            interface_arg = 'iifname ' + interface

        #
        # Generate the ports list, separated by commas
        # Only if ports is defined and is not 'any'
        #
        if ports and not 'any' in ports:
            ports_arg = 'dport {' + ','.join(map(str, ports)) + '}'

        for source in sources:
            source = str(source).strip()

            #
            # If source is not an IP address, get the IP address from the sources files
            #
            if not re.match(r'^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}(\/\d{1,2})?$', source):
                sourceIp = self.sourceController.getIp(source)
            else:
                sourceIp = source

            #
            # Allow traffic based on the specified protocol
            #
            # If both port and protocol are 'any', allow all traffic for the specified source
            if protocol == 'any' and 'any' in ports:
                self.ipv4_rules['ipv' + str(ip_version)]['allow'].append(interface_arg + ' ip saddr ' + sourceIp + ' ct state ' + state + ' accept')
                continue

            # If protocol is 'any', use meta l4proto {tcp, udp} to match both TCP and UDP
            if protocol == 'any':
                self.ipv4_rules['ipv' + str(ip_version)]['allow'].append(interface_arg + ' ip saddr ' + sourceIp + ' meta l4proto {tcp, udp} th ' + ports_arg + ' ct state ' + state + ' accept')

            # If protocol is 'tcp' or 'udp'
            if protocol == 'tcp' or protocol == 'udp':
                # If there is no port specified, use meta l4proto to match only the protocol without ports
                if ports_arg == '':
                    protocol = 'meta l4proto ' + protocol

                self.ipv4_rules['ipv' + str(ip_version)]['allow'].append(interface_arg + ' ip saddr ' + sourceIp + ' ' + protocol + ' ' + ports_arg + ' ct state ' + state + ' accept')

            # If protocol is 'icmp'
            if protocol == 'icmp':
                self.ipv4_rules['ipv' + str(ip_version)]['allow'].append(interface_arg + ' ip saddr ' + sourceIp + ' icmp type echo-request accept')


    #-----------------------------------------------------------------------------------------------
    #
    #   Generate drop input rules
    #
    #-----------------------------------------------------------------------------------------------
    def generate_drop_rules(self, ip_version: str, interface: str, sources: list, protocol: str, ports: list):
        # Default arguments
        interface_arg = ''
        ports_arg = ''
        
        #
        # If interface is not 'any', then set the interface on which the rule will be applied
        #
        if interface != 'any':
            interface_arg = 'iifname ' + interface

        #
        # Generate the ports list, separated by commas
        # Only if ports is defined and is not 'any'
        #
        if ports and not 'any' in ports:
            ports_arg = 'dport {' + ','.join(map(str, ports)) + '}'

        for source in sources:
            source = str(source).strip()

            #
            # If source is not an IP address, get the IP address from the sources files
            #
            if not re.match(r'^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}(\/\d{1,2})?$', source):
                sourceIp = self.sourceController.getIp(source)
            else:
                sourceIp = source

            #
            # Drop traffic based on the specified protocol and ports
            #
            # If both port and protocol are 'any', drop all traffic for the specified source
            if protocol == 'any' and 'any' in ports:
                self.ipv4_rules['ipv' + str(ip_version)]['drop'].append(interface_arg + ' ip saddr ' + sourceIp + ' drop')
                continue

            # If protocol is 'any', use meta l4proto {tcp, udp} to match both TCP and UDP
            if protocol == 'any':
                self.ipv4_rules['ipv' + str(ip_version)]['drop'].append(interface_arg + ' ip saddr ' + sourceIp + ' meta l4proto {tcp, udp} th ' + ports_arg + ' drop')

            # If protocol is 'tcp' or 'udp'
            if protocol == 'tcp' or protocol == 'udp':
                # If there is no port specified, use meta l4proto to match only the protocol without ports
                if ports_arg == '':
                    protocol = 'meta l4proto ' + protocol

                self.ipv4_rules['ipv' + str(ip_version)]['drop'].append(interface_arg + ' ip saddr ' + sourceIp + ' ' + protocol + ' ' + ports_arg + ' drop')

            # If protocol is 'icmp'
            if protocol == 'icmp':
                self.ipv4_rules['ipv' + str(ip_version)]['drop'].append(interface_arg + ' ip saddr ' + sourceIp + ' icmp type echo-request drop')


    #-----------------------------------------------------------------------------------------------
    #
    #   Write rules and config to nftables configuration file
    #
    #-----------------------------------------------------------------------------------------------
    def write(self, config):
        #
        # Get the nftables template
        #
        with open('/etc/nftables.conf.new', 'r') as infile:
            file = infile.read()

        #
        # Replace the template with the rules
        # Convert list to string with rules separated by line breaks
        #
        file = file.replace('__IPV4_RULES__', '\n        '.join([*self.ipv4_rules['ipv4']['drop'], *self.ipv4_rules['ipv4']['allow']]))
        file = file.replace('__IPV6_RULES__', '\n        '.join([*self.ipv6_rules['ipv6']['drop'], *self.ipv6_rules['ipv6']['allow']]))

        #
        # Enable or disable IPv4 and IPv6 logging of dropped packets
        #
        file = file.replace('__IPV4_LOG_DROP__', 'log prefix "[nftables-drop] IPv4 inbound denied: " counter drop' if config['ipv4']['log_dropped_traffic'] else '')
        file = file.replace('__IPV6_LOG_DROP__', 'log prefix "[nftables-drop] IPv6 inbound denied: " counter drop' if config['ipv6']['log_dropped_traffic'] else '')

        #
        # Set the default policies (accept or drop)
        #
        file = file.replace('__IPV4_DEFAULT_POLICY__', config['ipv4']['input_default_policy'])
        file = file.replace('__IPV6_DEFAULT_POLICY__', config['ipv6']['input_default_policy'])

        #
        # Write the new file
        #
        with open('/etc/nftables.conf.new', 'w') as ofile:
            ofile.write(file)
            ofile.close()
