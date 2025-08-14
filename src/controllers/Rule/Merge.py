from copy import deepcopy

class Merge:
    #-----------------------------------------------------------------------------------------------
    #
    #   Merge the 'input' sections of the interfaces
    #
    #-----------------------------------------------------------------------------------------------
    def merge_interfaces(self, base, new):
        result = deepcopy(base)

        for iface_name, iface_data in new.items():
            if iface_name not in result:
                # Si l'interface n'existe pas encore, on l'ajoute directement
                result[iface_name] = iface_data
            else:
                # Fusionner les données IPv4 et IPv6 dans la même interface
                result[iface_name] = self._merge_ip_versions(result[iface_name], iface_data)

        return result

    #-----------------------------------------------------------------------------------------------
    #
    #   Merge IPv4 and IPv6 data for the same interface
    #
    #-----------------------------------------------------------------------------------------------
    def _merge_ip_versions(self, base_iface, new_iface):
        merged_iface = deepcopy(base_iface)

        # Fusionner les sections ipv4 et ipv6
        for ip_version in ["ipv4", "ipv6"]:
            base_ip_data = base_iface.get(ip_version, {})
            new_ip_data = new_iface.get(ip_version, {})

            if base_ip_data or new_ip_data:
                merged_iface[ip_version] = {
                    "input": self._merge_input_sections(base_ip_data.get("input", {}),
                                                        new_ip_data.get("input", {})),
                    "output": self._merge_input_sections(base_ip_data.get("output", {}),
                                                        new_ip_data.get("output", {}))
                }

        return merged_iface

    #-----------------------------------------------------------------------------------------------
    #
    #   Merge the 'input' sections of the interfaces
    #
    #-----------------------------------------------------------------------------------------------
    def _merge_input_sections(self, base_input, new_input):
        merged_input = deepcopy(base_input)

        for rule_name, new_rule_data in new_input.items():
            if rule_name in merged_input:
                # Si la règle existe déjà, on fusionne les données
                merged_input[rule_name] = self._merge_rules(merged_input[rule_name], new_rule_data)
            else:
                # Sinon, on ajoute la nouvelle règle
                merged_input[rule_name] = new_rule_data

        return merged_input

    #-----------------------------------------------------------------------------------------------
    #
    #   Merge two rules
    #
    #-----------------------------------------------------------------------------------------------
    def _merge_rules(self, base_rule, new_rule):
        merged_rule = deepcopy(base_rule)

        # Fusionner les listes 'allow' et 'drop'
        for key in ["allow", "drop"]:
            if key in new_rule:
                merged_rule.setdefault(key, [])
                merged_rule[key] = sorted(set(merged_rule[key] + new_rule[key]))

        # Fusionner les ports
        if "ports" in new_rule:
            merged_rule.setdefault("ports", [])
            merged_rule["ports"] = sorted(set(merged_rule["ports"] + new_rule["ports"]))

        return merged_rule