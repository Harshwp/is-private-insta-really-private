import time
import shutil
import os
import random
import sys
import zipfile
import getpass
from selenium.webdriver import ActionChains, Chrome
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import *
from selenium_stealth import stealth




background_js = """
                                    var config = {
                                            mode: "fixed_servers",
                                            rules: {
                                            singleProxy: {
                                                scheme: "http",
                                                host: "%s",
                                                port: parseInt(%s)
                                            },
                                            bypassList: ["localhost"]
                                            }
                                        };

                                    chrome.proxy.settings.set({value: config, scope: "regular"}, function() {});

                                    function callbackFn(details) {
                                        return {
                                            authCredentials: {
                                                username: "%s",
                                                password: "%s"
                                            }
                                        };
                                    }

                                    chrome.webRequest.onAuthRequired.addListener(
                                                callbackFn,
                                                {urls: ["<all_urls>"]},
                                                ['blocking']
                                    );
                                    """

class AdvancedDriver:
    def __init__(self, executable_path=None, proxy=None,
                 waitDelay=15, defaultSleep=(2, 3), user_data_dir=False, legacy=False):
        proxy = None
        try:
            cmd_arg = sys.argv[1]
            if cmd_arg == '-p':
                proxy = 'txt'
            elif cmd_arg == '-ipr':
                proxy = 'iproyal'
                print('Using iproyal proxies.')
        except IndexError as e:
            pass
        self.proxy = proxy

        if not legacy:
            self.create_driver(executable_path, proxy, waitDelay, user_data_dir)
        self.defaultSleep = defaultSleep

    def create_driver(self, executable_path="chromedriver", proxy=None, waitDelay=10, user_data_dir=False):
        options = Options()
        if user_data_dir:
            options.add_argument('user-data-dir=/Users/%s/Library/Application Support/Google/Chrome/' % getpass.getuser())
        options.add_experimental_option('excludeSwitches', ['enable-logging'])
        # options.add_argument('headless')
        options.add_argument("start-maximized")
        options.add_argument('user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 12_0_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.45 Safari/537.36')
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        options.add_argument('--disable-blink-features=AutomationControlled')
        if self.proxy == 'txt':
            with open('proxies.txt') as f:
                oneline = f.readlines()[0][:-1]
                commaCount = oneline.count(',')
                f.seek(0)
                proxies = [x.strip().replace(',', ':') for x in f.readlines()]
                authProxy = commaCount == 3
                if commaCount not in (1, 3):
                    print("Failed to parse proxies.txt, expected 1 or 3 commas, got", commaCount)

            proxy = random.choice(proxies)
            print('Proxy:', proxy)
            if authProxy:
                self.add_auth_proxies(options, *proxy.split(':'))
            else:
                options.add_argument('--proxy-server=' + proxy)
        elif self.proxy == 'iproyal':
            self.add_auth_proxies(options, 'proxy.iproyal.com', '12323', 'Mare', 'mare123_country-de_session-f6sjbyzw_lifetime-5m')

        driver = Chrome(executable_path, options=options)
        stealth(driver,
                languages=["en-US", "en"],
                vendor="Google Inc.",
                platform="Win32",
                webgl_vendor="Intel Inc.",
                renderer="Intel Iris OpenGL Engine",
                fix_hairline=False,
                )
        self.driver = driver
        self.wait = WebDriverWait(driver, waitDelay)
        return driver

    def get_proxy_status(self):
        return self.proxy

    def switch_to_default_content(self):
        self.driver.switch_to.default_content()

    def __getattr__(self, item):
        return getattr(self.driver, item)

    def find_element(self, id=None, xpath=None, class_=None, name=None, selector=None,
                     text=None, sleep=None, jsclick=False):
        sleep = sleep if sleep else self.defaultSleep
        if sleep:
            time.sleep(random.uniform(*sleep))
        if id:
            el = self.wait.until(EC.presence_of_element_located((By.ID, id)))
        elif xpath:
            el = self.wait.until(EC.presence_of_element_located((By.XPATH, xpath)))
        elif class_:
            el = self.wait.until(EC.presence_of_element_located((By.CLASS_NAME, class_)))
        elif name:
            el = self.wait.until(EC.presence_of_element_located((By.NAME, name)))
        elif selector:
            el = self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, selector)))
        elif text:
            el = self.wait.until(EC.presence_of_element_located((By.XPATH, "//*[text()='%s']" % text)))
        else:
            raise Exception('You need to specify a method.')
        if jsclick:
            self.driver.execute_script("arguments[0].click();", el)
        else:
            return el

    def add_auth_proxies(self, options, host, port, username, password):
        pluginfile = 'proxy_auth_plugin.zip'
        with zipfile.ZipFile(pluginfile, 'w') as zp:
            zp.writestr("manifest.json", manifest_json)
            zp.writestr("background.js", background_js % (host, port, username, password))
        options.add_extension(pluginfile)

