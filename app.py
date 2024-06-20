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

# Global variable to store the ticket title
created_ticket_title = None

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

# Function to fetch ticket details by Title
def fetch_ticket_details_by_title(session_token, ticket_title):
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'user_token {GLPI_API_TOKEN}',
        'App-Token': GLPI_APP_TOKEN,
        'Session-Token': session_token
    }
    try:
        response = requests.get(f'{GLPI_API_URL}/search/Ticket?criteria[0][field]=1&criteria[0][searchtype]=contains&criteria[0][value]={ticket_title}', headers=headers)
        logging.debug(f'GLPI fetch ticket details by title response: {response.json()}')
        
        if response.status_code == 200:
            tickets = response.json()["data"]
            if tickets:
                ticket_id = tickets[0]["id"]
                ticket_details = fetch_ticket_details(session_token, ticket_id)
                return ticket_details
            else:
                return {"status": "fail", "message": "No ticket found with the given title"}
        else:
            return {"status": "fail", "message": response.json(), "status_code": response.status_code}
    except requests.exceptions.RequestException as e:
        logging.error(f'Error fetching ticket details by title: {str(e)}')
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
            ticket = response.json()
            return {
                "status": "success",
                "ticket": {
                    "ID": ticket["id"],
                    "Title": ticket["name"],
                    "Description": ticket["content"],
                    "Status": ticket["status"],
                    "Urgency": ticket["urgency"],
                    "Opening Date": ticket["date"],
                    # "Requester": ticket["_users_id_requester"],
                    "Request Source": ticket["requesttypes_id"],
                    "itilcategories_id": ticket["itilcategories_id"]
                }
            }
        else:
            return {"status": "fail", "message": response.json(), "status_code": response.status_code}
    except requests.exceptions.RequestException as e:
        logging.error(f'Error fetching ticket details: {str(e)}')
        return {"status": "error", "message": str(e)}

# Function to raise a ticket in GLPI
def raise_ticket(description, session_token, status, date, request_source):
    global created_ticket_title  # Use the global variable

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
            "date": date,  # Changed to 'date'
            "requesttypes_id": request_source,
            # "_users_id_requester": requester_email,
            # "itilcategories_id": itil_category_id,
            "type": 2
        }
    }

    logging.debug(f'GLPI ticket data: {ticket_data}')

    try:
        response = requests.post(f'{GLPI_API_URL}/Ticket', headers=headers, json=ticket_data)
        logging.debug(f'GLPI raise ticket response: {response.json()}')

        if response.status_code == 201:
            ticket_id = response.json()["id"]
            created_ticket_title = ticket_name  # Store the ticket title
            ticket_details = fetch_ticket_details(session_token, ticket_id)
            return {"status": "success", "ticket_number": ticket_id, "ticket_title": ticket_name, "ticket": ticket_details}
        else:
            logging.debug(f'GLPI raise ticket failed response: {response.json()}')
            return {"status": "fail", "message": response.json(), "status_code": response.status_code}
    except requests.exceptions.RequestException as e:
        logging.error(f'Error raising ticket: {str(e)}')
        return {"status": "error", "message": str(e)}

# Function to fetch created ticket title
def fetch_created_ticket_title():
    if created_ticket_title:
        return {"ticket_title": created_ticket_title}
    else:
        return {"status": "fail", "message": "No ticket title available"}

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
    date = data.get('date')  # Changed from 'opening_datetime' to 'date'
    # requester_email = data.get('requester_email')  # Use 'requester_email' field
    request_source = data.get('request_source')
    # itil_category_id = data.get('itilcategories_id')  # Include 'itilcategories_id' field

    logging.debug(f'API raise_ticket received data: {data}')

    # Validate required fields
    if not description or not status or not date  or not request_source :
        return jsonify({"status": "error", "message": "Description, status, date, request_source, and itilcategories_id are required"}), 400

    # Map status and request source to internal IDs
    status_id = STATUS_MAPPING.get(status, None)
    request_source_id = REQUEST_SOURCE_MAPPING.get(request_source, None)

    if status_id is None:
        return jsonify({"status": "error", "message": f"Invalid status: {status}"}), 400
    if request_source_id is None:
        return jsonify({"status": "error", "message": f"Invalid request source: {request_source}"}), 400

    try:
        # Check GLPI connection
        session_result = check_glpi_connection()
        if session_result['status'] == 'success':
            session_token = session_result['session_token']

             # Default time to '00:00:00' if only date is provided
            if len(date.split()) == 1:  # Check if date string contains only date part
                date += " 00:00:00"  # Append default time

            # Raise ticket
            ticket_result = raise_ticket(description, session_token, status_id, date, request_source_id)
            return jsonify(ticket_result)
        else:
            return jsonify(session_result)
    except ValueError as e:
        logging.error(f'ValueError: {str(e)}')
        return jsonify({"status": "error", "message": str(e)}), 400
    except Exception as e:
        logging.error(f'Exception: {str(e)}')
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route('/fetch_ticket_by_title', methods=['GET'])
def fetch_ticket_by_title():
    title = request.args.get('title')
    if not title:
        return jsonify({"status": "error", "message": "Title parameter is required"}), 400
    session_result = check_glpi_connection()
    if session_result['status'] == 'success':
        session_token = session_result['session_token']
        ticket_details = fetch_ticket_details_by_title(session_token, title)
        return jsonify(ticket_details)
    else:
        return jsonify(session_result)

@app.route('/get_created_ticket_title', methods=['GET'])
def get_created_ticket_title():
    result = fetch_created_ticket_title()
    return jsonify(result)

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug=True)
