import json


class ConfigSingleton:
    __instance = None

    @staticmethod
    def getInstance():
        """ Static access method. """
        if ConfigSingleton.__instance == None:
            ConfigSingleton()
        return ConfigSingleton.__instance

    @staticmethod
    def open_files(path):
        CONFIGURATION_FILE = path
        with open(CONFIGURATION_FILE) as config_file:
            return json.load(config_file)

    def __init__(self):
        try:
            self.config = ConfigSingleton.open_files("configuration.json")
        except FileNotFoundError as ex:
            self.config = ConfigSingleton.open_files("..\configuration.json")

        if ConfigSingleton.__instance != None:
            raise Exception("ConfigSingleton EXCEPTION")
        else:
            ConfigSingleton.__instance = self

    def get_config(self):
        return self.config

# maybe needed V V V
# ConfigSingleton.getInstance()
