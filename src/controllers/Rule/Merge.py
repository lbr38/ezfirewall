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

            if not base_ip_data and not new_ip_data:
                continue

            merged_ip = {}

            # Fusionner les sections 'input' et 'output' (fusion au niveau des listes allow/drop/ports)
            for section in ["input", "output"]:
                base_section = base_ip_data.get(section, {})
                new_section = new_ip_data.get(section, {})
                if base_section or new_section:
                    merged_ip[section] = self._merge_input_sections(base_section, new_section)

            # Fusionner la section 'forward'
            base_forward = base_ip_data.get("forward", {})
            new_forward = new_ip_data.get("forward", {})
            if base_forward or new_forward:
                merged_ip["forward"] = self._merge_forward_sections(base_forward, new_forward)

            # Fusionner la section 'nat'
            base_nat = base_ip_data.get("nat", {})
            new_nat = new_ip_data.get("nat", {})
            if base_nat or new_nat:
                merged_ip["nat"] = self._merge_nat_sections(base_nat, new_nat)

            merged_iface[ip_version] = merged_ip

        return merged_iface

    #-----------------------------------------------------------------------------------------------
    #
    #   Merge the 'forward' sections of the interfaces
    #
    #-----------------------------------------------------------------------------------------------
    def _merge_forward_sections(self, base_forward, new_forward):
        merged_forward = deepcopy(base_forward)

        for rule_name, new_rule_data in new_forward.items():
            if rule_name in merged_forward:
                # Si le groupe de règles existe déjà, on concatène les règles sans dupliquer
                # (les clés scalaires action/log/log_prefix du premier fichier sont conservées)
                base_rules = merged_forward[rule_name].setdefault('rules', [])
                for rule in new_rule_data.get('rules', []):
                    if rule not in base_rules:
                        base_rules.append(rule)
            else:
                # Sinon, on ajoute le nouveau groupe de règles
                merged_forward[rule_name] = deepcopy(new_rule_data)

        return merged_forward

    #-----------------------------------------------------------------------------------------------
    #
    #   Merge the 'nat' sections of the interfaces
    #
    #-----------------------------------------------------------------------------------------------
    def _merge_nat_sections(self, base_nat, new_nat):
        merged_nat = deepcopy(base_nat)

        # NAT is organized by chain (prerouting, postrouting), each containing named rules
        for chain, new_rules in new_nat.items():
            if chain not in merged_nat:
                merged_nat[chain] = deepcopy(new_rules)
            else:
                for rule_name, rule_config in new_rules.items():
                    # First file wins if the same rule name is defined twice
                    if rule_name not in merged_nat[chain]:
                        merged_nat[chain][rule_name] = deepcopy(rule_config)

        return merged_nat

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