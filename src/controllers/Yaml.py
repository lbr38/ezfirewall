# coding: utf-8

# Import libraries
import yaml

# Custom loader that raises an error when a key is defined twice in the same mapping
# By default, PyYAML silently keeps the last value, which would silently discard rules
class UniqueKeyLoader(yaml.SafeLoader):
    def construct_mapping(self, node, deep=False):
        keys = []
        for key_node, _ in node.value:
            key = self.construct_object(key_node, deep=deep)
            if key in keys:
                raise yaml.constructor.ConstructorError(None, None, 'duplicate key "' + str(key) + '"', key_node.start_mark)
            keys.append(key)
        return super().construct_mapping(node, deep)

# Custom class to handle yaml files and keep the order of the keys when writing the file
# Modern version of python3-yaml comes with 'sort_keys=False' option to keep the order of the keys, but
# this is not available on RHEL8 based OS (python3-yaml is too old)
# So this class is a workaround to keep the order of the keys when writing the file

# Yaml inherits from dict
class Yaml():
    #-----------------------------------------------------------------------------------------------
    #
    #   Load data from a yaml file (duplicate keys are rejected)
    #
    #-----------------------------------------------------------------------------------------------
    def load(self, file: str):
        with open(file, 'r') as yaml_file:
            return yaml.load(yaml_file, Loader=UniqueKeyLoader)


    #-----------------------------------------------------------------------------------------------
    #
    #   Write data to a yaml file
    #
    #-----------------------------------------------------------------------------------------------
    def write(self, data, file: str):
        try:
            with open(file, 'w') as yaml_file:
                try:
                    yaml.dump(data, yaml_file, default_flow_style=False, sort_keys=False)

                except TypeError:
                    yaml.dump(data, yaml_file, default_flow_style=False)
        except Exception as e:
            raise Exception(e)
