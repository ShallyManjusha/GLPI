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
# Status and Request Source Mapping
STATUS_MAPPING = {
    "New": 1,
    "Processing (assigned)": 2,
    "Processing (planned)": 3,
    "Pending": 4,
    "Solved": 5,
    "Closed": 6
}
REQUEST_SOURCE_MAPPING = {
    "------": 7,
    "Direct": 4,
    "Email": 2,
    "Helpdesk": 1,
    "Other": 6,
    "Phone": 3,
    "Written": 5
}
# Function to check GLPI connection
def check_glpi_connection():
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'user_token {GLPI_API_TOKEN}',
        'App-Token': GLPI_APP_TOKEN
    }
    try:
        response = requests.get(f'{GLPI_API_URL}/initSession', headers=headers)
        logging.debug(f'GLPI initSession response: {response.json()}')
        
        if response.status_code == 200:
            return {"status": "success", "session_token": response.json()['session_token']}
        else:
            return {"status": "fail", "message": response.json(), "status_code": response.status_code}
    except requests.exceptions.RequestException as e:
        logging.error(f'Error checking GLPI connection: {str(e)}')
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
        logging.debug(f'GLPI fetch status options response: {response.json()}')
        
        if response.status_code == 200:
            return {"status": "success", "data": response.json()}
        else:
            return {"status": "fail", "message": response.json(), "status_code": response.status_code}
    except requests.exceptions.RequestException as e:
        logging.error(f'Error fetching status options: {str(e)}')
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
        logging.debug(f'GLPI fetch request source options response: {response.json()}')
        
        if response.status_code == 200:
            return {"status": "success", "data": response.json()}
        else:
            return {"status": "fail", "message": response.json(), "status_code": response.status_code}
    except requests.exceptions.RequestException as e:
        logging.error(f'Error fetching request source options: {str(e)}')
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
        logging.debug(f'GLPI fetch ticket details response: {response.json()}')
        
        if response.status_code == 200:
            return {"status": "success", "ticket": response.json()}
        else:
            return {"status": "fail", "message": response.json(), "status_code": response.status_code}
    except requests.exceptions.RequestException as e:
        logging.error(f'Error fetching ticket details: {str(e)}')
        return {"status": "error", "message": str(e)}
# Function to raise a ticket in GLPI and fetch its details
def raise_ticket(description, session_token, status, opening_datetime, requester, request_source):
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
            "begin_date": opening_datetime,  # Date and time part in dd-mm-yyyy HH:mm:SS format
            "users_id_requester":requester,
            "type":2,
            "requesttypes_id": request_source
            
        }
    }
    logging.debug(f'GLPI ticket data: {ticket_data}')
    try:
        response = requests.post(f'{GLPI_API_URL}/Ticket', headers=headers, json=ticket_data)
        logging.debug(f'GLPI raise ticket response: {response.json()}')
        
        if response.status_code == 201:
            ticket_id = response.json()["id"]
            ticket_details = fetch_ticket_details(session_token, ticket_id)
            return {"status": "success", "ticket_number": ticket_id, "ticket_title": ticket_name, "ticket": ticket_details}
        else:
            logging.debug(f'GLPI raise ticket failed response: {response.json()}')
            return {"status": "fail", "message": response.json(), "status_code": response.status_code}
    except requests.exceptions.RequestException as e:
        logging.error(f'Error raising ticket: {str(e)}')
        return {"status": "error", "message": str(e)}
@app.route('/', methods=['GET'])
def home():
    return jsonify({"message": "Welcome to the GLPI API"}), 200
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
    opening_datetime = data.get('opening_datetime')  # Changed to 'opening_datetime'
    requester = data.get('requester')  # Keep as text input
    request_source = data.get('request_source')
    logging.debug(f'API raise_ticket received data: {data}')
    # Validate required fields
    if not description or not status or not opening_datetime or not requester or not request_source:
        return jsonify({"status": "error", "message": "Description, status, opening_datetime, requester, and request_source are required"}), 400
    # Map status and request source to internal IDs
    status_id = STATUS_MAPPING.get(status, None)
    request_source_id = REQUEST_SOURCE_MAPPING.get(request_source, None)
    if status_id is None:
        return jsonify({"status": "error", "message": f"Invalid status: {status}"}), 400
    if request_source_id is None:
        return jsonify({"status": "error", "message": f"Invalid request source: {request_source}"}), 400
    try:
        # Send opening_datetime directly in dd-mm-yyyy HH:mm:SS format
        session_result = check_glpi_connection()
        if session_result['status'] == 'success':
            session_token = session_result['session_token']
            
            ticket_result = raise_ticket(description, session_token, status_id, opening_datetime, requester, request_source_id)
            return jsonify(ticket_result)
        else:
            return jsonify(session_result)
    except ValueError as e:
        logging.error(f'ValueError: {str(e)}')
        return jsonify({"status": "error", "message": str(e)}), 400
    except Exception as e:
        logging.error(f'Exception: {str(e)}')
        return jsonify({"status": "error", "message": str(e)}), 500
if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug=True)
