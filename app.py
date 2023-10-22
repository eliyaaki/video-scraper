from flask import Flask, request, jsonify
import logging
from logger.logger import setup_logger
from service.website_video_scraper import WebsiteVideoScraper


from routes.video_scraper_routes import video_scraper

# Initialize the logger
logger = setup_logger(__name__, log_level=logging.DEBUG)

app = Flask(__name__)
app.register_blueprint(video_scraper)

app.debug = True  # Enable debug mode

@app.route('/', methods=['GET'])
def hello():
    return jsonify({"message": "hello"})


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
