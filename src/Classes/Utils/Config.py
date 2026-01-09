import os
import json



class JSONConfig:
    def __init__(self, config_file):
        self.config_file = config_file
        self.config = self._load_config()


    def _load_config(self):
        if not os.path.exists(self.config_file):
            self._create_default_config()
        with open(self.config_file) as file:
            config = json.load(file)
        return config


    def _create_default_config(self):
        default_config = {}
        with open(self.config_file, 'w') as file:
            json.dump(default_config, file, indent=4)


    def get_value(self, guild_id, key_name):
        if str(guild_id) in self.config:
            return self.config[str(guild_id)].get(key_name)
        else:
            return None


    def add_entry(self, guild_id, key_name, value, value_type):
        if not str(guild_id) in self.config:
            self.config[str(guild_id)] = {}

        type_map = {
            "str": str,
            "int": int,
            "float": float,
            "bool": bool,
            "dict": dict,
            "list": list
        }

        if value_type not in type_map:
            raise ValueError("Invalid value type. Supported types are 'str', 'int', 'float', 'bool', and 'dict'.")

        conversion_func = type_map[value_type]
        self.config[str(guild_id)][key_name] = conversion_func(value)
        self._save_config()


    def remove_entry(self, guild_id, key_name):
        if str(guild_id) in self.config:
            if key_name in self.config[str(guild_id)]:
                del self.config[str(guild_id)][key_name]
                self._save_config()


    def _save_config(self):
        with open(self.config_file, 'w') as file:
            json.dump(self.config, file, indent=4)
