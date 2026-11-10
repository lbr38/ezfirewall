# coding: utf-8

# Import classes
from src.controllers.Nftables.JsonBuilder import JsonBuilder
from src.controllers.Source import Source

class Input:
    """Build the INPUT and OUTPUT rules (same syntax: protocol, ports, allow, drop)
    INPUT rules match the source addresses, OUTPUT rules match the destination addresses"""

    def __init__(self):
        self.jsonBuilder = JsonBuilder()
        self.sourceController = Source()

        # IP addresses of the drop sets: {(chain, interface, rule_name): {'ip': [...], 'ip6': [...]}}
        self.drop_ips = {}

    #-----------------------------------------------------------------------------------------------
    #
    #   Generate allow rules
    #
    #-----------------------------------------------------------------------------------------------
    def generate_allow_rules(self, ip_version: str, interface: str, sources: list, protocol: str, ports: list, chain: str = 'INPUT', state: str = 'new,related,established'):
        """Generate individual allow rules for granular port/protocol control"""

        # Set the IP family based on the IP version
        family = 'ip' if ip_version == 'ipv4' else 'ip6'

        # If sources is not iterable or empty, skip
        if not sources:
            return

        # Create individual rule for each IP address
        for source in sources:
            # Get source IP address
            ip = self.sourceController.getIp(source, ip_version)

            # Add allow rule
            self.jsonBuilder.add_allow_rule(family, interface, ip, protocol, ports, state, chain)

    #-----------------------------------------------------------------------------------------------
    #
    #   Collect the IP addresses of the drop set of a rule
    #
    #-----------------------------------------------------------------------------------------------
    def generate_drop_rules(self, ip_version: str, interface: str, rule_name: str, sources: list, protocol: str, ports: list, chain: str = 'INPUT'):
        """Collect the IP addresses to drop, per chain, interface and rule (one set per rule)"""

        # Set the IP family based on the IP version
        family = 'ip' if ip_version == 'ipv4' else 'ip6'

        # Collect IPs from sources
        ips = []
        for source in sources:
            # Get source IP address
            ip = self.sourceController.getIp(source, ip_version)
            ips.append(ip)

        # Validate IP list for conflicts
        if not self.jsonBuilder.validate_ip_list(ips, interface, f"drop rules ({rule_name})"):
            raise Exception(f"IP address conflicts detected in {interface}/{rule_name} drop rules. Please fix the conflicts and try again.")

        key = (chain, interface, rule_name)

        if key not in self.drop_ips:
            self.drop_ips[key] = {'ip': [], 'ip6': []}

        for ip in ips:
            if ip not in self.drop_ips[key][family]:
                self.drop_ips[key][family].append(ip)

    #-----------------------------------------------------------------------------------------------
    #
    #   Finalize sets and rules
    #
    #-----------------------------------------------------------------------------------------------
    def finalize_sets_and_rules(self):
        """Add collected DROP IPs to their sets"""
        for (chain, interface, rule_name), ips in self.drop_ips.items():
            for family in ['ip', 'ip6']:
                if ips[family]:
                    self.jsonBuilder.add_to_drop_set(family, interface, rule_name, ips[family], chain)

    #-----------------------------------------------------------------------------------------------
    #
    #   Create rules that use the sets
    #
    #-----------------------------------------------------------------------------------------------
    def create_set_based_rules(self, rules_data):
        """Create DROP rules that use the drop sets"""
        for rule_data in rules_data:
            if rule_data['type'] != 'drop':
                continue

            chain = rule_data.get('chain', 'INPUT')
            family = 'ip' if rule_data['ip_version'] == 'ipv4' else 'ip6'
            key = (chain, rule_data['interface'], rule_data['rule_name'])

            # Only create the rule if the set contains at least one IP address of this family
            if key not in self.drop_ips or not self.drop_ips[key][family]:
                continue

            self.jsonBuilder.add_drop_rule(
                family,
                rule_data['interface'],
                rule_data['rule_name'],
                rule_data['protocol'],
                rule_data['ports'],
                chain
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
    #   Build the base ruleset
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
