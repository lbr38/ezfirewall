# coding: utf-8

# Import libraries
import re

# Import classes
from src.controllers.Iptables.Iptables import Iptables
from src.controllers.Source import Source

class Input:
    def __init__(self):
        self.iptablesController = Iptables()
        self.sourceController = Source()

    #-----------------------------------------------------------------------------------------------
    #
    #   Allow input traffic
    #
    #-----------------------------------------------------------------------------------------------
    def allow(self, ip_version: str, interface: str, sources: list, protocols: list, ports: list, state: str = 'NEW,ESTABLISHED,RELATED'):
        # Default arguments
        iptables = '/sbin/iptables'
        interface_arg = ''

        # If ip_version is v6, set the iptables command to ip6tables
        if ip_version == 'v6':
            iptables = '/sbin/iptables6'
        
        # If interface is not all, then set the interface on which the rule will be applied
        if interface != 'all':
            interface_arg = '-i ' + interface

        # If 'all' is in the protocols list, set the protocols list to ['tcp', 'udp']
        if 'all' in protocols:
            protocols = ['tcp', 'udp']

        for source in sources:
            source = str(source).strip()

            # If source is not an IP address, get the IP address from the sources files
            if not re.match(r'^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}(\/\d{1,2})?$', source):
                sourceIp = self.sourceController.getIp(source)
            else:
                sourceIp = source

            # Allow traffic based on the specified protocols and ports
            for protocol in protocols:
                # If all protocols and all ports are specified, directly allow all from the source IP
                if 'tcp' in protocols and 'udp' in protocols and 'all' in ports:
                    # Apply the rule and continue
                    self.iptablesController.execute(iptables + ' -A INPUT ' + interface_arg + ' -s ' + sourceIp + ' -m conntrack --ctstate ' + state + ' -j ACCEPT')
                    break

                # If protocol is 'icmp', add the ICMP type
                if protocol == 'icmp':
                    protocol += ' --icmp-type 8/0'
                
                # If 'icmp' is in the ports list, no need to specify the ports as there is no real 'icmp' port
                if 'icmp' in ports:
                    self.iptablesController.execute(iptables + ' -A INPUT ' + interface_arg + ' -s ' + sourceIp + ' -p ' + str(protocol) + ' -j ACCEPT')
                    continue

                # If 'all' is in the ports list, no need to specify the ports
                if 'all' in ports:
                    self.iptablesController.execute(iptables + ' -A INPUT ' + interface_arg + ' -s ' + sourceIp + ' -p ' + str(protocol) + ' -j ACCEPT')
                    continue
            
                # Allow traffic based on the specified ports
                if ports:
                    for port in ports:
                        self.iptablesController.execute(iptables + ' -t filter -A INPUT ' + interface_arg + ' -s ' + sourceIp + ' -p ' + str(protocol) + ' -m ' + str(protocol) + ' --destination-port ' + str(port) + ' -m conntrack --ctstate ' + state + ' -j ACCEPT')
    

    #-----------------------------------------------------------------------------------------------
    #
    #   Drop input traffic
    #
    #-----------------------------------------------------------------------------------------------
    def drop(self, ip_version: str, interface: str, sources: list, protocols: list, ports: list):
        # Default arguments
        iptables = '/sbin/iptables'
        interface_arg = ''

        # If ip_version is v6, set the iptables command to ip6tables
        if ip_version == 'v6':
            iptables = '/sbin/iptables6'
        
        # If interface is not all, then set the interface on which the rule will be applied
        if interface != 'all':
            interface_arg = '-i ' + interface

        # If 'all' is in the protocols list, set the protocols list to ['tcp', 'udp']
        if 'all' in protocols:
            protocols = ['tcp', 'udp']

        for source in sources:
            source = str(source).strip()

            # If source is not an IP address, get the IP address from the sources files
            if not re.match(r'^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}(\/\d{1,2})?$', source):
                sourceIp = self.sourceController.getIp(source)
            else:
                sourceIp = source

            # Drop traffic based on the specified protocols and ports
            for protocol in protocols:
                # If all protocols and all ports are specified, directly drop all from the source IP
                if 'tcp' in protocols and 'udp' in protocols and 'all' in ports:
                    # Apply the rule and continue
                    self.iptablesController.execute(iptables + ' -A INPUT ' + interface_arg + ' -s ' + sourceIp + ' -j DROP')
                    break

                # If protocol is 'icmp', add the ICMP type
                if protocol == 'icmp':
                    protocol += ' --icmp-type 8/0'

                # If 'icmp' is in the ports list, no need to specify the ports as there is no real 'icmp' port
                if 'icmp' in ports:
                    self.iptablesController.execute(iptables + ' -A INPUT ' + interface_arg + ' -s ' + sourceIp + ' -p ' + str(protocol) + ' -j DROP')
                    continue

                # If 'all' is in the ports list, no need to specify the ports
                if 'all' in ports:
                    self.iptablesController.execute(iptables + ' -A INPUT ' + interface_arg + ' -s ' + sourceIp + ' -p ' + str(protocol) + ' -j DROP')
                    continue

                # Drop traffic based on the specified ports
                if ports:
                    for port in ports:
                        self.iptablesController.execute(iptables + ' -A INPUT ' + interface_arg + ' -s ' + sourceIp + ' -p ' + str(protocol) + ' --destination-port ' + str(port) + ' -j DROP')
