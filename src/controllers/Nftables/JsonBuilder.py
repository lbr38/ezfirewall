# coding: utf-8

# Import libraries
import re
import json
import ipaddress
from colorama import Fore, Style

class JsonBuilder:
    def __init__(self):
        # Initialize ruleset structure
        self.ruleset = {
            "nftables": []
        }
        
        # Drop sets to create, per family: list of {'chain': 'INPUT'|'OUTPUT', 'interface': ..., 'rule_name': ...}
        self.sets = {
            'ipv4': [],
            'ipv6': []
        }

        # Final INPUT rules (log and/or drop), added at the end of the ruleset
        self._final_rules = []

    #-----------------------------------------------------------------------------------------------
    #
    #   Get the name of a drop set
    #
    #-----------------------------------------------------------------------------------------------
    def drop_set_name(self, interface, rule_name, chain='INPUT'):
        """Return the name of the drop set of a chain+interface+rule_name"""
        direction = 'in' if chain == 'INPUT' else 'out'

        # Characters that are not allowed in a set name (e.g. interface wildcard 'eth*') are replaced,
        # otherwise the ruleset saved in /etc/nftables.conf could not be loaded
        return re.sub(r'[^A-Za-z0-9_.-]', '_', f"ez_{direction}_{interface}_{rule_name}_drop")

    #-----------------------------------------------------------------------------------------------
    #
    #   Flush existing ruleset
    #
    #-----------------------------------------------------------------------------------------------
    def flush_ruleset(self):
        """Flush all existing nftables rules"""
        self.ruleset["nftables"].append({"flush": {"ruleset": None}})

    #-----------------------------------------------------------------------------------------------
    #
    #   Create IPv4 and IPv6 filter tables
    #
    #-----------------------------------------------------------------------------------------------
    def create_tables(self):
        """Create IPv4 and IPv6 filter tables"""
        # IPv4 filter table
        self.ruleset["nftables"].append({
            "table": {
                "family": "ip",
                "name": "filter"
            }
        })
        
        # IPv6 filter table
        self.ruleset["nftables"].append({
            "table": {
                "family": "ip6",
                "name": "filter"
            }
        })

    #-----------------------------------------------------------------------------------------------
    #
    #   Create sets for IPv4 and IPv6 interfaces
    #
    #-----------------------------------------------------------------------------------------------
    def create_sets(self):
        """Create sets for managing DROP IP addresses per chain, interface and rule"""
        for ip_version, family, set_type in [('ipv4', 'ip', 'ipv4_addr'), ('ipv6', 'ip6', 'ipv6_addr')]:
            for drop_set in self.sets[ip_version]:
                self.ruleset["nftables"].append({
                    "set": {
                        "family": family,
                        "table": "filter",
                        "name": self.drop_set_name(drop_set['interface'], drop_set['rule_name'], drop_set['chain']),
                        "type": set_type,
                        "flags": ["interval"]
                    }
                })

    #-----------------------------------------------------------------------------------------------
    #
    #   Create chains (INPUT, FORWARD, OUTPUT)
    #
    #-----------------------------------------------------------------------------------------------
    def create_chains(self, config):
        """Create base chains for IPv4 and IPv6"""
        
        # IPv4 chains
        self._create_input_chain("ip", config['ipv4']['input_default_policy'])
        self._create_forward_chain("ip", config['ipv4']['forward_default_policy'])
        self._create_output_chain("ip", config['ipv4']['output_default_policy'])
        
        # IPv6 chains
        self._create_input_chain("ip6", config['ipv6']['input_default_policy'])
        self._create_forward_chain("ip6", config['ipv6']['forward_default_policy'])
        self._create_output_chain("ip6", config['ipv6']['output_default_policy'])
        
    def _create_input_chain(self, family, policy):
        """Create INPUT chain for specified family"""
        self.ruleset["nftables"].append({
            "chain": {
                "family": family,
                "table": "filter",
                "name": "INPUT",
                "type": "filter",
                "hook": "input",
                "prio": 0,
                "policy": policy
            }
        })
        
    def _create_forward_chain(self, family, policy):
        """Create FORWARD chain for specified family"""
        self.ruleset["nftables"].append({
            "chain": {
                "family": family,
                "table": "filter",
                "name": "FORWARD",
                "type": "filter",
                "hook": "forward",
                "prio": 0,
                "policy": policy
            }
        })
        
    def _create_output_chain(self, family, policy):
        """Create OUTPUT chain for specified family"""
        self.ruleset["nftables"].append({
            "chain": {
                "family": family,
                "table": "filter",
                "name": "OUTPUT",
                "type": "filter",
                "hook": "output",
                "prio": 0,
                "policy": policy
            }
        })

    #-----------------------------------------------------------------------------------------------
    #
    #   Add base rules (conntrack, loopback, etc.)
    #
    #-----------------------------------------------------------------------------------------------
    def add_base_rules(self, config):
        """Add base rules for both IPv4 and IPv6"""
        
        families = ["ip", "ip6"]
        for family in families:
            # INPUT and OUTPUT chains share the same base rules: accept established and related connections,
            # drop invalid packets and accept loopback traffic
            for chain, interface_key in [("INPUT", "iifname"), ("OUTPUT", "oifname")]:
                # Connection tracking rules - accept established and related
                self._add_base_rule(family, chain, [
                    {
                        "match": {
                            "op": "==",
                            "left": {"ct": {"key": "state"}},
                            "right": {"set": ["established", "related"]}
                        }
                    },
                    {"accept": None}
                ])

                # Drop invalid packets
                self._add_base_rule(family, chain, [
                    {
                        "match": {
                            "op": "==",
                            "left": {"ct": {"key": "state"}},
                            "right": "invalid"
                        }
                    },
                    {"drop": None}
                ])

                # Allow loopback
                self._add_base_rule(family, chain, [
                    {
                        "match": {
                            "op": "==",
                            "left": {"meta": {"key": interface_key}},
                            "right": "lo"
                        }
                    },
                    {"accept": None}
                ])

                # Allow IPv6 neighbor discovery: these packets are not tracked by conntrack (ct state 'untracked'),
                # so they would be dropped by the default policy and IPv6 connectivity would be broken
                if family == "ip6":
                    self._add_base_rule(family, chain, [
                        {
                            "match": {
                                "op": "==",
                                "left": {"payload": {"protocol": "icmpv6", "field": "type"}},
                                "right": {"set": ["nd-router-solicit", "nd-router-advert", "nd-neighbor-solicit", "nd-neighbor-advert"]}
                            }
                        },
                        {"accept": None}
                    ])

            # Connection tracking rules for the FORWARD chain - accept established
            # and related traffic so that the return packets of forwarded
            # connections are not dropped by the default 'drop' policy
            self._add_base_rule(family, "FORWARD", [
                {
                    "match": {
                        "op": "==",
                        "left": {"ct": {"key": "state"}},
                        "right": {"set": ["established", "related"]}
                    }
                },
                {"accept": None}
            ])

            # Drop invalid packets in the FORWARD chain
            self._add_base_rule(family, "FORWARD", [
                {
                    "match": {
                        "op": "==",
                        "left": {"ct": {"key": "state"}},
                        "right": "invalid"
                    }
                },
                {"drop": None}
            ])

        # Add final INPUT and OUTPUT rules for logging and dropping (after all custom rules are added)
        # No final rule is added to the FORWARD chain: its default policy applies, so that rules appended
        # to the chain by other services (e.g. docker) keep working
        for family in families:
            ip_version = "ipv4" if family == "ip" else "ipv6"

            for chain, policy_key, direction in [("INPUT", "input_default_policy", "inbound"), ("OUTPUT", "output_default_policy", "outbound")]:
                # If the default policy is 'accept', new connections are not dropped (and so not logged)
                if config[ip_version][policy_key] != 'drop':
                    continue

                # Drop new connections by default
                expr = [
                    {
                        "match": {
                            "op": "==",
                            "left": {"ct": {"key": "state"}},
                            "right": "new"
                        }
                    }
                ]

                # Add logging if enabled
                if config[ip_version]['log_dropped_traffic']:
                    # Generate correct log prefix based on IP version and direction
                    log_prefix = f"[nftables-drop] IPv{ip_version[-1]} {direction} denied: "
                    expr.append({"log": {"prefix": log_prefix}})
                    expr.append({"counter": None})

                expr.append({"drop": None})

                # Store this for later - will be added at the end
                self._final_rules.append({
                    "rule": {
                        "family": family,
                        "table": "filter",
                        "chain": chain,
                        "expr": expr
                    }
                })

    def _add_base_rule(self, family, chain, expr):
        """Add a rule to a chain of the filter table"""
        self.ruleset["nftables"].append({
            "rule": {
                "family": family,
                "table": "filter",
                "chain": chain,
                "expr": expr
            }
        })

    #-----------------------------------------------------------------------------------------------
    #
    #   Format IP address for nftables JSON
    #
    #-----------------------------------------------------------------------------------------------
    def format_ip_address(self, ip_address):
        """Format IP address for nftables JSON, handling CIDR notation"""
        if '/' in ip_address:
            # CIDR notation - split address and prefix (host bits are cleared, e.g. 10.0.0.1/24 => 10.0.0.0/24)
            network = ipaddress.ip_network(ip_address, strict=False)
            return {
                "prefix": {
                    "addr": str(network.network_address),
                    "len": network.prefixlen
                }
            }
        else:
            # Single IP address
            return ip_address

    #-----------------------------------------------------------------------------------------------
    #
    #   Validate IP list for conflicting intervals
    #
    #-----------------------------------------------------------------------------------------------
    def validate_ip_list(self, ip_addresses, interface, rule_name):
        """Validate IP addresses for conflicting intervals and report errors"""
        
        if not ip_addresses:
            return True
            
        # Separate individual IPs and CIDR ranges
        individual_ips = []
        cidr_ranges = []
        invalid_ips = []
        
        for ip in ip_addresses:
            if ip == "any":
                continue
            try:
                if '/' in ip:
                    cidr_ranges.append((ip, ipaddress.ip_network(ip, strict=False)))
                else:
                    individual_ips.append((ip, ipaddress.ip_address(ip)))
            except ValueError:
                invalid_ips.append(ip)
        
        # Check for invalid IP addresses
        if invalid_ips:
            print(f"\n{Fore.RED}✗ Invalid IP addresses found in {interface} → {rule_name}:{Style.RESET_ALL}")
            for ip in invalid_ips:
                print(f"  • {ip}")
            return False
        
        # Check for individual IPs covered by CIDR ranges
        conflicts = []
        for ip_str, ip_obj in individual_ips:
            for cidr_str, cidr_obj in cidr_ranges:
                try:
                    if ip_obj in cidr_obj:
                        conflicts.append(f"IP {ip_str} is already covered by CIDR range {cidr_str}")
                except:
                    continue
        
        # Check for overlapping CIDR ranges
        for i, (cidr1_str, cidr1_obj) in enumerate(cidr_ranges):
            for j, (cidr2_str, cidr2_obj) in enumerate(cidr_ranges[i+1:], i+1):
                try:
                    if cidr1_obj.overlaps(cidr2_obj):
                        conflicts.append(f"CIDR ranges {cidr1_str} and {cidr2_str} overlap")
                except:
                    continue
        
        # Report conflicts
        if conflicts:
            print(f"\n{Fore.RED}✗ IP address conflicts found in {interface} → {rule_name}:{Style.RESET_ALL}")
            for conflict in conflicts:
                print(f"  • {conflict}")
            print(f"{Fore.YELLOW}  ℹ Please remove redundant IP addresses to avoid nftables interval conflicts{Style.RESET_ALL}")
            return False
            
        return True

    #-----------------------------------------------------------------------------------------------
    #
    #   Add IP addresses to drop sets only
    #
    #-----------------------------------------------------------------------------------------------
    def add_to_drop_set(self, family, interface, rule_name, ip_addresses, chain='INPUT'):
        """Add IP addresses to the drop set for a specific chain, interface and rule"""
        if not ip_addresses:
            return
            
        # Format IP addresses for the set
        formatted_ips = []
        for ip in ip_addresses:
            if ip != "any":
                formatted_ips.append(self.format_ip_address(ip))
        
        set_name = self.drop_set_name(interface, rule_name, chain)

        if formatted_ips:
            self.ruleset["nftables"].append({
                "element": {
                    "family": family,
                    "table": "filter",
                    "name": set_name,
                    "elem": formatted_ips
                }
            })
    
    #-----------------------------------------------------------------------------------------------
    #
    #   Helper: Build port value (single port or set of ports)
    #
    #-----------------------------------------------------------------------------------------------
    def _port_value(self, ports):
        """Return the JSON value matching a port or a list of ports"""
        if not isinstance(ports, list):
            return int(ports)
        if len(ports) == 1:
            return int(ports[0])
        return {"set": [int(p) for p in ports]}

    #-----------------------------------------------------------------------------------------------
    #
    #   Helper: Build protocol and destination port matches of an input rule
    #
    #-----------------------------------------------------------------------------------------------
    def _input_protocol_matches(self, family, protocol, ports):
        """Return the protocol/port matches of an input rule"""
        expr = []
        specific_ports = bool(ports) and 'any' not in ports

        if protocol == 'any':
            # 'any' means all protocols, or tcp and udp when ports are specified (ports only exist for tcp/udp)
            if specific_ports:
                expr.append({
                    "match": {
                        "op": "==",
                        "left": {"meta": {"key": "l4proto"}},
                        "right": {"set": ["tcp", "udp"]}
                    }
                })
                expr.append({
                    "match": {
                        "op": "==",
                        "left": {"payload": {"protocol": "th", "field": "dport"}},
                        "right": {"set": [int(p) for p in ports]}
                    }
                })
        elif protocol in ['tcp', 'udp']:
            if specific_ports:
                expr.append({
                    "match": {
                        "op": "==",
                        "left": {"payload": {"protocol": protocol, "field": "dport"}},
                        "right": self._port_value(ports)
                    }
                })
            else:
                expr.append({
                    "match": {
                        "op": "==",
                        "left": {"meta": {"key": "l4proto"}},
                        "right": protocol
                    }
                })
        elif protocol == 'icmp':
            # Handle both ICMPv4 and ICMPv6
            icmp_protocol = "icmp" if family == "ip" else "icmpv6"
            expr.append({
                "match": {
                    "op": "==",
                    "left": {"payload": {"protocol": icmp_protocol, "field": "type"}},
                    "right": "echo-request"
                }
            })
        else:
            # Should never happen as the rules are validated before, but never generate a rule that
            # would match more traffic than expected
            raise Exception('unsupported protocol "' + str(protocol) + '"')

        return expr

    #-----------------------------------------------------------------------------------------------
    #
    #   Build protocol and port matches of a forward or NAT rule
    #
    #-----------------------------------------------------------------------------------------------
    def protocol_port_matches(self, family, protocol, sport=None, dport=None):
        """Return the protocol/port matches of a forward or NAT rule"""
        expr = []

        # Protocol ('any' with ports means tcp and udp)
        if protocol == 'icmp':
            l4proto = "icmp" if family == "ip" else "icmpv6"
        elif protocol == 'any':
            l4proto = {"set": ["tcp", "udp"]} if (sport or dport) else None
        else:
            l4proto = protocol

        if l4proto:
            expr.append({
                "match": {
                    "op": "==",
                    "left": {"meta": {"key": "l4proto"}},
                    "right": l4proto
                }
            })

        # Source and destination ports ('th' matches both tcp and udp)
        port_protocol = protocol if protocol in ['tcp', 'udp'] else 'th'
        for field, ports in [('sport', sport), ('dport', dport)]:
            if ports:
                expr.append({
                    "match": {
                        "op": "==",
                        "left": {"payload": {"protocol": port_protocol, "field": field}},
                        "right": self._port_value(ports)
                    }
                })

        return expr

    #-----------------------------------------------------------------------------------------------
    #
    #   Generate allow rules
    #
    #-----------------------------------------------------------------------------------------------
    def add_allow_rule(self, family, interface, ip, protocol, ports, state="new,related,established", chain='INPUT'):
        """Add an allow rule to the ruleset - individual rules per IP for granular control
        In the INPUT chain, ip is the source address, in the OUTPUT chain it is the destination address"""
        rule_expr = self._chain_matches(family, chain, interface, ip)
        
        # Add protocol and port matches
        rule_expr.extend(self._input_protocol_matches(family, protocol, ports))
        
        # Add connection state match if specified
        if protocol != 'icmp' and state:
            states = [s.strip() for s in state.split(',')]
            rule_expr.append({
                "match": {
                    "op": "==",
                    "left": {"ct": {"key": "state"}},
                    "right": {"set": states} if len(states) > 1 else states[0]
                }
            })
        
        # Add accept action
        rule_expr.append({"accept": None})
        
        # Add the rule to the ruleset
        self.ruleset["nftables"].append({
            "rule": {
                "family": family,
                "table": "filter",
                "chain": chain,
                "expr": rule_expr
            }
        })

    #-----------------------------------------------------------------------------------------------
    #
    #   Generate drop rules
    #
    #-----------------------------------------------------------------------------------------------
    def add_drop_rule(self, family, interface, rule_name, protocol, ports, chain='INPUT'):
        """Add a drop rule to the ruleset using the drop set of the chain, interface and rule"""
        rule_expr = self._chain_matches(family, chain, interface, '@' + self.drop_set_name(interface, rule_name, chain))
        
        # Add protocol and port matches
        rule_expr.extend(self._input_protocol_matches(family, protocol, ports))
        
        # Add drop action
        rule_expr.append({"drop": None})
        
        # Add the rule to the ruleset
        self.ruleset["nftables"].append({
            "rule": {
                "family": family,
                "table": "filter",
                "chain": chain,
                "expr": rule_expr
            }
        })

    #-----------------------------------------------------------------------------------------------
    #
    #   Helper: Build the interface and address matches of an input/output rule
    #   INPUT rules match the input interface and the source address,
    #   OUTPUT rules match the output interface and the destination address
    #
    #-----------------------------------------------------------------------------------------------
    def _chain_matches(self, family, chain, interface, ip):
        """Return the interface and address matches of an INPUT or OUTPUT rule (ip can be a set reference)"""
        if chain == 'OUTPUT':
            interface_key, address_field = 'oifname', 'daddr'
        else:
            interface_key, address_field = 'iifname', 'saddr'

        expr = []

        # Add interface match if not 'any'
        if interface != 'any':
            expr.append({
                "match": {
                    "op": "==",
                    "left": {"meta": {"key": interface_key}},
                    "right": interface
                }
            })

        # Add address match (skip if 'any')
        if ip != 'any':
            expr.append({
                "match": {
                    "op": "==",
                    "left": {"payload": {"protocol": family, "field": address_field}},
                    "right": ip if ip.startswith('@') else self.format_ip_address(ip)
                }
            })

        return expr

    #-----------------------------------------------------------------------------------------------
    #
    #   Add forward rule
    #
    #-----------------------------------------------------------------------------------------------
    def add_forward_rule(self, family: str, expressions: list, action, log_prefix=None):
        """Add a forward rule to the ruleset"""
        
        rule_expr = expressions.copy()
        
        # Add log expression if log_prefix is provided (a trailing space separates it from the logged packet info)
        if log_prefix:
            rule_expr.append({
                "log": {
                    "prefix": log_prefix if log_prefix.endswith(' ') else log_prefix + ' '
                }
            })
            
        # Add action expression
        if isinstance(action, str):
            rule_expr.append({action: None})
        else:
            rule_expr.append(action)
        
        # Add the rule to the ruleset
        self.ruleset["nftables"].append({
            "rule": {
                "family": family,
                "table": "filter",
                "chain": "FORWARD",
                "expr": rule_expr
            }
        })

    #-----------------------------------------------------------------------------------------------
    #
    #   Add NAT rule
    #
    #-----------------------------------------------------------------------------------------------
    def add_nat_rule(self, family: str, chain: str, expressions: list, action):
        """Add a NAT rule to the ruleset"""
        
        rule_expr = expressions.copy()
        
        # Add action expression
        if isinstance(action, str):
            rule_expr.append({action: None})
        else:
            rule_expr.append(action)
        
        # Add the rule to the ruleset
        self.ruleset["nftables"].append({
            "rule": {
                "family": family,
                "table": "nat",
                "chain": chain.upper(),
                "expr": rule_expr
            }
        })

    #-----------------------------------------------------------------------------------------------
    #
    #   Create NAT tables
    #
    #-----------------------------------------------------------------------------------------------
    def create_nat_tables(self):
        """Create IPv4 and IPv6 NAT tables"""
        # IPv4 NAT table
        self.ruleset["nftables"].append({
            "table": {
                "family": "ip",
                "name": "nat"
            }
        })
        
        # IPv6 NAT table
        self.ruleset["nftables"].append({
            "table": {
                "family": "ip6",
                "name": "nat"
            }
        })

    #-----------------------------------------------------------------------------------------------
    #
    #   Create NAT chains
    #
    #-----------------------------------------------------------------------------------------------
    def create_nat_chains(self):
        """Create NAT chains for both IPv4 and IPv6"""
        
        families = ["ip", "ip6"]
        for family in families:
            # PREROUTING chain
            self.ruleset["nftables"].append({
                "chain": {
                    "family": family,
                    "table": "nat",
                    "name": "PREROUTING",
                    "type": "nat",
                    "hook": "prerouting",
                    "prio": -100,
                    "policy": "accept"
                }
            })
            
            # POSTROUTING chain
            self.ruleset["nftables"].append({
                "chain": {
                    "family": family,
                    "table": "nat",
                    "name": "POSTROUTING",
                    "type": "nat",
                    "hook": "postrouting",
                    "prio": 100,
                    "policy": "accept"
                }
            })

    #-----------------------------------------------------------------------------------------------
    #
    #   Build complete ruleset
    #
    #-----------------------------------------------------------------------------------------------
    def build_ruleset(self, config):
        """Build the complete nftables ruleset"""
        self.flush_ruleset()
        self.create_tables()
        self.create_nat_tables()
        self.create_sets()
        self.create_chains(config)
        self.create_nat_chains()
        self.add_base_rules(config)
        
    #-----------------------------------------------------------------------------------------------
    #
    #   Finalize ruleset by adding final drop/log rules
    #
    #-----------------------------------------------------------------------------------------------
    def finalize_ruleset(self):
        """Add final logging and drop rules"""
        self.ruleset["nftables"].extend(self._final_rules)

    #-----------------------------------------------------------------------------------------------
    #
    #   Get current ruleset as JSON
    #
    #-----------------------------------------------------------------------------------------------
    def get_ruleset_json(self):
        """Get the current ruleset as JSON string"""
        return json.dumps(self.ruleset, indent=2)

    #-----------------------------------------------------------------------------------------------
    #
    #   Prepare sets
    #
    #-----------------------------------------------------------------------------------------------
    def prepare_sets(self, content):
        """Prepare sets for nftables configuration - one set per chain+interface+rule_name"""
        for interface in content:
            for ip_version in ['ipv4', 'ipv6']:
                for section, chain in [('input', 'INPUT'), ('output', 'OUTPUT')]:
                    rules = content[interface].get(ip_version, {}).get(section, {})

                    for rule_name, rule in rules.items():
                        if not rule.get('drop'):
                            continue

                        entry = {'chain': chain, 'interface': interface, 'rule_name': rule_name}

                        if entry not in self.sets[ip_version]:
                            self.sets[ip_version].append(entry)
