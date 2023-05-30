import os
from selenium import webdriver
import chromedriver_autoinstaller


def seleniumWebdriver(headless=True, download_dir=os.getcwd()):
    chromedriver_autoinstaller.install()
    chromeOptions = webdriver.ChromeOptions()
    chromeOptions.add_argument("--disable-notifications")
    chromeOptions.add_argument("--disable-web-security")
    chromeOptions.add_argument("--disable-site-isolation-trials")
    if headless:
        chromeOptions.add_argument("--headless")
    chromeOptions.add_experimental_option("prefs", {"download.default_directory": download_dir})
    driver = webdriver.Chrome(options=chromeOptions)
    return driver
