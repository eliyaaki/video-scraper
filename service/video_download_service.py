from bs4 import BeautifulSoup
import subprocess
import os
import requests
import logging
from logger.logger import setup_logger

# Initialize the logger without needing to know the configuration details
logger = setup_logger(__name__, log_level=logging.DEBUG)

DEFAULT_URL = "https://www.mako.co.il/news-military/6361323ddea5a810/Article-93bd6261a6f3b81027.htm?sCh=31750a2610f26110&pId=173113802"
DEFAULT_PARENT_DIRECTORY = "videos"
DEFAULT_REMOTE_WEB_DRIVER = "http://selenium:4444/wd/hub"
DEFAULT_MAX_VIDEO_DOWNLOAD_RETRIES = 3

class VideoDownloadService:
    def __init__(self):
        self.m3u8 = None
        self.parent_directory = DEFAULT_PARENT_DIRECTORY
        self.output_directory = DEFAULT_PARENT_DIRECTORY
        self.max_video_download_retries = int(
            os.environ.get("MAX_VIDEO_DOWNLOAD_RETRIES", DEFAULT_MAX_VIDEO_DOWNLOAD_RETRIES))




    def set_m3u8_and_folder_name(self, url, news_organizations):
        for org_data in news_organizations:
            news_organisation_name = org_data["name"]
            if url.startswith(org_data["url"]):
                # Define the output directory under the parent directory
                self.output_directory = os.path.join(self.parent_directory, f"{news_organisation_name}_videos")
                self.m3u8 = org_data.get("m3u8_name", None)
                logger.debug(
                    f"initializing m3u8: {self.m3u8}")
                break  # Exit the loop if a match is found


    def is_valid_url(self, url):
        try:
            response = requests.head(url)  # Use head request to check without downloading content
            if response.status_code == 200:
                logger.debug(f"Url is valid: {url}")
                return True  # The URL is valid
            else:
                logger.debug(f"Url is not valid: {url}")
                return False  # The URL returned a non-200 status code
        except requests.exceptions.RequestException:
            logger.debug(f"requests exception for url: {url}")
            return False  # An error occurred while accessing the URL

    def save_html_to_file(self, soup):
        file = "entire_html_page.html"
        with open(file, 'w', encoding='utf-8') as file:
            file.write(soup.prettify())
        logger.debug(f"BeautifulSoup object saved to '{file}'")

    def extract_video_urls(self, html_content):
        soup = BeautifulSoup(html_content, 'html.parser')
        self.save_html_to_file(soup)
        video_urls = [video['src'] for video in soup.find_all('video', src=True)]
        logger.debug(f"video_urls: {video_urls}")
        return video_urls

    def extract_m3u8_prefix(self, url):
        # Split the URL by '/'
        parts = url.split('/')

        # Iterate through the parts to find the one containing ".m3u8"
        for part in parts:
            if ".m3u8" in part:
                prefix = part.split(".m3u8")[0]
                break
        return prefix

    def process_page(self, url, news_organizations, page_source, m3u8_urls):
        try:
            self.set_m3u8_and_folder_name(url, news_organizations)
            video_urls = self.extract_video_urls(page_source)
            return self.process_video(video_urls, m3u8_urls)
        except Exception as e:
            logger.error(f"An error occurred while processing video URLs: {e}")


    def process_video(self, video_urls, m3u8_urls):
        try:
            # Process MP4 video files
            mp4_files_saved = self.process_mp4_files(video_urls)

            # Process m3u8 playlist files
            playlist_files_saved = self.process_playlist_files(m3u8_urls)

            if mp4_files_saved:
                return mp4_files_saved
            elif playlist_files_saved:
                return playlist_files_saved
        except Exception as e:
            logger.error(f"An error occurred while processing video URLs: {e}")

    def process_mp4_files(self, video_urls):
        mp4_files= []
        if video_urls:
            for video_src in video_urls:
                if video_src.endswith('.mp4'):
                    mp4_files.append(video_src)
            for mp4_file in mp4_files:
                self.download_mp4(mp4_file)
        return mp4_files

    def process_playlist_files(self, m3u8_video_urls):
        playlist_files = self.extract_playlist_files(m3u8_video_urls)
        if playlist_files:
            logger.debug(f"There are: {len(playlist_files)} to be saved")
            logger.debug(f"playlist_files before save: {playlist_files}")
            for playlist_file in playlist_files:
                self.download_playlist(playlist_file)
            return playlist_files
        return None

    def extract_playlist_files(self, m3u8_urls):

        logger.debug(f"m3u8_urls {len(m3u8_urls)}")
        # Filter the list to find .m3u8 files with media playlists
        playlist_files = [file for file in m3u8_urls if self.has_media_playlist(file)]
        logger.debug(f"playlist_files: {playlist_files}, amount: {len(playlist_files)}")

        return playlist_files

    def has_media_playlist(self, url):
        m3u8_prefix = self.extract_m3u8_prefix(url)
        if self.is_valid_url(url) and (self.m3u8 is None or self.m3u8 in url):
            logger.debug(f"The desired {self.m3u8} is found successfully in the URL: {url}")
            return True
        else:
            logger.debug(f"The desired {self.m3u8} is not found in the URL, the m3u8_prefix from the URL: {m3u8_prefix}")
            return False

    def ensure_mp4_extension(self, file_path):
        # Check if the file path ends with ".mp4"
        if not file_path.endswith(".mp4"):
            # If it doesn't, append ".mp4" to the file path
            file_path += ".mp4"
        return file_path

    def get_filename_from_url(self, url):

        # Split the URL by '/'
        parts = url.split('/')

        # Extract the last two parts and join them with a comma
        filename = ','.join(parts[-3:-1])

        return self.ensure_mp4_extension(filename)

    def get_filename_from_mp4_url(self, url):
        # Split the URL by '/' to separate the path components
        url_parts = url.split('/')

        # Get the last part of the URL, which should be the filename
        filename = url_parts[-1]
        filename = filename.split('?')[0]

        return filename


    def create_directories(self):
        # Create the parent directory if it doesn't exist
        os.makedirs(self.parent_directory, exist_ok=True)

        # Create the output directory if it doesn't exist
        os.makedirs(self.output_directory, exist_ok=True)

    def download_playlist(self, playlist_url):
        self.create_directories()
        full_file_name = os.path.join(self.output_directory, f"{self.get_filename_from_url(playlist_url)}")
        cmd = [
            'ffmpeg',
            '-i', playlist_url,
            '-c', 'copy',
            full_file_name
        ]
        self.download_with_retry(cmd, full_file_name, playlist_url)

    def download_with_retry(self, cmd, full_file_name, playlist_url):
        retries = 0
        while retries < self.max_video_download_retries:
            try:
                subprocess.run(cmd, timeout=120, check=True, stderr=subprocess.PIPE, text=True)
                logger.debug(f"Downloaded and converted playlist to {full_file_name}")
                break  # Success, exit the loop
            except subprocess.CalledProcessError as e:
                logger.error(f"An error occurred: {e}")
                logger.error(f"FFmpeg error output: {e.stderr}" )
                logger.error(f"Retrying ({retries + 1}/{self.max_video_download_retries})...")
                retries += 1
            except subprocess.TimeoutExpired:
                # Handle the timeout error
                logger.error("FFmpeg command timed out.")
        else:
            logger.debug(f"Max retries reached. Failed to download and convert {playlist_url}")

    def download_mp4(self, mp4_url):
        self.create_directories()
        full_file_name = os.path.join(self.output_directory, self.get_filename_from_mp4_url(mp4_url))
        response = requests.get(mp4_url, stream=True)
        if self.is_valid_url(mp4_url):
            with open(full_file_name, 'wb') as file:
                for chunk in response.iter_content(chunk_size=1024):
                    if chunk:
                        file.write(chunk)
            logger.debug(f"Downloaded {full_file_name}")
        else:
            logger.debug(f"Failed to download: {mp4_url}")


