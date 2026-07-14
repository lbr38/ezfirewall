# coding: utf-8

# Import classes
from typing import Optional
from src.controllers.Nftables.JsonBuilder import JsonBuilder
from src.controllers.Source import Source

class Forward:
    def __init__(self, jsonBuilder: Optional[JsonBuilder] = None):
        self.jsonBuilder = jsonBuilder if jsonBuilder else JsonBuilder()
        self.sourceController = Source()

    #-----------------------------------------------------------------------------------------------
    #
    #   Generate forward rules
    #
    #-----------------------------------------------------------------------------------------------
    def generate_forward_rules(self, ip_version: str, forward_rules: dict):
        """Generate forward rules for the given IP version"""
        
        # Set the IP family based on the IP version
        family = 'ip' if ip_version == 'ipv4' else 'ip6'
        
        # Process each forward rule group
        for rule_name, rule_config in forward_rules.items():
            action = rule_config.get('action', 'accept')
            log = rule_config.get('log', False)
            log_prefix = rule_config.get('log_prefix', f'Forward-{rule_name}')
            rules = rule_config.get('rules', [])
            
            # Process each rule in the group
            for rule in rules:
                self._process_forward_rule(
                    family, rule, action, log, log_prefix
                )

    #-----------------------------------------------------------------------------------------------
    #
    #   Process individual forward rule
    #
    #-----------------------------------------------------------------------------------------------
    def _process_forward_rule(self, family: str, rule: dict, action: str, log: bool, log_prefix: str):
        """Process and add an individual forward rule"""
        
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
            source_ip = self.sourceController.getIp(from_source) if not self._is_ip_address(from_source) else from_source
            expr.append({
                "match": {
                    "op": "==",
                    "left": {"payload": {"protocol": family, "field": "saddr"}},
                    "right": self.jsonBuilder.format_ip_address(source_ip)
                }
            })
        
        # Destination address
        if to_destination:
            dest_ip = self.sourceController.getIp(to_destination) if not self._is_ip_address(to_destination) else to_destination
            expr.append({
                "match": {
                    "op": "==",
                    "left": {"payload": {"protocol": family, "field": "daddr"}},
                    "right": self.jsonBuilder.format_ip_address(dest_ip)
                }
            })
        
        # Protocol
        if protocol and protocol != 'any':
            expr.append({
                "match": {
                    "op": "==",
                    "left": {"payload": {"protocol": family, "field": "protocol"}},
                    "right": protocol
                }
            })
        
        # Source port
        if from_port and protocol in ['tcp', 'udp']:
            expr.append({
                "match": {
                    "op": "==",
                    "left": {"payload": {"protocol": protocol, "field": "sport"}},
                    "right": from_port
                }
            })
        
        # Destination port
        if to_port and protocol in ['tcp', 'udp']:
            expr.append({
                "match": {
                    "op": "==",
                    "left": {"payload": {"protocol": protocol, "field": "dport"}},
                    "right": to_port
                }
            })
        
        # Add logging if requested
        if log:
            self.jsonBuilder.add_forward_rule(family, expr.copy(), "log", log_prefix=log_prefix)
        
        # Add action rule
        self.jsonBuilder.add_forward_rule(family, expr, action)

    #-----------------------------------------------------------------------------------------------
    #
    #   Helper: Check if string is an IP address or CIDR
    #
    #-----------------------------------------------------------------------------------------------
    def _is_ip_address(self, string: str) -> bool:
        """Check if a string is an IP address or CIDR notation"""
        try:
            import ipaddress
            # Try to parse as IP network (handles both single IPs and CIDR)
            ipaddress.ip_network(string, strict=False)
            return True
        except ValueError:
            return False