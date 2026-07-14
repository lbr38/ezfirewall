# coding: utf-8

# Import classes
from src.controllers.Nftables.JsonBuilder import JsonBuilder
from src.controllers.Source import Source

class Input:
    def __init__(self):
        self.jsonBuilder = JsonBuilder()
        self.sourceController = Source()
        
        # Track IPs for drop sets per service: {interface: {rule_name: {family: [ips]}}}
        self.interface_drop_ips = {}
        
        # Track global IPs for 'any' interface per service: {rule_name: {family: [ips]}}
        self.any_drop_ips = {}

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
    def generate_drop_rules(self, ip_version: str, interface: str, rule_name: str, sources: list, protocol: str, ports: list):
        """Generate drop rules using sets for IP management, per service"""
        
        # Set the IP family based on the IP version
        family = 'ip' if ip_version == 'ipv4' else 'ip6'
        
        # Collect IPs from sources
        ips = []
        for source in sources:
            # Get source IP address
            ip = self.sourceController.getIp(source)
            ips.append(ip)
        
        # Validate IP list for conflicts
        if not self.jsonBuilder.validate_ip_list(ips, interface, f"drop rules ({rule_name})"):
            raise Exception(f"IP address conflicts detected in {interface}/{rule_name} drop rules. Please fix the conflicts and try again.")

        if interface == 'any':
            # Handle global 'any' interface, per rule_name
            if rule_name not in self.any_drop_ips:
                self.any_drop_ips[rule_name] = {'ip': [], 'ip6': []}
            for ip in ips:
                if ip not in self.any_drop_ips[rule_name][family]:
                    self.any_drop_ips[rule_name][family].append(ip)
        else:
            # Handle specific interface, per rule_name
            if interface not in self.interface_drop_ips:
                self.interface_drop_ips[interface] = {}
            if rule_name not in self.interface_drop_ips[interface]:
                self.interface_drop_ips[interface][rule_name] = {'ip': [], 'ip6': []}
            
            for ip in ips:
                if ip not in self.interface_drop_ips[interface][rule_name][family]:
                    self.interface_drop_ips[interface][rule_name][family].append(ip)

    #-----------------------------------------------------------------------------------------------
    #
    #   Finalize sets and rules
    #
    #-----------------------------------------------------------------------------------------------
    def finalize_sets_and_rules(self):
        """Add collected DROP IPs to sets per service"""
        
        # Add global 'any' DROP IPs to their sets
        for rule_name in self.any_drop_ips:
            for family in ['ip', 'ip6']:
                if self.any_drop_ips[rule_name][family]:
                    self.jsonBuilder.add_to_drop_set(family, 'any', rule_name, self.any_drop_ips[rule_name][family])
        
        # Add IPs to interface+rule_name specific drop sets
        for interface in self.interface_drop_ips:
            for rule_name in self.interface_drop_ips[interface]:
                for family in ['ip', 'ip6']:
                    if self.interface_drop_ips[interface][rule_name][family]:
                        self.jsonBuilder.add_to_drop_set(family, interface, rule_name, self.interface_drop_ips[interface][rule_name][family])

    #-----------------------------------------------------------------------------------------------
    #
    #   Create rules that use the sets
    #
    #-----------------------------------------------------------------------------------------------
    def create_set_based_rules(self, rules_data):
        """Create DROP rules that use per-service sets"""
        
        # Group DROP rules by interface+rule_name and protocol/ports to avoid duplicates
        interface_drop_rules = {}
        
        for rule_data in rules_data:
            if rule_data['type'] != 'drop':
                continue
                
            ip_version = rule_data['ip_version']
            interface = rule_data['interface']
            rule_name = rule_data['rule_name']
            protocol = rule_data['protocol']
            ports = rule_data['ports']
            
            family = 'ip' if ip_version == 'ipv4' else 'ip6'
            rule_key = f"{interface}_{rule_name}_{family}_{protocol}_{','.join(map(str, ports))}_drop"
            
            if rule_key not in interface_drop_rules:
                interface_drop_rules[rule_key] = {
                    'family': family,
                    'interface': interface,
                    'rule_name': rule_name,
                    'protocol': protocol,
                    'ports': ports
                }
        
        # Create DROP rules that use the per-service sets
        for rule_data in interface_drop_rules.values():
            has_ips = False
            if rule_data['interface'] == 'any':
                has_ips = (rule_data['rule_name'] in self.any_drop_ips and
                          bool(self.any_drop_ips[rule_data['rule_name']][rule_data['family']]))
            else:
                has_ips = (rule_data['interface'] in self.interface_drop_ips and
                          rule_data['rule_name'] in self.interface_drop_ips[rule_data['interface']] and
                          bool(self.interface_drop_ips[rule_data['interface']][rule_data['rule_name']][rule_data['family']]))
            
            if has_ips:
                self.jsonBuilder.add_drop_rule(
                    rule_data['family'],
                    rule_data['interface'],
                    rule_data['rule_name'],
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
    #   Get ruleset as JSON string
    #
    #-----------------------------------------------------------------------------------------------
    def get_ruleset_json(self):
        """Get the current ruleset as JSON string"""
        return self.jsonBuilder.get_ruleset_json()