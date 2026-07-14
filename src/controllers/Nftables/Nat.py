# coding: utf-8

# Import classes
from typing import Optional
from src.controllers.Nftables.JsonBuilder import JsonBuilder
from src.controllers.Source import Source

class Nat:
    def __init__(self, jsonBuilder: Optional[JsonBuilder] = None):
        self.jsonBuilder = jsonBuilder if jsonBuilder else JsonBuilder()
        self.sourceController = Source()

    #-----------------------------------------------------------------------------------------------
    #
    #   Generate NAT rules
    #
    #-----------------------------------------------------------------------------------------------
    def generate_nat_rules(self, ip_version: str, nat_rules: dict):
        """Generate NAT rules for the given IP version"""
        
        # Set the IP family based on the IP version
        family = 'ip' if ip_version == 'ipv4' else 'ip6'
        
        # Process PREROUTING rules
        if 'prerouting' in nat_rules:
            for rule_name, rule_config in nat_rules['prerouting'].items():
                self._process_prerouting_rule(family, rule_config)
        
        # Process POSTROUTING rules
        if 'postrouting' in nat_rules:
            for rule_name, rule_config in nat_rules['postrouting'].items():
                self._process_postrouting_rule(family, rule_config)

    #-----------------------------------------------------------------------------------------------
    #
    #   Process PREROUTING NAT rule
    #
    #-----------------------------------------------------------------------------------------------
    def _process_prerouting_rule(self, family: str, rule_config: dict):
        """Process and add a PREROUTING NAT rule (DNAT)"""
        
        # Extract rule parameters
        destination = rule_config.get('destination')
        in_interface = rule_config.get('in_interface')
        protocol = rule_config.get('protocol', 'any')
        to_port = rule_config.get('to_port')
        to_destination = rule_config.get('to_destination')
        
        # Build rule expression
        expr = []
        
        # Input interface
        if in_interface:
            expr.append({
                "match": {
                    "op": "==",
                    "left": {"meta": {"key": "iifname"}},
                    "right": in_interface
                }
            })
        
        # Destination address
        if destination:
            dest_ip = self.sourceController.getIp(destination) if not self._is_ip_address(destination) else destination
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
        
        # Destination port
        if to_port and protocol in ['tcp', 'udp']:
            expr.append({
                "match": {
                    "op": "==",
                    "left": {"payload": {"protocol": protocol, "field": "dport"}},
                    "right": to_port
                }
            })
        
        # DNAT action
        if to_destination:
            dnat_target = self.sourceController.getIp(to_destination) if not self._is_ip_address(to_destination) else to_destination
            self.jsonBuilder.add_nat_rule(family, "prerouting", expr, {"dnat": {"addr": self.jsonBuilder.format_ip_address(dnat_target)}})

    #-----------------------------------------------------------------------------------------------
    #
    #   Process POSTROUTING NAT rule
    #
    #-----------------------------------------------------------------------------------------------
    def _process_postrouting_rule(self, family: str, rule_config: dict):
        """Process and add a POSTROUTING NAT rule (SNAT/MASQUERADE)"""
        
        # Extract rule parameters
        source = rule_config.get('source')
        out_interface = rule_config.get('out_interface')
        protocol = rule_config.get('protocol', 'any')
        to_source = rule_config.get('to_source')
        masquerade = rule_config.get('masquerade', False)
        
        # Build rule expression
        expr = []
        
        # Source address
        if source:
            source_ip = self.sourceController.getIp(source) if not self._is_ip_address(source) else source
            expr.append({
                "match": {
                    "op": "==",
                    "left": {"payload": {"protocol": family, "field": "saddr"}},
                    "right": self.jsonBuilder.format_ip_address(source_ip)
                }
            })
        
        # Output interface
        if out_interface:
            expr.append({
                "match": {
                    "op": "==",
                    "left": {"meta": {"key": "oifname"}},
                    "right": out_interface
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
        
        # SNAT or MASQUERADE action
        if masquerade:
            self.jsonBuilder.add_nat_rule(family, "postrouting", expr, "masquerade")
        elif to_source:
            if to_source == "auto":
                # Use MASQUERADE for auto-detection
                self.jsonBuilder.add_nat_rule(family, "postrouting", expr, "masquerade")
            else:
                # Use specific IP for SNAT
                snat_ip = self.sourceController.getIp(to_source) if not self._is_ip_address(to_source) else to_source
                self.jsonBuilder.add_nat_rule(family, "postrouting", expr, {"snat": {"addr": self.jsonBuilder.format_ip_address(snat_ip)}})

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