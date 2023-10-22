
from selenium.webdriver.chrome.options import Options
import logging
from logger.logger import setup_logger

logger = setup_logger(__name__, log_level=logging.DEBUG)


class ChromeOptionsBuilder:
    def __init__(self):
        self.chrome_options = Options()


    def configure_chrome_options(self, referer_website_url, news_organisation_name):
        self.chrome_options = Options()
        self.set_chrome_capabilities()
        self.chrome_options.add_argument("--start-maximized")
        self.chrome_options.add_argument("--ignore-certificate-errors")
        self.chrome_options.add_argument("--allow-running-insecure-content")
        self.chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        self.set_user_agent_header()
        self.chrome_options.add_argument(f'referer={referer_website_url}')
        self.add_chrome_extensions(news_organisation_name)
        return self.chrome_options

    def set_chrome_capabilities(self):
        self.chrome_options.set_capability("goog:loggingPrefs", {"performance": "ALL"})
        self.chrome_options.set_capability("goog:perfLoggingPrefs", {"enableNetwork": True})

    def set_user_agent_header(self):
        user_agent = 'user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36'
        self.chrome_options.add_argument(user_agent)

    def add_chrome_extensions(self, news_organisation_name):
        first_extension_path = 'extensions/extension_1_52_2_0.crx'
        second_extension_path = 'extensions/bypass-paywalls-chrome-7029ba34ef83ce638986e1964baa82de88a962da.crx'
        self.chrome_options.add_extension(first_extension_path)
        # Check if the URL belongs to any organization with paywalls
        organization_news_with_pay_wall = ["The New York Times", "The Washington Post"]
        for organization in organization_news_with_pay_wall:
            if organization in news_organisation_name:
                logger.debug(f"organization_news_with_pay_wall, news_organisation_name: {organization}")
                self.chrome_options.add_extension(second_extension_path)
                break  # Add the extension once, if a match is found
