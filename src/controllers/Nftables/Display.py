# coding: utf-8

# Import libraries
import json
import ipaddress
from colorama import Fore, Style
from tabulate import tabulate

# Import classes
from src.controllers.Source import Source

class Display:
    FAMILIES = {
        'ip': 'IPv4',
        'ip6': 'IPv6',
        'inet': 'IPv4 + IPv6',
        'arp': 'ARP',
        'bridge': 'bridge',
        'netdev': 'netdev'
    }

    HEADER = ['#', 'Interface (in → out)', 'Source', 'Destination', 'Protocol', 'Port(s) (src → dst)', 'State', 'Action']

    def __init__(self):
        # IP address => source name, used to display the source names next to the IP addresses
        self.source_names = {}

        try:
            for name, ip in Source().load().items():
                self.source_names[self._normalize_ip(ip)] = name
        except Exception:
            # Source names are only informative, ignore invalid source files here
            pass

    #-----------------------------------------------------------------------------------------------
    #
    #   Print a ruleset (JSON output of 'list ruleset') as tables, one table per nftables table
    #
    #-----------------------------------------------------------------------------------------------
    def print_ruleset(self, ruleset: list):
        tables = []
        chains = {}
        rules = {}

        # Sets elements, used to display the content of the sets used by the rules
        self.sets = {}

        for item in ruleset:
            if 'table' in item:
                tables.append((item['table']['family'], item['table']['name']))
            elif 'chain' in item:
                chains.setdefault((item['chain']['family'], item['chain']['table']), []).append(item['chain'])
            elif 'rule' in item:
                rule = item['rule']
                rules.setdefault((rule['family'], rule['table'], rule['chain']), []).append(rule)
            elif 'set' in item:
                set_data = item['set']
                self.sets[(set_data['family'], set_data['table'], set_data['name'])] = set_data.get('elem', [])

        if not tables:
            print(' ▪ No rules are currently in place')
            return

        print(' ▪ Rules currently in place:')

        for family, table_name in tables:
            print('\n ' + Style.BRIGHT + 'Table ' + Fore.GREEN + family + ' ' + table_name + Style.RESET_ALL + ' (' + self.FAMILIES.get(family, family) + ')')

            table_chains = chains.get((family, table_name), [])

            if not table_chains:
                print('   No chain')

            for chain in table_chains:
                # Chain title
                if 'hook' in chain:
                    policy = chain.get('policy', 'accept')
                    policy_formatted = (Fore.GREEN if policy == 'accept' else Fore.YELLOW) + policy + Style.RESET_ALL
                    print('\n   Chain ' + Style.BRIGHT + chain['name'] + Style.RESET_ALL + ' (hook ' + chain['hook'] + ', policy ' + policy_formatted + ')')
                else:
                    print('\n   Chain ' + Style.BRIGHT + chain['name'] + Style.RESET_ALL + ' (regular chain)')

                chain_rules = rules.get((family, table_name, chain['name']), [])

                if not chain_rules:
                    print('   No rule')
                    continue

                table = [[i] + self._rule_columns(rule) for i, rule in enumerate(chain_rules, 1)]
                print(tabulate(table, headers = [Style.BRIGHT + h + Style.RESET_ALL for h in self.HEADER], tablefmt = 'fancy_grid'), end = '\n')

    #-----------------------------------------------------------------------------------------------
    #
    #   Convert a rule to table columns
    #
    #-----------------------------------------------------------------------------------------------
    def _rule_columns(self, rule: dict) -> list:
        in_interface = ''
        out_interface = ''
        source = ''
        destination = ''
        protocol = ''
        sport = ''
        dport = ''
        state = ''
        action = ''
        notes = []
        others = []

        for expr in rule.get('expr', []):
            key = list(expr)[0]
            value = expr[key]

            if key == 'match':
                left = value.get('left', {})
                right = value.get('right')
                negation = 'not ' if value.get('op') == '!=' else ''

                if 'meta' in left and left['meta'].get('key') in ['iifname', 'oifname', 'l4proto']:
                    formatted = negation + self._format_value(right)
                    if left['meta']['key'] == 'iifname':
                        in_interface = formatted
                    elif left['meta']['key'] == 'oifname':
                        out_interface = formatted
                    else:
                        protocol = formatted

                elif 'payload' in left and left['payload'].get('field') in ['saddr', 'daddr']:
                    formatted = negation + self._format_addresses(right, rule)
                    if left['payload']['field'] == 'saddr':
                        source = formatted
                    else:
                        destination = formatted

                elif 'payload' in left and left['payload'].get('field') in ['sport', 'dport']:
                    formatted = negation + self._format_value(right)
                    if left['payload']['field'] == 'sport':
                        sport = formatted
                    else:
                        dport = formatted

                    # 'th' matches both tcp and udp, the protocol is then specified by a l4proto match
                    if left['payload'].get('protocol') in ['tcp', 'udp'] and not protocol:
                        protocol = left['payload']['protocol']

                elif 'payload' in left and left['payload'].get('protocol') in ['icmp', 'icmpv6'] and left['payload'].get('field') == 'type':
                    protocol = left['payload']['protocol'] + '\n' + negation + self._format_value(right, '\n')

                elif 'payload' in left and left['payload'].get('field') in ['protocol', 'nexthdr']:
                    protocol = negation + self._format_value(right)

                elif 'ct' in left and left['ct'].get('key') == 'state':
                    state = negation + self._format_value(right)

                else:
                    others.append(self._format_json(expr))

            # Verdicts
            elif key in ['accept', 'drop', 'reject', 'return', 'continue', 'queue']:
                action = key
            elif key in ['jump', 'goto']:
                action = key + ' ' + value.get('target', '')

            # NAT statements
            elif key in ['masquerade', 'redirect']:
                action = key
            elif key in ['snat', 'dnat']:
                action = key + ' to ' + self._format_addresses(value.get('addr', ''), rule)
                if 'port' in value:
                    action += ':' + self._format_value(value['port'])

            # Other statements
            elif key == 'log':
                notes.append('log' + (' "' + value['prefix'].strip() + '"' if isinstance(value, dict) and value.get('prefix') else ''))
            elif key == 'counter':
                if isinstance(value, dict) and 'packets' in value:
                    notes.append(str(value['packets']) + ' packets')
            elif key == 'xt':
                # xtables compat expression (created by iptables-nft, e.g. by docker)
                if value.get('type') == 'target':
                    action = value.get('name', '') + ' (iptables-nft)'
                else:
                    others.append('iptables-nft ' + value.get('type', '') + ' ' + value.get('name', ''))
            else:
                others.append(self._format_json(expr))

        # Format action for table display
        if action:
            action_formatted = (Fore.GREEN if action == 'accept' else Fore.YELLOW if action in ['drop', 'reject'] else '') + action + Style.RESET_ALL
        else:
            action_formatted = ''

        if notes:
            action_formatted += '\n(' + ', '.join(notes) + ')'

        if others:
            action_formatted += '\n' + Fore.CYAN + '\n'.join(others) + Style.RESET_ALL

        # Interfaces column
        if in_interface or out_interface:
            interfaces = (in_interface or 'any') + (' → ' + (out_interface or 'any') if out_interface else '')
        else:
            interfaces = ''

        # Ports column
        if sport or dport:
            ports = (sport or 'any') + ' → ' + (dport or 'any')
        else:
            ports = ''

        return [interfaces, source, destination, protocol, ports, state, action_formatted]

    #-----------------------------------------------------------------------------------------------
    #
    #   Helpers
    #
    #-----------------------------------------------------------------------------------------------
    def _format_value(self, value, separator: str = ', ') -> str:
        """Format a match value (string, number, set, prefix, range...)"""
        if isinstance(value, (str, int)):
            return str(value)
        if isinstance(value, list):
            return separator.join(self._format_value(v) for v in value)
        if isinstance(value, dict):
            if 'set' in value:
                return self._format_value(value['set'], separator)
            if 'prefix' in value:
                return str(value['prefix'].get('addr')) + '/' + str(value['prefix'].get('len'))
            if 'range' in value:
                return '-'.join(self._format_value(v) for v in value['range'])
        return self._format_json(value)

    def _format_addresses(self, value, rule: dict) -> str:
        """Format addresses, one per line, with the name of the source if any (sets are replaced by their content)"""
        # Named set (e.g. ezfirewall drop sets): display its elements
        if isinstance(value, str) and value.startswith('@'):
            elements = self.sets.get((rule['family'], rule['table'], value[1:]))
            if not elements:
                return value
            value = elements

        if isinstance(value, dict) and 'set' in value:
            value = value['set']

        if not isinstance(value, list):
            value = [value]

        addresses = []
        for address in value:
            formatted = self._format_value(address)
            name = self.source_names.get(self._normalize_ip(formatted))
            addresses.append(formatted + (' (' + name + ')' if name else ''))

        return '\n'.join(addresses)

    def _normalize_ip(self, ip: str) -> str:
        """Normalize an IP address or network so that it can be compared (e.g. 9.9.9.9/32 => 9.9.9.9)"""
        try:
            network = ipaddress.ip_network(ip, strict=False)
        except ValueError:
            return ip

        if network.prefixlen == network.max_prefixlen:
            return str(network.network_address)

        return str(network)

    def _format_json(self, value) -> str:
        return json.dumps(value, separators=(',', ':'))
