import json
from PySide6.QtCore import QObject, Signal

class ConnectionModel(QObject):
    """
    Manages loading and accessing SSH connection configurations from a JSON file.
    """
    configurations_loaded = Signal(list)
    error_occurred = Signal(str)

    def __init__(self):
        super().__init__()
        self.configurations = []
        self.config_map = {}
        self.file_path = None

    def load_configurations(self, file_path):
        """
        Loads connection configurations from a JSON file.
        
        The JSON file should be a list of objects, where each object has
        'name', 'hostname', 'port', and 'username' keys.
        """
        self.file_path = file_path
        try:
            with open(self.file_path, 'r') as f:
                # Handle empty file case
                content = f.read()
                if not content:
                    data = []
                else:
                    data = json.loads(content)

            self.configurations = data
            self.config_map = {item['name']: item for item in self.configurations}
            
            config_names = [item['name'] for item in self.configurations]
            self.configurations_loaded.emit(config_names)

        except FileNotFoundError:
            self.error_occurred.emit(f"Error: File not found at '{file_path}'")
        except json.JSONDecodeError:
            self.error_occurred.emit(f"Error: Could not decode JSON from '{file_path}'")
        except KeyError as e:
            self.error_occurred.emit(f"Error: Missing key in configuration file: {e}")
        except Exception as e:
            self.error_occurred.emit(f"An unexpected error occurred: {e}")

    def get_configuration(self, name):
        """
        Returns the configuration details for a given name.
        """
        return self.config_map.get(name)

    def add_configuration(self, config_data):
        """Adds a new configuration and saves it."""
        if config_data['name'] in self.config_map:
            self.error_occurred.emit(f"Error: Configuration with name '{config_data['name']}' already exists.")
            return
        self.configurations.append(config_data)
        self.save_configurations()

    def update_configuration(self, old_name, config_data):
        """Updates an existing configuration and saves it."""
        config_to_update = self.get_configuration(old_name)
        if not config_to_update:
            self.error_occurred.emit(f"Error: Cannot update non-existent configuration '{old_name}'.")
            return
        
        # Update the item in the list
        for i, item in enumerate(self.configurations):
            if item['name'] == old_name:
                self.configurations[i] = config_data
                break
        
        self.save_configurations()

    def delete_configuration(self, name):
        """Deletes a configuration and saves the change."""
        config_to_delete = self.get_configuration(name)
        if not config_to_delete:
            self.error_occurred.emit(f"Error: Cannot delete non-existent configuration '{name}'.")
            return
        
        self.configurations = [item for item in self.configurations if item['name'] != name]
        self.save_configurations()

    def save_configurations(self):
        """Saves the current configurations back to the JSON file."""
        if not self.file_path:
            self.error_occurred.emit("Error: No configuration file loaded to save to.")
            return
        
        try:
            with open(self.file_path, 'w') as f:
                json.dump(self.configurations, f, indent=4)
            
            # Reload to update map and notify view
            self.load_configurations(self.file_path)
        except Exception as e:
            self.error_occurred.emit(f"An error occurred while saving: {e}")
