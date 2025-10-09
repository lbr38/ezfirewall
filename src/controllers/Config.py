# coding: utf-8

# Import libraries
from pathlib import Path
import yaml

# Import classes
from src.controllers.Yaml import Yaml

class Config:
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
        # Generate configuration
        config = {
            'ipv4': {
                'input_default_policy': 'drop',
                'output_default_policy': 'accept',
                'log_dropped_traffic': False,
            },
            'ipv6': {
                'input_default_policy': 'drop',
                'output_default_policy': 'accept',
                'log_dropped_traffic': False,
            },
            'log_retention_days': 30,
            'restart_services': [],
        }

        # Write configuration to file
        try:
            self.yamlController.write(config, self.config)
        except Exception as e:
            raise Exception('Failed to generate configuration file: ' + str(e))


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

        return config
