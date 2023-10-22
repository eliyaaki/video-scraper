
from flask import Blueprint, request, jsonify
import logging
from logger.logger import setup_logger
from service.video_scraper_service import VideoScraperService

# Initialize the logger
logger = setup_logger(__name__, log_level=logging.DEBUG)

video_scraper = Blueprint('video_scraper', __name__)

scraper = VideoScraperService()

@video_scraper.route('/send_url', methods=['POST'])
def scrape_website():
    if request.method == 'POST':
        url_to_scrape = request.json.get('url')  # Assume a JSON payload with 'url' field
        if url_to_scrape:
            data = request.get_json()  # Get JSON data from the request
            url = data.get('url')
            max_scroll_attempts = data.get('max_scroll_attempts')
            logger.debug(f"send_url api is being called with url: {url}")
            video_urls = scraper.initialize_driver(url, max_scroll_attempts)
            # Check if video_urls is empty
            if not video_urls:
                return jsonify({"error": "No video URLs found on the provided page."})
            return jsonify({"message": "Video scraping and processing completed.", "video_urls": video_urls})
        else:
            return jsonify({'result': 'error', 'message': 'URL not provided'})
    else:
        return jsonify({'result': 'error', 'message': 'Invalid request method'})
