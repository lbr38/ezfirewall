# coding: utf-8

# Import libraries
import re

# Import classes
from src.controllers.Nftables.JsonBuilder import JsonBuilder
from src.controllers.Source import Source

class Input:
    def __init__(self):
        self.jsonBuilder = JsonBuilder()
        self.sourceController = Source()
        
        # Track IPs for drop sets only - allow rules are individual
        self.interface_drop_ips = {}   # {interface: {family: [ips]}}
        
        # Track global IPs for 'any' interface - drop only
        self.any_drop_ips = {'ip': [], 'ip6': []}   # Global drop IPs

    #-----------------------------------------------------------------------------------------------
    #
    #   Generate allow input rules with sets
    #
    #-----------------------------------------------------------------------------------------------
    def generate_allow_rules(self, ip_version: str, interface: str, sources: list, protocol: str, ports: list, state: str = 'new,related,established'):
        """Generate individual allow rules for granular port/protocol control"""
        
        # Set the IP family based on the IP version
        family = 'ip' if ip_version == 'ipv4' else 'ip6'
        
        # If sources is not iterable or empty, skip
        if not sources:
            return

        # Create individual rule for each source IP
        for source in sources:
            # Get source IP address
            ip = self.sourceController.getIp(source)
    
            # Add allow rule
            self.jsonBuilder.add_allow_rule(family, interface, ip, protocol, ports, state)

    #-----------------------------------------------------------------------------------------------
    #
    #   Generate drop input rules with sets
    #
    #-----------------------------------------------------------------------------------------------
    def generate_drop_rules(self, ip_version: str, interface: str, sources: list, protocol: str, ports: list):
        """Generate drop rules using sets for IP management"""
        
        # Set the IP family based on the IP version
        family = 'ip' if ip_version == 'ipv4' else 'ip6'
        
        # Collect IPs from sources
        ips = []
        for source in sources:
            # Get source IP address
            ip = self.sourceController.getIp(source)
            ips.append(ip)
        
        # Validate IP list for conflicts
        if not self.jsonBuilder.validate_ip_list(ips, interface, f"drop rules ({protocol})"):
            raise Exception(f"IP address conflicts detected in {interface} drop rules. Please fix the conflicts and try again.")

        if interface == 'any':
            # Handle global 'any' interface
            for ip in ips:
                if ip not in self.any_drop_ips[family]:
                    self.any_drop_ips[family].append(ip)
        else:
            # Handle specific interface
            # Initialize interface tracking if not exists
            if interface not in self.interface_drop_ips:
                self.interface_drop_ips[interface] = {'ip': [], 'ip6': []}
            
            # Collect all IPs for this interface
            for ip in ips:
                if ip not in self.interface_drop_ips[interface][family]:
                    self.interface_drop_ips[interface][family].append(ip)

    #-----------------------------------------------------------------------------------------------
    #
    #   Finalize sets and rules
    #
    #-----------------------------------------------------------------------------------------------
    def finalize_sets_and_rules(self):
        """Add collected DROP IPs to sets - ALLOW rules are already created individually"""
        
        # Add global 'any' DROP IPs to their sets
        for family in ['ip', 'ip6']:
            if self.any_drop_ips[family]:
                self.jsonBuilder.add_to_drop_set(family, 'any', self.any_drop_ips[family])
        
        # Add IPs to interface-specific drop sets  
        for interface in self.interface_drop_ips:
            for family in ['ip', 'ip6']:
                if self.interface_drop_ips[interface][family]:
                    # Add IPs to the drop set
                    self.jsonBuilder.add_to_drop_set(family, interface, self.interface_drop_ips[interface][family])

    #-----------------------------------------------------------------------------------------------
    #
    #   Create rules that use the sets
    #
    #-----------------------------------------------------------------------------------------------
    def create_set_based_rules(self, rules_data):
        """Create DROP rules that use sets - ALLOW rules are already individual"""
        
        # Group DROP rules by interface and protocol/ports to avoid duplicates
        interface_drop_rules = {}
        
        for rule_data in rules_data:
            if rule_data['type'] != 'drop':
                continue  # Skip allow rules - they're already handled individually
                
            ip_version = rule_data['ip_version']
            interface = rule_data['interface'] 
            protocol = rule_data['protocol']
            ports = rule_data['ports']
            
            family = 'ip' if ip_version == 'ipv4' else 'ip6'
            rule_key = f"{interface}_{family}_{protocol}_{','.join(map(str, ports))}_drop"
            
            if rule_key not in interface_drop_rules:
                interface_drop_rules[rule_key] = {
                    'family': family,
                    'interface': interface,
                    'protocol': protocol,
                    'ports': ports
                }
        
        # Create DROP rules that use the sets
        for rule_data in interface_drop_rules.values():
            # Check if we have IPs in the appropriate drop set
            has_ips = False
            if rule_data['interface'] == 'any':
                has_ips = bool(self.any_drop_ips[rule_data['family']])
            else:
                has_ips = (rule_data['interface'] in self.interface_drop_ips and 
                          self.interface_drop_ips[rule_data['interface']][rule_data['family']])
            
            if has_ips:
                self.jsonBuilder.add_drop_rule(
                    rule_data['family'], 
                    rule_data['interface'], 
                    rule_data['protocol'], 
                    rule_data['ports']
                )

    #-----------------------------------------------------------------------------------------------
    #
    #   Prepare sets for nftables configuration
    #
    #-----------------------------------------------------------------------------------------------
    def prepare_sets(self, content):
        """Prepare sets for nftables configuration"""
        self.jsonBuilder.prepare_sets(content)

    #-----------------------------------------------------------------------------------------------
    #
    #   Build and apply the complete ruleset
    #
    #-----------------------------------------------------------------------------------------------
    def write(self, config):
        """Build the complete nftables ruleset"""
        self.jsonBuilder.build_ruleset(config)

    #-----------------------------------------------------------------------------------------------
    #
    #   Finalize the ruleset
    #
    #-----------------------------------------------------------------------------------------------
    def finalize(self):
        """Finalize the ruleset by adding final rules"""
        self.jsonBuilder.finalize_ruleset()

    #-----------------------------------------------------------------------------------------------
    #
    #   Check ruleset validity
    #
    #-----------------------------------------------------------------------------------------------
    def check(self):
        """Check if the ruleset is valid"""
        self.jsonBuilder.check()

    #-----------------------------------------------------------------------------------------------
    #
    #   Apply the ruleset
    #
    #-----------------------------------------------------------------------------------------------
    def apply(self):
        """Apply the ruleset to nftables"""
        self.jsonBuilder.apply()

    #-----------------------------------------------------------------------------------------------
    #
    #   Get ruleset as JSON string (for debugging)
    #
    #-----------------------------------------------------------------------------------------------
    def get_ruleset_json(self):
        """Get the current ruleset as JSON string"""
        return self.jsonBuilder.get_ruleset_json()