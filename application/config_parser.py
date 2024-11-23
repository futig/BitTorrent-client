import configparser

CONFIG = "config.ini"

def get_downloader_config():
    configuration = configparser.ConfigParser()
    configuration.read(CONFIG)
    return configuration["CLIENT"]

def get_distributer_config():
    configuration = configparser.ConfigParser()
    configuration.read(CONFIG)
    return configuration["SERVER"]