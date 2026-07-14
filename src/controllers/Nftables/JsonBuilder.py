# coding: utf-8

# Import libraries
import json
import ipaddress
from colorama import Fore, Style
from nftables import Nftables

class JsonBuilder:
    def __init__(self):
        self.nft = Nftables()
        self.nft.set_json_output(True)
        self.nft.set_handle_output(True)
        
        # Initialize ruleset structure
        self.ruleset = {
            "nftables": []
        }
        
        self.sets = {
            'ipv4': {
                'drop_sets': [],  # list of {'interface': ..., 'rule_name': ...}
                'has_any': False,
                'any_rules': []   # rule names for 'any' interface
            },
            'ipv6': {
                'drop_sets': [],
                'has_any': False,
                'any_rules': []
            }
        }

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
        """Create sets for managing DROP IP addresses per service"""
        # Create DROP sets per interface+rule_name for IPv4
        for drop_set in self.sets['ipv4']['drop_sets']:
            self.ruleset["nftables"].append({
                "set": {
                    "family": "ip",
                    "table": "filter",
                    "name": f"ez_{drop_set['interface']}_{drop_set['rule_name']}_drop",
                    "type": "ipv4_addr",
                    "flags": ["interval"]
                }
            })

        # Create DROP sets per interface+rule_name for IPv6
        for drop_set in self.sets['ipv6']['drop_sets']:
            self.ruleset["nftables"].append({
                "set": {
                    "family": "ip6",
                    "table": "filter",
                    "name": f"ez_{drop_set['interface']}_{drop_set['rule_name']}_drop",
                    "type": "ipv6_addr",
                    "flags": ["interval"]
                }
            })

        # Create global DROP sets for 'any' interface if needed
        for rule_name in self.sets['ipv4']['any_rules']:
            self.ruleset["nftables"].append({
                "set": {
                    "family": "ip",
                    "table": "filter",
                    "name": f"ez_any_{rule_name}_drop",
                    "type": "ipv4_addr",
                    "flags": ["interval"]
                }
            })

        for rule_name in self.sets['ipv6']['any_rules']:
            self.ruleset["nftables"].append({
                "set": {
                    "family": "ip6",
                    "table": "filter",
                    "name": f"ez_any_{rule_name}_drop",
                    "type": "ipv6_addr",
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
        self._create_output_chain("ip")
        
        # IPv6 chains
        self._create_input_chain("ip6", config['ipv6']['input_default_policy'])
        self._create_forward_chain("ip6", config['ipv6']['forward_default_policy'])
        self._create_output_chain("ip6")
        
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
        
    def _create_output_chain(self, family):
        """Create OUTPUT chain for specified family"""
        self.ruleset["nftables"].append({
            "chain": {
                "family": family,
                "table": "filter",
                "name": "OUTPUT",
                "type": "filter",
                "hook": "output",
                "prio": 0,
                "policy": "accept"
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
            # Connection tracking rules - accept established and related
            self.ruleset["nftables"].append({
                "rule": {
                    "family": family,
                    "table": "filter",
                    "chain": "INPUT",
                    "expr": [
                        {
                            "match": {
                                "op": "==",
                                "left": {"ct": {"key": "state"}},
                                "right": {"set": ["established", "related"]}
                            }
                        },
                        {"accept": None}
                    ]
                }
            })

            # Drop invalid packets
            self.ruleset["nftables"].append({
                "rule": {
                    "family": family,
                    "table": "filter",
                    "chain": "INPUT",
                    "expr": [
                        {
                            "match": {
                                "op": "==",
                                "left": {"ct": {"key": "state"}},
                                "right": "invalid"
                            }
                        },
                        {"drop": None}
                    ]
                }
            })

            # Allow loopback
            self.ruleset["nftables"].append({
                "rule": {
                    "family": family,
                    "table": "filter",
                    "chain": "INPUT",
                    "expr": [
                        {
                            "match": {
                                "op": "==",
                                "left": {"meta": {"key": "iifname"}},
                                "right": "lo"
                            }
                        },
                        {"accept": None}
                    ]
                }
            })

            # Connection tracking rules for the FORWARD chain - accept established
            # and related traffic so that the return packets of forwarded
            # connections are not dropped by the default 'drop' policy
            self.ruleset["nftables"].append({
                "rule": {
                    "family": family,
                    "table": "filter",
                    "chain": "FORWARD",
                    "expr": [
                        {
                            "match": {
                                "op": "==",
                                "left": {"ct": {"key": "state"}},
                                "right": {"set": ["established", "related"]}
                            }
                        },
                        {"accept": None}
                    ]
                }
            })

            # Drop invalid packets in the FORWARD chain
            self.ruleset["nftables"].append({
                "rule": {
                    "family": family,
                    "table": "filter",
                    "chain": "FORWARD",
                    "expr": [
                        {
                            "match": {
                                "op": "==",
                                "left": {"ct": {"key": "state"}},
                                "right": "invalid"
                            }
                        },
                        {"drop": None}
                    ]
                }
            })

        # Add final rules for logging and dropping (after all custom rules are added)
        for family in families:    
            # Add logging rule if enabled
            if ((family == "ip" and config['ipv4']['log_dropped_traffic']) or 
                (family == "ip6" and config['ipv6']['log_dropped_traffic'])):
                # Generate correct log prefix based on IP version
                ip_version = "IPv4" if family == "ip" else "IPv6"
                log_prefix = f"[nftables-drop] {ip_version} inbound denied: "
                # Store this for later - will be added at the end
                self._logging_rules = self._logging_rules if hasattr(self, '_logging_rules') else []
                self._logging_rules.append({
                    "rule": {
                        "family": family,
                        "table": "filter", 
                        "chain": "INPUT",
                        "expr": [
                            {
                                "match": {
                                    "op": "==",
                                    "left": {"ct": {"key": "state"}},
                                    "right": "new"
                                }
                            },
                            {
                                "log": {
                                    "prefix": log_prefix
                                }
                            },
                            {"counter": None},
                            {"drop": None}
                        ]
                    }
                })
            else:
                # Drop new connections by default
                # Store this for later - will be added at the end
                self._final_drop_rules = self._final_drop_rules if hasattr(self, '_final_drop_rules') else []
                self._final_drop_rules.append({
                    "rule": {
                        "family": family,
                        "table": "filter",
                        "chain": "INPUT",
                        "expr": [
                            {
                                "match": {
                                    "op": "==",
                                    "left": {"ct": {"key": "state"}},
                                    "right": "new"
                                }
                            },
                            {"drop": None}
                        ]
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
            # CIDR notation - split address and prefix
            addr, prefix_len = ip_address.split('/')
            return {
                "prefix": {
                    "addr": addr,
                    "len": int(prefix_len)
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
    def add_to_drop_set(self, family, interface, rule_name, ip_addresses):
        """Add IP addresses to the drop set for a specific interface and rule"""
        if not ip_addresses:
            return
            
        # Format IP addresses for the set
        formatted_ips = []
        for ip in ip_addresses:
            if ip != "any":
                formatted_ips.append(self.format_ip_address(ip))
        
        set_name = f"ez_{interface}_{rule_name}_drop"
        
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
    #   Generate allow rules
    #
    #-----------------------------------------------------------------------------------------------
    def add_allow_rule(self, family, interface, source_ip, protocol, ports, state="new,related,established"):
        """Add an allow rule to the ruleset - individual rules per IP for granular control"""
        rule_expr = []
        
        # Add interface match if not 'any'
        if interface != 'any':
            rule_expr.append({
                "match": {
                    "op": "==",
                    "left": {"meta": {"key": "iifname"}},
                    "right": interface
                }
            })
        
        # Add source IP match (skip if source is 'any')
        if source_ip != "any":
            rule_expr.append({
                "match": {
                    "op": "==",
                    "left": {"payload": {"protocol": family, "field": "saddr"}},
                    "right": self.format_ip_address(source_ip)
                }
            })
        
        # Add protocol and port matches
        if protocol == 'any' and 'any' not in ports and ports:
            # TCP/UDP with specific ports
            rule_expr.append({
                "match": {
                    "op": "==",
                    "left": {"meta": {"key": "l4proto"}},
                    "right": {"set": ["tcp", "udp"]}
                }
            })
            rule_expr.append({
                "match": {
                    "op": "==",
                    "left": {"payload": {"protocol": "th", "field": "dport"}},
                    "right": {"set": [int(p) for p in ports]}
                }
            })
        elif protocol in ['tcp', 'udp']:
            if ports and 'any' not in ports:
                port_value = [int(p) for p in ports] if len(ports) > 1 else int(ports[0])
                rule_expr.append({
                    "match": {
                        "op": "==",
                        "left": {"payload": {"protocol": protocol, "field": "dport"}},
                        "right": {"set": port_value} if len(ports) > 1 else port_value
                    }
                })
            else:
                rule_expr.append({
                    "match": {
                        "op": "==",
                        "left": {"meta": {"key": "l4proto"}},
                        "right": protocol
                    }
                })
        elif protocol == 'icmp':
            # Handle both ICMPv4 and ICMPv6
            icmp_protocol = "icmp" if family == "ip" else "icmpv6"
            rule_expr.append({
                "match": {
                    "op": "==",
                    "left": {"payload": {"protocol": icmp_protocol, "field": "type"}},
                    "right": "echo-request"
                }
            })
        
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
                "chain": "INPUT",
                "expr": rule_expr
            }
        })

    #-----------------------------------------------------------------------------------------------
    #
    #   Generate drop rules
    #
    #-----------------------------------------------------------------------------------------------
    def add_drop_rule(self, family, interface, rule_name, protocol, ports, use_sets=True):
        """Add a drop rule to the ruleset using sets for IP management"""
        rule_expr = []
        
        # Add interface match if not 'any'
        if interface != 'any':
            rule_expr.append({
                "match": {
                    "op": "==",
                    "left": {"meta": {"key": "iifname"}},
                    "right": interface
                }
            })
        
        # Add source IP match using the appropriate drop set
        if use_sets:
            set_name = f"ez_{interface}_{rule_name}_drop"
            rule_expr.append({
                "match": {
                    "op": "==",
                    "left": {"payload": {"protocol": family, "field": "saddr"}},
                    "right": f"@{set_name}"
                }
            })
        
        # Add protocol and port matches
        if protocol == 'any' and 'any' not in ports and ports:
            # TCP/UDP with specific ports
            rule_expr.append({
                "match": {
                    "op": "==",
                    "left": {"meta": {"key": "l4proto"}},
                    "right": {"set": ["tcp", "udp"]}
                }
            })
            rule_expr.append({
                "match": {
                    "op": "==",
                    "left": {"payload": {"protocol": "th", "field": "dport"}},
                    "right": {"set": [int(p) for p in ports]}
                }
            })
        elif protocol in ['tcp', 'udp']:
            if ports and 'any' not in ports:
                port_value = [int(p) for p in ports] if len(ports) > 1 else int(ports[0])
                rule_expr.append({
                    "match": {
                        "op": "==",
                        "left": {"payload": {"protocol": protocol, "field": "dport"}},
                        "right": {"set": port_value} if len(ports) > 1 else port_value
                    }
                })
            else:
                rule_expr.append({
                    "match": {
                        "op": "==",
                        "left": {"meta": {"key": "l4proto"}},
                        "right": protocol
                    }
                })
        elif protocol == 'icmp':
            # Handle both ICMPv4 and ICMPv6
            icmp_protocol = "icmp" if family == "ip" else "icmpv6"
            rule_expr.append({
                "match": {
                    "op": "==",
                    "left": {"payload": {"protocol": icmp_protocol, "field": "type"}},
                    "right": "echo-request"
                }
            })
        
        # Add drop action
        rule_expr.append({"drop": None})
        
        # Add the rule to the ruleset
        self.ruleset["nftables"].append({
            "rule": {
                "family": family,
                "table": "filter",
                "chain": "INPUT",
                "expr": rule_expr
            }
        })

    #-----------------------------------------------------------------------------------------------
    #
    #   Add forward rule
    #
    #-----------------------------------------------------------------------------------------------
    def add_forward_rule(self, family: str, expressions: list, action, log_prefix=None):
        """Add a forward rule to the ruleset"""
        
        rule_expr = expressions.copy()
        
        # Add log expression if log_prefix is provided
        if log_prefix:
            rule_expr.append({
                "log": {
                    "prefix": log_prefix
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
        # Add logging rules if they exist
        if hasattr(self, '_logging_rules'):
            self.ruleset["nftables"].extend(self._logging_rules)
            
        # Add final drop rules if they exist
        if hasattr(self, '_final_drop_rules'):
            self.ruleset["nftables"].extend(self._final_drop_rules)

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
        """Prepare sets for nftables configuration - one set per interface+rule_name"""
        for interface in content:
            for ip_version_key, family_key in [("ipv4", "ipv4"), ("ipv6", "ipv6")]:
                if ip_version_key not in content[interface]:
                    continue
                if 'input' not in content[interface][ip_version_key]:
                    continue
                for rule_name in content[interface][ip_version_key]['input']:
                    if 'drop' not in content[interface][ip_version_key]['input'][rule_name]:
                        continue
                    if interface == 'any':
                        self.sets[family_key]['has_any'] = True
                        if rule_name not in self.sets[family_key]['any_rules']:
                            self.sets[family_key]['any_rules'].append(rule_name)
                    else:
                        entry = {'interface': interface, 'rule_name': rule_name}
                        if entry not in self.sets[family_key]['drop_sets']:
                            self.sets[family_key]['drop_sets'].append(entry)