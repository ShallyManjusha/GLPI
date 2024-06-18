import os
import requests
from dotenv import load_dotenv
from flask import Flask, jsonify, request
import logging
import uuid

app = Flask(__name__)

# Set up logging
logging.basicConfig(level=logging.DEBUG)

# Load environment variables from .env file
load_dotenv()

# Retrieve environment variables
GLPI_API_URL = os.getenv('GLPI_API_URL')
GLPI_API_TOKEN = os.getenv('GLPI_API_TOKEN')
GLPI_APP_TOKEN = os.getenv('GLPI_APP_TOKEN')

# Function to check GLPI connection
def check_glpi_connection():
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'user_token {GLPI_API_TOKEN}',
        'App-Token': GLPI_APP_TOKEN
    }

    try:
        response = requests.get(f'{GLPI_API_URL}/initSession', headers=headers)
        
        if response.status_code == 200:
            return {"status": "success", "session_token": response.json()['session_token']}
        else:
            return {"status": "fail", "message": response.json(), "status_code": response.status_code}
    except requests.exceptions.RequestException as e:
        return {"status": "error", "message": str(e)}

# Function to fetch status options
def fetch_status_options(session_token):
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'user_token {GLPI_API_TOKEN}',
        'App-Token': GLPI_APP_TOKEN,
        'Session-Token': session_token
    }

    try:
        response = requests.get(f'{GLPI_API_URL}/TicketStatus', headers=headers)
        
        if response.status_code == 200:
            return {"status": "success", "data": response.json()}
        else:
            return {"status": "fail", "message": response.json(), "status_code": response.status_code}
    except requests.exceptions.RequestException as e:
        return {"status": "error", "message": str(e)}

# Function to fetch request source options
def fetch_request_source_options(session_token):
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'user_token {GLPI_API_TOKEN}',
        'App-Token': GLPI_APP_TOKEN,
        'Session-Token': session_token
    }

    try:
        response = requests.get(f'{GLPI_API_URL}/TicketType', headers=headers)
        
        if response.status_code == 200:
            return {"status": "success", "data": response.json()}
        else:
            return {"status": "fail", "message": response.json(), "status_code": response.status_code}
    except requests.exceptions.RequestException as e:
        return {"status": "error", "message": str(e)}

# Function to fetch ticket details by ID
def fetch_ticket_details(session_token, ticket_id):
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'user_token {GLPI_API_TOKEN}',
        'App-Token': GLPI_APP_TOKEN,
        'Session-Token': session_token
    }

    try:
        response = requests.get(f'{GLPI_API_URL}/Ticket/{ticket_id}', headers=headers)
        
        if response.status_code == 200:
            return {"status": "success", "ticket": response.json()}
        else:
            return {"status": "fail", "message": response.json(), "status_code": response.status_code}
    except requests.exceptions.RequestException as e:
        return {"status": "error", "message": str(e)}

# Function to raise a ticket in GLPI and fetch its details
def raise_ticket(description, session_token, status, opening_date, requester, request_source):
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'user_token {GLPI_API_TOKEN}',
        'App-Token': GLPI_APP_TOKEN,
        'Session-Token': session_token
    }

    # Generate a unique and random ticket name
    ticket_name = str(uuid.uuid4())

    ticket_data = {
        "input": {
            "name": ticket_name,
            "content": description,
            "status": status,
            "urgency": 3,
            "begin_date": opening_date,
            "requesttypes_id": request_source,
            "users_id_recipient": requester
        }
    }

    try:
        response = requests.post(f'{GLPI_API_URL}/Ticket', headers=headers, json=ticket_data)
        
        if response.status_code == 201:
            ticket_id = response.json()["id"]
            ticket_details = fetch_ticket_details(session_token, ticket_id)
            return {"status": "success", "ticket": ticket_details}
        else:
            return {"status": "fail", "message": response.json(), "status_code": response.status_code}
    except requests.exceptions.RequestException as e:
        return {"status": "error", "message": str(e)}

@app.route('/', methods=['GET'])
def home():
    return jsonify({"message": "Welcome to the GLPI API, your Ticket has been successfully generated!!"}), 200

@app.route('/favicon.ico')
def favicon():
    return '', 204

@app.route('/check_connection', methods=['GET'])
def check_connection():
    result = check_glpi_connection()
    return jsonify(result)

@app.route('/status_options', methods=['GET'])
def status_options():
    session_result = check_glpi_connection()
    if session_result['status'] == 'success':
        session_token = session_result['session_token']
        status_result = fetch_status_options(session_token)
        return jsonify(status_result)
    else:
        return jsonify(session_result)

@app.route('/request_source_options', methods=['GET'])
def request_source_options():
    session_result = check_glpi_connection()
    if session_result['status'] == 'success':
        session_token = session_result['session_token']
        request_source_result = fetch_request_source_options(session_token)
        return jsonify(request_source_result)
    else:
        return jsonify(session_result)

@app.route('/raise_ticket', methods=['POST'])
def api_raise_ticket():
    data = request.get_json()
    description = data.get('description')
    status = data.get('status')
    opening_date = data.get('opening_date')
    requester = data.get('requester')
    request_source = data.get('request_source')

    if not description or not status or not opening_date or not requester or not request_source:
        return jsonify({"status": "error", "message": "Description, status, opening_date, requester, and request_source are required"}), 400

    session_result = check_glpi_connection()
    if session_result['status'] == 'success':
        session_token = session_result['session_token']
        ticket_result = raise_ticket(description, session_token, status, opening_date, requester, request_source)
        return jsonify(ticket_result)
    else:
        return jsonify(session_result)

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug=True)
