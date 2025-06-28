# src/services/config_service.py
import configparser
import logging

class ConfigService:
    """负责所有 config.ini 文件的读写逻辑"""
    def __init__(self, filepath):
        self.filepath = filepath
        self.config = configparser.ConfigParser()
        self.load_config()

    def load_config(self):
        try:
            self.config.read(self.filepath, encoding='utf-8-sig')
            logging.info(f"成功加载配置文件: {self.filepath}")
        except Exception as e:
            logging.error(f"加载配置文件失败: {e}")
            self.config = configparser.ConfigParser()

    def get_sections(self):
        return self.config.sections()

    def get_options(self, section):
        return self.config.items(section)

    def set_option(self, section, option, value):
        if not self.config.has_section(section):
            self.config.add_section(section)
        self.config.set(section, option, value)

    def save_config(self):
        try:
            with open(self.filepath, 'w', encoding='utf-8') as configfile:
                self.config.write(configfile)
            logging.info(f"配置文件已成功保存到: {self.filepath}")
            return True
        except Exception as e:
            logging.error(f"保存配置文件失败: {e}")
            return False