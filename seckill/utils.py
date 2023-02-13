import http
import logging
import os
import platform

import requests
import yaml
from selenium import webdriver


def get_useragent(filename: str = "./useragents.txt") -> list:
    root_folder = os.path.dirname(__file__)
    user_agents_file = os.path.join(root_folder, filename)
    with open(user_agents_file, 'r', encoding='utf-8') as reader:
        data = [line.strip() for line in reader.readlines()]
    return data


def get_chrome_path(driver_dir):
    if platform.system() == "Windows":
        return os.path.abspath(os.path.join(driver_dir, "chromedriver.exe"))
    else:
        return os.path.abspath(os.path.join(driver_dir, "chromedriver"))


def build_chrome_options():
    """配置启动项"""
    chromeOptions = webdriver.ChromeOptions()
    chromeOptions.accept_untrusted_certs = True
    chromeOptions.assume_untrusted_cert_issuer = True
    arguments = ['--no-sandbox', '--disable-impl-side-painting', '--disable-setuid-sandbox',
                 '--disable-seccomp-filter-sandbox',
                 '--disable-breakpad', '--disable-client-side-phishing-detection', '--disable-cast',
                 '--disable-cast-streaming-hw-encoding', '--disable-cloud-import', '--disable-popup-blocking',
                 '--ignore-certificate-errors', '--disable-session-crashed-bubble', '--disable-ipv6',
                 '--allow-http-screen-capture', '--start-maximized']
    for arg in arguments:
        chromeOptions.add_argument(arg)
    # chromeOptions.add_argument(f'--user-agent={choice(get_useragent_data())}')
    chromeOptions.add_argument(
        f'--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.0.0 Safari/537.36')
    return chromeOptions


def notify_user(msg: str):
    print(msg)

    token = os.getenv("TOKEN")
    if not token:
        return

    rs = requests.post(url="https://sre24.com/api/v1/push", json=dict(token=token, msg=msg, )).json()
    assert rs["code"] == http.HTTPStatus.ACCEPTED, rs


def build_logger(name, output_dir="./"):
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)
    c_handler = logging.StreamHandler()
    f_handler = logging.FileHandler(os.path.join(output_dir, name + '.log'), 'w', "UTF-8")
    c_handler.setLevel(level=logging.INFO)
    f_handler.setLevel(level=logging.DEBUG)
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    c_handler.setFormatter(formatter)
    f_handler.setFormatter(formatter)
    logger.addHandler(c_handler)
    logger.addHandler(f_handler)
    return logger


def read_yaml(yaml_file):
    with open(yaml_file, encoding='utf-8') as file:
        content = file.read()
        # 设置Loader=yaml.FullLoader忽略YAMLLoadWarning警告
        return yaml.load(content, Loader=yaml.FullLoader)


if __name__ == "__main__":
    print(read_yaml("config.yml"))
