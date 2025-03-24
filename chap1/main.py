
import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import sys


def selenium_settings(headless_mode:bool=False, headers:dict=dict()) -> object:
    # 셀레니움 설정
    chrome_options = Options()
    chrome_options.add_argument("disable-blink-features=AutomationControlled")  # 자동화 탐지 방지
    chrome_options.add_experimental_option("detach", True)
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--lang=ko")
    chrome_options.add_argument("--window-size=1920, 1080")
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--log-level=3')
    
    # 헤드리스 모드 활성화 및 비활성화 설정
    if headless_mode:
        chrome_options.add_argument("headless")

    # 헤더스 적용
    for k, v in headers.items():
        chrome_options.add_argument(f"{k}={v}")
        
    # dns 적용으로 광고 차단
    local_state = {
        "dns_over_https.mode": "secure",
        "dns_over_https.templates": "https://dns.adguard.com/dns-query",
    }
    chrome_options.add_experimental_option('localState', local_state)

    service = Service(excutable_path=ChromeDriverManager().install()) 
    driver = webdriver.Chrome(service=service, options=chrome_options)
    driver.get('chrome://settings/security')
    driver.implicitly_wait(10)
    driver._unwrap_value

    time.sleep(2)
    
    return driver