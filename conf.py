import yaml
import os


# 获取配置文件的绝对路径
path = os.getcwd()


def read_config():
    with open(os.path.join(path, "conf.yaml")) as yaml_file:
        return yaml.safe_load(yaml_file)


configs = read_config()
