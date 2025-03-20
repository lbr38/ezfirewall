# coding: utf-8

# Import libraries
from copy import deepcopy

class Merge:
    def __init__(self):
        self.additional_rule_counters = {}

    #-----------------------------------------------------------------------------------------------
    #
    #   Merge the 'input' sections of the interfaces
    #
    #-----------------------------------------------------------------------------------------------
    def merge_interfaces(self, base, new):
        result = deepcopy(base)

        for iface_name, iface_data in new.items():
            if iface_name not in result:
                result[iface_name] = iface_data
            else:
                result[iface_name] = self._merge_input_sections(iface_name, result[iface_name], iface_data)

        return result


    #-----------------------------------------------------------------------------------------------
    #
    #   Merge the 'input' sections of the interfaces
    #
    #-----------------------------------------------------------------------------------------------
    def _merge_input_sections(self, iface_name, base_input, new_input):
        base = deepcopy(base_input)
        new = deepcopy(new_input)

        # Initialize a counter for the additional rules of this interface
        if iface_name not in self.additional_rule_counters:
            self.additional_rule_counters[iface_name] = 1

        for rule_name, new_rule_data in new.get("input", {}).items():
            # Find a matching rule in 'base'
            matched = False
            for base_rule_name, base_rule_data in base.get("input", {}).items():
                if self._rules_match(base_rule_data, new_rule_data):
                    # Merge if rules are identical in ports/protocols
                    base["input"][base_rule_name] = self._merge_rules(base_rule_data, new_rule_data)
                    matched = True
                    break

            if not matched:
                # No match: Rename with an "additionalX" suffix
                unique_rule_name = self._make_additional_rule_name(iface_name, rule_name, base.get("input", {}))
                base.setdefault("input", {})[unique_rule_name] = new_rule_data

        return base


    #-----------------------------------------------------------------------------------------------
    #
    #   Check if two rules have the same ports and protocols
    #
    #-----------------------------------------------------------------------------------------------
    def _rules_match(self, rule1, rule2):
        return sorted(rule1.get("port", [])) == sorted(rule2.get("port", [])) and \
               sorted(rule1.get("protocols", [])) == sorted(rule2.get("protocols", []))


    #-----------------------------------------------------------------------------------------------
    #
    #   Merge two rules having the same ports and protocols
    #
    #-----------------------------------------------------------------------------------------------
    def _merge_rules(self, rule1, rule2):
        merged_rule = deepcopy(rule1)

        # Merge and sort allow/drop lists
        for key in ["allow", "drop"]:
            if key in rule1 or key in rule2:
                merged_rule.setdefault(key, [])
                merged_rule[key] = sorted(set(rule1.get(key, []) + rule2.get(key, [])))

        # Sort ports and protocols
        merged_rule["port"] = sorted(set(rule1.get("port", []) + rule2.get("port", [])))
        merged_rule["protocols"] = sorted(set(rule1.get("protocols", []) + rule2.get("protocols", [])))

        return merged_rule


    #-----------------------------------------------------------------------------------------------
    #
    #   Rename a rule by adding a unique 'additionalX' suffix
    #
    #-----------------------------------------------------------------------------------------------
    def _make_additional_rule_name(self, iface_name, rule_name, existing_rules):
        while True:
            unique_name = f"{rule_name}_additional{self.additional_rule_counters[iface_name]}"
            self.additional_rule_counters[iface_name] += 1
            if unique_name not in existing_rules:
                return unique_name
