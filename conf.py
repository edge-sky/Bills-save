import yaml


def read_config():
    with open("conf.yaml") as yaml_file:
        return yaml.safe_load(yaml_file)


configs = read_config()
