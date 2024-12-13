from flask import Flask, jsonify, Blueprint
import requests
import json
import random
import time
from config import Config
from utils.logger import Logger

business_search_api = Blueprint('business_search_api', __name__)
logger = Logger('business_search_api')

# API Configuration
BASE_URL = "http://35.227.114.49:8080/api/v2/tables"
TOKEN = "-iGWInPJpwDcwvB0t3XqdGiVFsTRJmcEA3457AUD"

def fetch_random_us_city():
    url = f"{BASE_URL}/ms38nwz5p1q0gxz/records?where=(country_code,eq,US)&limit=1000&shuffle=1"
    headers = {"accept": "application/json", "xc-token": TOKEN}
    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            cities = response.json().get("list", [])
            return random.choice(cities) if cities else None
    except Exception as e:
        logger.error(f"Error fetching random city: {str(e)}")
    return None

def fetch_random_occupation():
    url = f"{BASE_URL}/mj849ro0fwra5er/records?limit=1&shuffle=1"
    headers = {"accept": "application/json", "xc-token": TOKEN}
    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            occupations = response.json().get("list", [])
            return occupations[0] if occupations else None
    except Exception as e:
        logger.error(f"Error fetching random occupation: {str(e)}")
    return None

@business_search_api.route('/usa_random_profile_with_businesses', methods=['GET'])
def get_usa_random_profile_with_businesses():
    try:
        # Fetch random city and occupation
        city = fetch_random_us_city()
        if not city:
            return jsonify({"error": "Failed to fetch a random US city"}), 500
        
        occupation = fetch_random_occupation()
        if not occupation:
            return jsonify({"error": "Failed to fetch a random occupation"}), 500

        # Create message for business search queue
        search_message = {
            "city": {
                "name": city.get('name', 'Unknown'),
                "state_code": city.get('state_code', 'Unknown'),
                "latitude": city.get('latitude', 'Unknown'),
                "longitude": city.get('longitude', 'Unknown')
            },
            "occupation": occupation.get('Occupation', 'Unknown'),
            "timestamp": time.time()
        }

        # Publish to RabbitMQ business queue
        channel = Config.get_rabbitmq_channel()
        channel.basic_publish(
            exchange='',
            routing_key='business_queue',
            body=json.dumps(search_message),
            properties=pika.BasicProperties(
                delivery_mode=2,  # make message persistent
                content_type='application/json'
            )
        )

        return jsonify({
            "status": "processing",
            "request_id": f"{city.get('name')}_{int(time.time())}",
            "profile": search_message
        })

    except Exception as e:
        logger.error(f"Error processing random profile request: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500 