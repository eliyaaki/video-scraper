
import os
import json
from selenium import webdriver
from selenium.common.exceptions import ElementClickInterceptedException
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
import time
import logging
from logger.logger import setup_logger

# Initialize the logger without needing to know the configuration details
from service.chrome_option_builder import ChromeOptionsBuilder
from service.video_download_service import VideoDownloadService

logger = setup_logger(__name__, log_level=logging.DEBUG)

DEFAULT_URL = "https://www.mako.co.il/news-military/6361323ddea5a810/Article-93bd6261a6f3b81027.htm?sCh=31750a2610f26110&pId=173113802"

DEFAULT_REMOTE_WEB_DRIVER = "http://selenium:4444/wd/hub"
DEFAULT_MAX_VIDEO_DOWNLOAD_RETRIES = 3
DEFAULT_MAX_DRIVER_RETRIES = 3
DEFAULT_ELEMENT_IDENTIFIER = "click_container"



class VideoScraperService:

    def __init__(self):
        self.driver = None
        self.news_organisation_name = "The New York Times"
        self.referer_website_url = "https://13tv.co.il/"
        self.video_download_service = VideoDownloadService()
        self.chrome_options_builder = ChromeOptionsBuilder()
        self.max_driver_retries = int(os.environ.get("MAX_DRIVER_RETRIES", DEFAULT_MAX_DRIVER_RETRIES))
        self.remote_web_driver = os.environ.get("REMOTE_WEB_DRIVER", DEFAULT_REMOTE_WEB_DRIVER)
        self.element_identifier = os.environ.get("ELEMENT_IDENTIFIER", DEFAULT_ELEMENT_IDENTIFIER)
        self.news_organizations = [
            {
                "name": "Daily Mail",
                "url": "https://www.dailymail.co.uk/",
            },
            {
                "name": "Reuters",
                "url": "https://www.reuters.com/",
                "m3u8_name": "master.m3u8",
                # "element_identifier": "",
            },
            {
                "name": "AP News",
                "url": "https://apnews.com/",
                # "m3u8_name": "any",
                # "element_identifier": "",
            },
            {
                "name": "The New York Times",
                "url": "https://www.nytimes.com/",
                "m3u8_name": "playlist.m3u8",
                "element_identifier": "playIconDefaults-r78KaMXm",
            },
            {
                "name": "The Washington Post",
                "url": "https://www.washingtonpost.com/",
                "m3u8_name": "playlist.m3u8",
                "element_identifier": "overlay-2cwpQscP",
            },
            {
                "name": "CNN",
                "url": "https://edition.cnn.com/",
                "m3u8_name": "proxy.1.m3u8",
                # "m3u8_name": "master_cl_de.m3u8",
                "element_identifier": "pui_center-controls_big-play-toggle",
            },
            {
                "name": "Fox News",
                "url": "https://www.foxnews.com/",
                "m3u8_name": "rendition.m3u8",
                "element_identifier": "video-container",
            },
            {
                "name": "MSNBC",
                "url": "https://www.msnbc.com/",
                "m3u8_name": "index.m3u8",
                "element_identifier": "videoPlayer ",
            },
            {
                "name": "NBC News",
                "url": "https://www.nbcnews.com/",
                "m3u8_name": "index.m3u8",
                "element_identifier": "videoPlayer ",
                # "element_identifier": "videoSlate",
            },
            {
                "name": "CBS",
                "url": "https://www.cbsnews.com/",
                "m3u8_name": "master.m3u8",
                # "element_identifier": "some_cbs_identifier",
            },
            {
                "name": "Al Jazeera",
                "url": "https://www.aljazeera.com/",
                "m3u8_name": "master.m3u8",
                "element_identifier": "in-page-video",
            },
            {
                "name": "Ynet",
                "url": "https://www.ynet.co.il/",
                "m3u8_name": "master.m3u8",
                # "element_identifier": "fp-play",
                "element_identifier": "VideoComponenta",
            },
            {
                "name": "Mako",
                "url": "https://www.mako.co.il/",
                "m3u8_name": "master.m3u8",
                "element_identifier": "click_container",
            },
            {
                "name": "Channel 12",
                "url": "https://www.12tv.co.il/",
                "m3u8_name": "playlist.m3u8",
                "element_identifier": "click_container",
            },
            {
                "name": "KAN",
                "url": "https://www.kan.org.il/",
                "m3u8_name": "a.m3u8",
                "element_identifier": "playkit-pre-playback-play-button",
                # "element_identifier": "playkit-overlay-action ",
            },
            {
                "name": "Channel 13",
                "url": "https://13tv.co.il/",
                "m3u8_name": "a.m3u8",
                "element_identifier": "kaltura-player-container",
            },
            # Add more news organizations and their data as needed
        ]

    def initialize_driver(self, url, max_scroll_attempts):
        self.set_oranization_name_and_identifier(url)

        return self.init_driver_connection_with_retry(self.chrome_options_builder.configure_chrome_options(self.referer_website_url, self.news_organisation_name), url, max_scroll_attempts)

    def init_driver_connection_with_retry(self, chrome_options, url, max_scroll_attempts):
        retries = 0
        while retries < self.max_driver_retries:
            try:
                with webdriver.Remote(command_executor=self.remote_web_driver, options=chrome_options) as driver:
                    self.driver = driver
                    return self.scrape_website(url, max_scroll_attempts)
                logger.debug("WebDriver initialized successfully")
            except Exception as e:
                logger.debug(f"An error occurred while initializing the WebDriver: {e}")
                logger.debug(f"Retrying ({retries + 1}/{self.max_driver_retries})...")
                retries += 1
        else:
            logger.debug("Max driver initialization retries reached. Exiting.")



    def scroll_down_page(self, max_scroll_attempts=None):
        if max_scroll_attempts is None:
            max_scroll_attempts = 10
        page_height = self.driver.execute_script("return document.body.scrollHeight")

        scroll_attempts = 0
        while scroll_attempts < max_scroll_attempts:
            # Scroll down the page
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")

            # Wait for a short period to allow content to load, adjust as needed
            time.sleep(3)

            # Get the updated page height
            new_page_height = self.driver.execute_script("return document.body.scrollHeight")

            # Check if the page height has changed; if not, you've likely reached the end of the page
            if new_page_height == page_height:
                break

            # Update the page height and increment scroll attempts
            page_height = new_page_height
            scroll_attempts += 1

    def scrape_website(self, url, max_scroll_attempts=None):
        logger.debug(f"scrape_website with url: {url}")
        # self.initialize_driver()
        time.sleep(3)
        self.driver.get(url)
        self.scroll_down_page(max_scroll_attempts)
        # time.sleep(3)  # Adjust this as needed to allow the page to load
        self.wait_for_elements_and_click(self.element_identifier)
        logger.debug(f"wait_for_elements_and_click happened for: {url}")
        page_source = self.driver.page_source
        m3u8_urls = self.capture_m3u8_urls_from_log()
        video_urls_after_save = self.video_download_service.process_page(url, self.news_organizations, page_source, m3u8_urls)
        return video_urls_after_save


    def set_oranization_name_and_identifier(self, url):
        # Check the base URL to determine the news organization
        exist_in_news_organization = False
        for org_data in self.news_organizations:
            news_organisation_url = org_data["url"]
            news_organisation_name = org_data["name"]
            logger.debug(f"org_data: {news_organisation_name} : {news_organisation_url}")
            if url.startswith(org_data["url"]):
                self.referer_website_url = news_organisation_url
                self.news_organisation_name = news_organisation_name
                exist_in_news_organization = True
                self.element_identifier = org_data.get("element_identifier", None)
                break  # Exit the loop if a match is found

        if not exist_in_news_organization:
            logger.error(f"url dost exists in news_organizations list")


    def wait_for_elements_and_click(self, element_identifier, timeout=30):

        if element_identifier:
            click_containers = []

            try:

                # Try to locate elements by ID or class
                id_condition = EC.presence_of_all_elements_located(
                    (By.CSS_SELECTOR, f'[id="{element_identifier}"], .{element_identifier}'))
                # id_condition = EC.presence_of_all_elements_located(By.CSS_SELECTOR, f'[id="{element_identifier}"], .{element_identifier}')
                click_containers = WebDriverWait(self.driver, timeout).until(id_condition)
                logger.debug(f"click_containers for ID: {len(click_containers)}")
                for click_container in click_containers:
                    self.driver.execute_script("arguments[0].scrollIntoView();", click_container)
                    # Wait until the element is clickable
                    WebDriverWait(self.driver, timeout).until(EC.element_to_be_clickable ((By.CSS_SELECTOR, f'[id="{element_identifier}"], .{element_identifier}')))
                    # self.driver.execute_script('arguments[0].click()', click_container)
                    try:
                        click_container.click()
                        self.driver.execute_script('arguments[0].click()', click_container)
                    except ElementClickInterceptedException:
                        logger.error(f"ElementClickInterceptedException because of click_container.click()")
                        self.driver.execute_script('arguments[0].click()', click_container)
                    time.sleep(3)

            except TimeoutException as e:
                logger.error(f"Timeout waiting for elements with identifier: '{element_identifier}' to appear: {e}")

            except Exception as e:
                logger.error(f"An error occurred while waiting for and clicking elements: {e}")

            return click_containers
        else:
            time.sleep(3)

    def capture_m3u8_urls_from_log(self):
        time.sleep(15)  # Adjust this as needed to allow the page to load

        logs = self.driver.get_log("performance")
        m3u8_url_list = []
        network_logs_list = []

        for log in logs:
            network_log = json.loads(log["message"])["message"]
            method = network_log["method"]
            params = network_log["params"]
            network_logs_list.append(network_log)
            if any(keyword in method for keyword in ["Network.response", "Network.request", "Network.webSocket"]):
                if 'request' in params:
                    request_url = params["request"].get("url", "")

                    if ('m3u8' in request_url or '.mp4' in request_url) and "blob" not in request_url:
                        if '.m3u8' in request_url:
                            logger.debug(f"m3u8: {request_url}")
                            m3u8_url_list.append(request_url)
        return m3u8_url_list