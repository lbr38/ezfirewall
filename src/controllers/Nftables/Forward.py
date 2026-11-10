# coding: utf-8

# Import classes
from typing import Optional
from src.controllers.Nftables.JsonBuilder import JsonBuilder
from src.controllers.Source import Source

class Forward:
    def __init__(self, jsonBuilder: Optional[JsonBuilder] = None, sourceController: Optional[Source] = None):
        self.jsonBuilder = jsonBuilder if jsonBuilder else JsonBuilder()
        self.sourceController = sourceController if sourceController else Source()

    #-----------------------------------------------------------------------------------------------
    #
    #   Generate forward rules
    #
    #-----------------------------------------------------------------------------------------------
    def generate_forward_rules(self, ip_version: str, forward_rules: dict):
        """Generate forward rules for the given IP version"""

        # Process each forward rule group
        for rule_name, rule_config in forward_rules.items():
            action = rule_config.get('action', 'accept')
            log = rule_config.get('log', False)
            log_prefix = rule_config.get('log_prefix', f'Forward-{rule_name}')
            rules = rule_config.get('rules', [])

            # Process each rule in the group
            for rule in rules:
                self._process_forward_rule(
                    ip_version, rule, action, log, log_prefix
                )

    #-----------------------------------------------------------------------------------------------
    #
    #   Process individual forward rule
    #
    #-----------------------------------------------------------------------------------------------
    def _process_forward_rule(self, ip_version: str, rule: dict, action: str, log: bool, log_prefix: str):
        """Process and add an individual forward rule"""

        # Set the IP family based on the IP version
        family = 'ip' if ip_version == 'ipv4' else 'ip6'

        # Extract rule parameters
        from_interface = rule.get('from_interface')
        to_interface = rule.get('to_interface')
        from_source = rule.get('from_source')
        to_destination = rule.get('to_destination')
        protocol = rule.get('protocol', 'any')
        from_port = rule.get('from_port')
        to_port = rule.get('to_port')

        # Build rule expression
        expr = []

        # Input interface
        if from_interface:
            expr.append({
                "match": {
                    "op": "==",
                    "left": {"meta": {"key": "iifname"}},
                    "right": from_interface
                }
            })

        # Output interface
        if to_interface:
            expr.append({
                "match": {
                    "op": "==",
                    "left": {"meta": {"key": "oifname"}},
                    "right": to_interface
                }
            })

        # Source address
        if from_source:
            source_ip = self.sourceController.getIp(from_source, ip_version)
            if source_ip != 'any':
                expr.append({
                    "match": {
                        "op": "==",
                        "left": {"payload": {"protocol": family, "field": "saddr"}},
                        "right": self.jsonBuilder.format_ip_address(source_ip)
                    }
                })

        # Destination address
        if to_destination:
            dest_ip = self.sourceController.getIp(to_destination, ip_version)
            if dest_ip != 'any':
                expr.append({
                    "match": {
                        "op": "==",
                        "left": {"payload": {"protocol": family, "field": "daddr"}},
                        "right": self.jsonBuilder.format_ip_address(dest_ip)
                    }
                })

        # Protocol, source and destination ports
        expr.extend(self.jsonBuilder.protocol_port_matches(family, protocol, from_port, to_port))

        # Add action rule (with logging if requested)
        self.jsonBuilder.add_forward_rule(family, expr, action, log_prefix=log_prefix if log else None)
