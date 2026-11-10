# coding: utf-8

# Import classes
from typing import Optional
from src.controllers.Nftables.JsonBuilder import JsonBuilder
from src.controllers.Source import Source

class Nat:
    def __init__(self, jsonBuilder: Optional[JsonBuilder] = None, sourceController: Optional[Source] = None):
        self.jsonBuilder = jsonBuilder if jsonBuilder else JsonBuilder()
        self.sourceController = sourceController if sourceController else Source()

    #-----------------------------------------------------------------------------------------------
    #
    #   Generate NAT rules
    #
    #-----------------------------------------------------------------------------------------------
    def generate_nat_rules(self, ip_version: str, nat_rules: dict):
        """Generate NAT rules for the given IP version"""

        # Process PREROUTING rules
        if 'prerouting' in nat_rules:
            for rule_name, rule_config in nat_rules['prerouting'].items():
                self._process_prerouting_rule(ip_version, rule_config)

        # Process POSTROUTING rules
        if 'postrouting' in nat_rules:
            for rule_name, rule_config in nat_rules['postrouting'].items():
                self._process_postrouting_rule(ip_version, rule_config)

    #-----------------------------------------------------------------------------------------------
    #
    #   Helper: Build an address match (None if the address is 'any')
    #
    #-----------------------------------------------------------------------------------------------
    def _address_match(self, ip_version: str, field: str, address: str):
        """Return the match of a source/destination address"""
        family = 'ip' if ip_version == 'ipv4' else 'ip6'
        ip = self.sourceController.getIp(address, ip_version)

        if ip == 'any':
            return None

        return {
            "match": {
                "op": "==",
                "left": {"payload": {"protocol": family, "field": field}},
                "right": self.jsonBuilder.format_ip_address(ip)
            }
        }

    #-----------------------------------------------------------------------------------------------
    #
    #   Helper: Get the address to translate to (source alias or IP address)
    #
    #-----------------------------------------------------------------------------------------------
    def _nat_address(self, ip_version: str, address: str):
        """Return the address used by a dnat/snat statement"""
        ip = self.sourceController.getIp(address, ip_version)

        if ip == 'any':
            raise Exception('"any" cannot be used as a NAT address')

        return self.jsonBuilder.format_ip_address(ip)

    #-----------------------------------------------------------------------------------------------
    #
    #   Process PREROUTING NAT rule
    #
    #-----------------------------------------------------------------------------------------------
    def _process_prerouting_rule(self, ip_version: str, rule_config: dict):
        """Process and add a PREROUTING NAT rule (DNAT)"""

        # Set the IP family based on the IP version
        family = 'ip' if ip_version == 'ipv4' else 'ip6'

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
            match = self._address_match(ip_version, 'daddr', destination)
            if match:
                expr.append(match)

        # Protocol and destination port
        expr.extend(self.jsonBuilder.protocol_port_matches(family, protocol, dport=to_port))

        # DNAT action
        self.jsonBuilder.add_nat_rule(family, "prerouting", expr, {"dnat": {"addr": self._nat_address(ip_version, to_destination)}})

    #-----------------------------------------------------------------------------------------------
    #
    #   Process POSTROUTING NAT rule
    #
    #-----------------------------------------------------------------------------------------------
    def _process_postrouting_rule(self, ip_version: str, rule_config: dict):
        """Process and add a POSTROUTING NAT rule (SNAT/MASQUERADE)"""

        # Set the IP family based on the IP version
        family = 'ip' if ip_version == 'ipv4' else 'ip6'

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
            match = self._address_match(ip_version, 'saddr', source)
            if match:
                expr.append(match)

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
        expr.extend(self.jsonBuilder.protocol_port_matches(family, protocol))

        # SNAT or MASQUERADE action
        if masquerade:
            self.jsonBuilder.add_nat_rule(family, "postrouting", expr, "masquerade")
        else:
            self.jsonBuilder.add_nat_rule(family, "postrouting", expr, {"snat": {"addr": self._nat_address(ip_version, to_source)}})
