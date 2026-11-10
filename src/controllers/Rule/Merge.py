from copy import deepcopy

class Merge:
    def __init__(self):
        # File in which each rule has been defined first, used to display explicit errors on conflicts
        self.origins = {}

    #-----------------------------------------------------------------------------------------------
    #
    #   Merge the rules of a file (already validated) into the rules of the previous files
    #
    #-----------------------------------------------------------------------------------------------
    def merge_interfaces(self, base, new, file):
        result = deepcopy(base)

        for interface, iface_data in new.items():
            for ip_version, ip_data in iface_data.items():
                target = result.setdefault(interface, {}).setdefault(ip_version, {})

                for section, section_data in ip_data.items():
                    # NAT rules are organized by chain (prerouting, postrouting), each containing named rules
                    if section == 'nat':
                        for chain, chain_rules in section_data.items():
                            self._merge_section(target.setdefault('nat', {}).setdefault(chain, {}), chain_rules, [interface, ip_version, 'nat', chain], file)
                    else:
                        self._merge_section(target.setdefault(section, {}), section_data, [interface, ip_version, section], file)

        return result

    #-----------------------------------------------------------------------------------------------
    #
    #   Merge the rules of a section
    #
    #-----------------------------------------------------------------------------------------------
    def _merge_section(self, target, rules, path, file):
        section = path[2]

        for rule_name, rule_data in rules.items():
            location = '/'.join(path + [rule_name])

            # New rule, add it
            if rule_name not in target:
                target[rule_name] = deepcopy(rule_data)
                self.origins[location] = file
                continue

            # The rule already exists in a previous file, merge it
            origin = self.origins[location]

            if section in ['input', 'output']:
                target[rule_name] = self._merge_rules(target[rule_name], rule_data, location, origin, file)
            elif section == 'forward':
                target[rule_name] = self._merge_forward_rules(target[rule_name], rule_data, location, origin, file)
            elif target[rule_name] != rule_data:
                # NAT rules cannot be merged
                raise Exception('NAT rule "' + location + '" is defined differently in ' + origin + ' and in ' + file + ', please use a different name for each rule')

    #-----------------------------------------------------------------------------------------------
    #
    #   Merge two input/output rules (only if they use the same protocol)
    #
    #-----------------------------------------------------------------------------------------------
    def _merge_rules(self, base_rule, new_rule, location, origin, file):
        if base_rule['protocol'] != new_rule['protocol']:
            raise Exception('rule "' + location + '" is defined with protocol "' + base_rule['protocol'] + '" in ' + origin + ' and with protocol "' + new_rule['protocol'] + '" in ' + file + ': rules with the same name can only be merged if they use the same protocol, please use a different name for each rule')

        merged_rule = deepcopy(base_rule)

        # Merge 'allow' and 'drop' lists
        for key in ['allow', 'drop']:
            merged_rule[key] = list(dict.fromkeys(base_rule[key] + new_rule[key]))

        # Merge ports ('any' includes all the other ports)
        if 'any' in base_rule['ports'] or 'any' in new_rule['ports']:
            merged_rule['ports'] = ['any']
        else:
            merged_rule['ports'] = sorted(set(base_rule['ports'] + new_rule['ports']))

        return merged_rule

    #-----------------------------------------------------------------------------------------------
    #
    #   Merge two forward rule groups (only if they have the same action and logging)
    #
    #-----------------------------------------------------------------------------------------------
    def _merge_forward_rules(self, base_group, new_group, location, origin, file):
        for key in ['action', 'log', 'log_prefix']:
            if base_group.get(key) != new_group.get(key):
                raise Exception('forward rule "' + location + '" is defined with a different "' + key + '" in ' + origin + ' and in ' + file + ': forward rules with the same name can only be merged if they have the same action and logging parameters')

        merged_group = deepcopy(base_group)

        # Concatenate the rules without duplicates
        for rule in new_group['rules']:
            if rule not in merged_group['rules']:
                merged_group['rules'].append(deepcopy(rule))

        return merged_group
