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
                'interfaces': [],
                'has_any': False
            },
            'ipv6': {
                'interfaces': [],
                'has_any': False
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
        """Create sets for managing DROP IP addresses only"""
        # Create DROP sets for specific interfaces
        for interface in self.sets['ipv4']['interfaces']:
            if interface != 'any':  # Skip 'any' as we handle it separately
                # Drop list for IPv4
                self.ruleset["nftables"].append({
                    "set": {
                        "family": "ip",
                        "table": "filter",
                        "name": f"ez_{interface}_drop_list",
                        "type": "ipv4_addr",
                        "flags": ["interval"]
                    }
                })

        for interface in self.sets['ipv6']['interfaces']:
            if interface != 'any':  # Skip 'any' as we handle it separately
                # Drop list for IPv6
                self.ruleset["nftables"].append({
                    "set": {
                        "family": "ip6",
                        "table": "filter",
                        "name": f"ez_{interface}_drop_list",
                        "type": "ipv6_addr", 
                        "flags": ["interval"]
                    }
                })

        # Create global DROP sets for 'any' interface if needed
        if self.sets['ipv4']['has_any']:
            # Global drop list for IPv4 (any interface)
            self.ruleset["nftables"].append({
                "set": {
                    "family": "ip",
                    "table": "filter",
                    "name": "ez_any_drop_list",
                    "type": "ipv4_addr",
                    "flags": ["interval"]
                }
            })

        if self.sets['ipv6']['has_any']:
            # Global drop list for IPv6 (any interface)
            self.ruleset["nftables"].append({
                "set": {
                    "family": "ip6",
                    "table": "filter",
                    "name": "ez_any_drop_list",
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
        self._create_forward_chain("ip")
        self._create_output_chain("ip")
        
        # IPv6 chains
        self._create_input_chain("ip6", config['ipv6']['input_default_policy'])
        self._create_forward_chain("ip6")
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
        
    def _create_forward_chain(self, family):
        """Create FORWARD chain for specified family"""
        self.ruleset["nftables"].append({
            "chain": {
                "family": family,
                "table": "filter",
                "name": "FORWARD",
                "type": "filter",
                "hook": "forward",
                "prio": 0,
                "policy": "drop"
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
    def add_to_drop_set(self, family, interface, ip_addresses):
        """Add IP addresses to the drop set for a specific interface"""
        if not ip_addresses:
            return
            
        # Format IP addresses for the set
        formatted_ips = []
        for ip in ip_addresses:
            if ip != "any":
                formatted_ips.append(self.format_ip_address(ip))
        
        if formatted_ips:
            self.ruleset["nftables"].append({
                "element": {
                    "family": family,
                    "table": "filter",
                    "name": f"ez_{interface}_drop_list",
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
    def add_drop_rule(self, family, interface, protocol, ports, use_sets=True):
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
            if interface == 'any':
                # Use global drop set for any interface
                rule_expr.append({
                    "match": {
                        "op": "==",
                        "left": {"payload": {"protocol": family, "field": "saddr"}},
                        "right": "@ez_any_drop_list"
                    }
                })
            elif interface != 'any':
                # Use interface-specific drop set
                rule_expr.append({
                    "match": {
                        "op": "==",
                        "left": {"payload": {"protocol": family, "field": "saddr"}},
                        "right": f"@ez_{interface}_drop_list"
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
    #   Build complete ruleset
    #
    #-----------------------------------------------------------------------------------------------
    def build_ruleset(self, config):
        """Build the complete nftables ruleset"""
        self.flush_ruleset()
        self.create_tables()
        self.create_sets()
        self.create_chains(config)
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
    #   Check ruleset validity
    #
    #-----------------------------------------------------------------------------------------------
    def check(self):
        """Check if the ruleset is valid"""
        try:
            # Test the ruleset without applying it
            rc, output, error = self.nft.cmd(json.dumps(self.ruleset))
            
            if rc != 0:
                raise Exception('invalid nftables ruleset: ' + error)
                
        except Exception as e:
            raise Exception('Error checking ruleset: ' + str(e))

    #-----------------------------------------------------------------------------------------------
    #
    #   Apply ruleset
    #
    #-----------------------------------------------------------------------------------------------
    def apply(self):
        """Apply the ruleset to nftables"""
        try:
            # Apply the ruleset
            rc, output, error = self.nft.cmd(json.dumps(self.ruleset))
            
            if rc != 0:
                raise Exception(error)
                
        except Exception as e:
            raise Exception('Error applying ruleset: ' + str(e))

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
        """Prepare sets for nftables configuration"""
        # In the rules file, loop through every interface to apply their rules
        for interface in content:    
            if "ipv4" in content[interface]:
                if interface == 'any':
                    self.sets['ipv4']['has_any'] = True
                else:
                    self.sets['ipv4']['interfaces'].append(interface)

            if "ipv6" in content[interface]:
                if interface == 'any':
                    self.sets['ipv6']['has_any'] = True
                else:
                    self.sets['ipv6']['interfaces'].append(interface)