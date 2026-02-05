# coding: utf-8

# Import libraries
from pathlib import Path
from copy import deepcopy
import yaml
from colorama import Fore, Style

# Import classes
from src.controllers.Yaml import Yaml

class Config:
    # Default configuration values, used both to generate a new configuration
    # file and to repair an existing one that is missing some parameters
    DEFAULTS = {
        'ipv4': {
            'input_default_policy': 'drop',
            'output_default_policy': 'accept',
            'forward_default_policy': 'drop',
            'log_dropped_traffic': False,
        },
        'ipv6': {
            'input_default_policy': 'drop',
            'output_default_policy': 'accept',
            'forward_default_policy': 'drop',
            'log_dropped_traffic': False,
        },
        'log_retention_days': 30,
        'restart_services': [],
    }

    def __init__(self):
        self.yamlController = Yaml()
        self.config = '/opt/ezfirewall/config.yml'

        # If no configuration file exists, generate it
        if not Path(self.config).is_file():
            self.generate()
            # Set permissions
            Path(self.config).chmod(0o644)


    #-----------------------------------------------------------------------------------------------
    #
    #   Generate configuration
    #
    #-----------------------------------------------------------------------------------------------
    def generate(self):
        # Generate configuration using default values
        config = deepcopy(self.DEFAULTS)

        # Write configuration to file
        try:
            self.yamlController.write(config, self.config)
        except Exception as e:
            raise Exception('Failed to generate configuration file: ' + str(e))


    #-----------------------------------------------------------------------------------------------
    #
    #   Repair configuration by adding any missing parameter with its default value
    #
    #-----------------------------------------------------------------------------------------------
    def repair(self, config):
        """Fill in any missing configuration key with its default value.

        Returns a tuple (config, changed) where changed is True if at least
        one parameter was added.
        """
        changed = False

        # If the configuration file is empty or invalid, start from scratch
        if not isinstance(config, dict):
            config = {}
            changed = True

        for key, default_value in self.DEFAULTS.items():
            # Top level parameter is entirely missing (e.g. 'ipv4', 'log_retention_days', ...)
            if key not in config or (isinstance(default_value, dict) and not isinstance(config[key], dict)):
                config[key] = deepcopy(default_value)
                changed = True
                print(Fore.YELLOW + ' ▪ Missing "' + key + '" parameter in configuration file, added with default value' + Style.RESET_ALL)
                continue

            # For sections (ipv4, ipv6), check each sub parameter individually
            if isinstance(default_value, dict):
                for sub_key, sub_default_value in default_value.items():
                    if sub_key not in config[key]:
                        config[key][sub_key] = deepcopy(sub_default_value)
                        changed = True
                        print(Fore.YELLOW + ' ▪ Missing "' + key + '.' + sub_key + '" parameter in configuration file, added with default value "' + str(sub_default_value) + '"' + Style.RESET_ALL)

        return config, changed


    #-----------------------------------------------------------------------------------------------
    #
    #   Validate configuration schema
    #
    #-----------------------------------------------------------------------------------------------
    def validate(self, config):
        # Configuration must be a non-empty mapping
        if not isinstance(config, dict):
            raise Exception('configuration file is empty or invalid')

        valid_policies = ['accept', 'drop']

        # Validate ipv4 and ipv6 sections
        for ip_version in ['ipv4', 'ipv6']:
            if not isinstance(config[ip_version], dict):
                raise Exception('"' + ip_version + '" section must be a mapping')

            # Validate default policies
            for policy_key in ['input_default_policy', 'output_default_policy', 'forward_default_policy']:
                if config[ip_version][policy_key] not in valid_policies:
                    raise Exception('"' + ip_version + '.' + policy_key + '" must be one of: ' + ', '.join(valid_policies))

            # Validate log_dropped_traffic flag
            if not isinstance(config[ip_version]['log_dropped_traffic'], bool):
                raise Exception('"' + ip_version + '.log_dropped_traffic" must be a boolean')

        # Validate log_retention_days
        if not isinstance(config['log_retention_days'], int) or isinstance(config['log_retention_days'], bool) or config['log_retention_days'] < 1:
            raise Exception('"log_retention_days" must be a positive integer')

        # Validate restart_services
        if not isinstance(config['restart_services'], list):
            raise Exception('"restart_services" must be a list')


    #-----------------------------------------------------------------------------------------------
    #
    #   Get configuration
    #
    #-----------------------------------------------------------------------------------------------
    def get(self):
        try:
            # Open configuration file
            with open(self.config, 'r') as file:
                config = yaml.safe_load(file)
        except Exception as e:
            raise Exception('Failed to open configuration file: ' + str(e))

        # Repair the configuration by adding any missing parameter with its default value
        config, changed = self.repair(config)

        # If the configuration was repaired, persist the changes to the file
        if changed:
            try:
                self.yamlController.write(config, self.config)
            except Exception as e:
                raise Exception('Failed to update configuration file: ' + str(e))

        # Validate the configuration schema before returning it
        try:
            self.validate(config)
        except Exception as e:
            raise Exception('Invalid configuration file ' + self.config + ': ' + str(e))

        return config
