# coding: utf-8

# Import libraries
import re

class Validate:
    IP_VERSIONS = ['ipv4', 'ipv6']
    SECTIONS = ['input', 'output', 'forward', 'nat']

    # Input/output rules
    PROTOCOLS = ['tcp', 'udp', 'any', 'icmp']
    INPUT_RULE_KEYS = ['protocol', 'ports', 'allow', 'drop']
    # Rule names are used in nftables set names, so only some characters are allowed
    RULE_NAME_REGEX = re.compile(r'^[A-Za-z0-9_.-]+$')

    # Forward rules
    FORWARD_ACTIONS = ['accept', 'drop', 'reject']
    FORWARD_GROUP_KEYS = ['action', 'log', 'log_prefix', 'rules']
    FORWARD_RULE_KEYS = ['from_interface', 'to_interface', 'from_source', 'to_destination', 'protocol', 'from_port', 'to_port']

    # NAT rules
    NAT_RULE_KEYS = {
        'prerouting': ['destination', 'in_interface', 'protocol', 'to_port', 'to_destination'],
        'postrouting': ['source', 'out_interface', 'protocol', 'to_source', 'masquerade'],
    }

    #-----------------------------------------------------------------------------------------------
    #
    #   Validate and normalize the content of a rule file
    #   Raise an exception with a clear message if something is wrong, so that a typo can never
    #   lead to a rule silently ignored or matching more traffic than expected
    #
    #-----------------------------------------------------------------------------------------------
    def validate(self, content, file: str):
        """Validate the structure of a rule file and normalize its values (in place)"""
        self.file = file

        # Non-blocking warnings, printed by the caller once the whole file has been checked
        self.warnings = []

        if not isinstance(content, dict):
            raise Exception(self.file + ': the file must contain a mapping of network interfaces')

        for interface in list(content.keys()):
            if not isinstance(interface, str) or not interface:
                raise Exception(self.file + ': invalid interface name "' + str(interface) + '"')

            # Ignore empty interfaces (e.g. all rules are commented)
            if content[interface] is None:
                del content[interface]
                continue

            self._check_mapping(content[interface], [interface])
            self._check_keys(content[interface], self.IP_VERSIONS, [interface], 'IP version')

            for ip_version in list(content[interface].keys()):
                path = [interface, ip_version]
                ip_data = content[interface][ip_version]

                if ip_data is None:
                    del content[interface][ip_version]
                    continue

                self._check_mapping(ip_data, path)
                self._check_keys(ip_data, self.SECTIONS, path, 'section')

                for section in list(ip_data.keys()):
                    # Ignore empty sections
                    if ip_data[section] is None:
                        del ip_data[section]
                        continue

                    self._check_mapping(ip_data[section], path + [section])

                    if section in ['input', 'output']:
                        self._validate_input_section(ip_data[section], path + [section])

                    if section == 'forward':
                        self._validate_forward_section(ip_data[section], path + [section])

                    if section == 'nat':
                        self._validate_nat_section(ip_data[section], path + [section])

                    if not ip_data[section]:
                        del ip_data[section]

                if not ip_data:
                    del content[interface][ip_version]

            if not content[interface]:
                del content[interface]

        return content

    #-----------------------------------------------------------------------------------------------
    #
    #   Validate input/output rules
    #
    #-----------------------------------------------------------------------------------------------
    def _validate_input_section(self, section: dict, path: list):
        for rule_name in list(section.keys()):
            rule_path = path + [str(rule_name)]
            rule = section[rule_name]

            if not isinstance(rule_name, str) or not self.RULE_NAME_REGEX.match(rule_name):
                raise self._error(rule_path, 'invalid rule name, only letters, digits, "_", "-" and "." are allowed')

            self._check_mapping(rule, rule_path)
            self._check_keys(rule, self.INPUT_RULE_KEYS, rule_path, 'parameter')

            # Protocol (required)
            rule['protocol'] = self._protocol(rule.get('protocol'), self.PROTOCOLS, rule_path, required = True)

            # Ports (no port or 'any' means all ports, ports are ignored for icmp)
            ports = self._ports(rule.get('ports'), rule_path + ['ports'])

            if rule['protocol'] == 'icmp':
                rule['ports'] = []
            elif not ports or 'any' in ports:
                rule['ports'] = ['any']
            else:
                rule['ports'] = ports

            # Allow and drop sources
            for key in ['allow', 'drop']:
                rule[key] = self._sources(rule.get(key), rule_path + [key])

            if 'any' in rule['drop']:
                raise self._error(rule_path + ['drop'], '"any" cannot be used in a drop list')

            # Check that at least 'allow' or 'drop' is present
            if not rule['allow'] and not rule['drop']:
                raise self._error(rule_path, 'must have at least one of "allow" or "drop" (non-empty)')

    #-----------------------------------------------------------------------------------------------
    #
    #   Validate forward rules
    #
    #-----------------------------------------------------------------------------------------------
    def _validate_forward_section(self, section: dict, path: list):
        for rule_name in section:
            group_path = path + [str(rule_name)]
            group = section[rule_name]

            self._check_mapping(group, group_path)
            self._check_keys(group, self.FORWARD_GROUP_KEYS, group_path, 'parameter')

            # Action
            action = group.get('action')
            group['action'] = action.lower() if isinstance(action, str) else 'accept' if action is None else action
            if group['action'] not in self.FORWARD_ACTIONS:
                raise self._error(group_path + ['action'], 'must be one of: ' + ', '.join(self.FORWARD_ACTIONS))

            # Logging
            group['log'] = False if group.get('log') is None else group['log']
            if not isinstance(group['log'], bool):
                raise self._error(group_path + ['log'], 'must be true or false')

            if 'log_prefix' in group:
                if not isinstance(group['log_prefix'], str) or not group['log_prefix'] or len(group['log_prefix']) > 120:
                    raise self._error(group_path + ['log_prefix'], 'must be a non-empty string of 120 characters maximum')

            # Check for required field 'rules'
            rules = group.get('rules')
            if not isinstance(rules, list) or len(rules) == 0:
                raise self._error(group_path + ['rules'], 'missing or empty, it must be a non-empty list')

            # Validate each rule in the list
            for i, rule in enumerate(rules):
                rule_path = group_path + ['rules[' + str(i) + ']']

                self._check_mapping(rule, rule_path)
                self._check_keys(rule, self.FORWARD_RULE_KEYS, rule_path, 'parameter')

                # Each rule must have at least one of from_interface or to_interface
                if not rule.get('from_interface') and not rule.get('to_interface'):
                    raise self._error(rule_path, 'must have at least one of "from_interface" or "to_interface"')

                for key in ['from_interface', 'to_interface', 'from_source', 'to_destination']:
                    self._check_string(rule, key, rule_path)

                rule['protocol'] = self._protocol(rule.get('protocol'), self.PROTOCOLS, rule_path)
                self._normalize_ports(rule, ['from_port', 'to_port'], rule_path)

    #-----------------------------------------------------------------------------------------------
    #
    #   Validate NAT rules
    #
    #-----------------------------------------------------------------------------------------------
    def _validate_nat_section(self, section: dict, path: list):
        for chain in section:
            chain_path = path + [str(chain)]

            if chain not in self.NAT_RULE_KEYS:
                raise self._error(chain_path, 'unknown NAT chain (must be "prerouting" or "postrouting")')

            self._check_mapping(section[chain], chain_path)

            for rule_name in section[chain]:
                rule_path = chain_path + [str(rule_name)]
                rule = section[chain][rule_name]

                self._check_mapping(rule, rule_path)
                self._check_keys(rule, self.NAT_RULE_KEYS[chain], rule_path, 'parameter')

                for key in ['destination', 'in_interface', 'to_destination', 'source', 'out_interface', 'to_source']:
                    self._check_string(rule, key, rule_path)

                # Protocol ('icmp' is not supported in NAT rules)
                rule['protocol'] = self._protocol(rule.get('protocol'), ['tcp', 'udp', 'any'], rule_path)

                if chain == 'prerouting':
                    self._normalize_ports(rule, ['to_port'], rule_path)

                    if not rule.get('to_destination'):
                        raise self._error(rule_path, 'missing required field "to_destination"')

                if chain == 'postrouting':
                    rule['masquerade'] = False if rule.get('masquerade') is None else rule['masquerade']
                    if not isinstance(rule['masquerade'], bool):
                        raise self._error(rule_path + ['masquerade'], 'must be true or false')

                    if not rule['masquerade'] and not rule.get('to_source'):
                        raise self._error(rule_path, 'must have "to_source" or "masquerade: true"')

    #-----------------------------------------------------------------------------------------------
    #
    #   Helpers
    #
    #-----------------------------------------------------------------------------------------------
    def _error(self, path: list, message: str) -> Exception:
        return Exception(self.file + ': ' + '/'.join(str(p) for p in path) + ': ' + message)

    def _check_mapping(self, data, path: list):
        if not isinstance(data, dict):
            raise self._error(path, 'must be a mapping')

    def _check_keys(self, data: dict, allowed: list, path: list, label: str):
        for key in data:
            if key not in allowed:
                raise self._error(path, 'unknown ' + label + ' "' + str(key) + '" (allowed: ' + ', '.join(allowed) + ')')

    def _check_string(self, data: dict, key: str, path: list):
        if key in data and not isinstance(data[key], str):
            raise self._error(path + [key], 'must be a string')

    def _protocol(self, protocol, allowed: list, path: list, required: bool = False) -> str:
        """Return the protocol in lower case ('any' if not specified and not required)"""
        if protocol is None:
            if required:
                raise self._error(path, 'missing required field "protocol"')
            return 'any'

        if not isinstance(protocol, str) or protocol.lower() not in allowed:
            raise self._error(path + ['protocol'], 'invalid protocol "' + str(protocol) + '" (allowed: ' + ', '.join(allowed) + ')')

        return protocol.lower()

    def _ports(self, ports, path: list) -> list:
        """Return a list of ports (int) and/or 'any'"""
        if ports is None:
            return []

        # A single port can be specified without a list
        if not isinstance(ports, list):
            ports = [ports]

        result = []
        for port in ports:
            if isinstance(port, str) and port.lower() == 'any':
                port = 'any'
            elif isinstance(port, int) and not isinstance(port, bool) and 1 <= port <= 65535:
                pass
            elif isinstance(port, str) and port.isdigit() and 1 <= int(port) <= 65535:
                port = int(port)
            else:
                raise self._error(path, 'invalid port "' + str(port) + '" (must be a number between 1 and 65535 or "any")')

            if port not in result:
                result.append(port)

        return result

    def _normalize_ports(self, rule: dict, keys: list, path: list):
        """Normalize forward/NAT ports: a port, a list of ports, or removed if 'any'"""
        for key in keys:
            ports = self._ports(rule.get(key), path + [key])

            if not ports or 'any' in ports:
                rule.pop(key, None)
                continue

            if rule['protocol'] not in ['tcp', 'udp', 'any']:
                raise self._error(path + [key], 'ports can only be used with protocol tcp, udp or any')

            rule[key] = ports if len(ports) > 1 else ports[0]

    def _sources(self, sources, path: list) -> list:
        """Return a list of source names / IP addresses"""
        if sources is None:
            return []

        # A single source can be specified without a list
        if not isinstance(sources, list):
            sources = [sources]

        result = []
        for source in sources:
            if source is None or isinstance(source, (dict, list, bool)) or str(source) == '':
                raise self._error(path, 'invalid source "' + str(source) + '"')

            if str(source) not in result:
                result.append(str(source))

        return result
