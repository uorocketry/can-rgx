import configparser

config = configparser.ConfigParser()
config.read('config.ini')


def get_config(location):
    return config[location]


def update_config():
    default = dict()
    default['DEFAULT'] = {'rpi_port': '65432'}
    default['rpi'] = {
        'rpi_listening_ip': '127.0.0.1',
        'laptop_ip': '127.0.0.1'}

    default['laptop'] = {
        'laptop_listening_ip': '127.0.0.1',
        'rpi_ip': '127.0.0.1'}

    for section, keys in default.items():  # Make sure the config has at least all the keys. If not, init to default
        modified = False
        if section not in config:
            config[section] = {}
            modified = True

        for key, value in keys.items():
            if key not in config[section]:
                config[section][key] = value
                modified = True

    if modified:
        with open('config.ini', 'w') as file:
            config.write(file)


update_config()
