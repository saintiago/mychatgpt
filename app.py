import boto3
import json
import requests
import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Function to retrieve secrets from AWS Secrets Manager
def get_secret(secret_name):
    session = boto3.session.Session()
    client = session.client(service_name='secretsmanager', region_name='eu-central-1')
    response = client.get_secret_value(SecretId=secret_name)
    return json.loads(response['SecretString'])

# Load tokens from AWS Secrets Manager
secrets = get_secret('telegram_bot_secrets')
TELEGRAM_TOKEN = secrets['TELEGRAM_TOKEN']
OPENAI_API_KEY = secrets['OPENAI_API_KEY']

# Define OpenAI API endpoint URL
OPENAI_API_URL = 'https://api.openai.com/v1/chat/completions'

# Set headers for OpenAI API request
headers = {
    'Content-Type': 'application/json',
    'Authorization': f'Bearer {OPENAI_API_KEY}'
}

def lambda_handler(event, context):

    # Parse the incoming JSON update from Telegram
    update = json.loads(event["body"])

    logger.info(update)

    # Check if the update has a message field
    if 'message' in update:

        # Extract the chat ID and message text from the update
        chat_id = update['message']['chat']['id']
        message_text = update['message']['text']

        # Prepare the prompt for the OpenAI API
        prompt = f'{message_text}\nResponse:'

        # Define the data to be sent to the OpenAI API
        data = {
            "model": "gpt-4",
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.7
        }

        # Send a POST request to the OpenAI API with the headers and data
        response = requests.post(OPENAI_API_URL, headers=headers, json=data)

        logger.info(response.json())

        # Extract the generated response text from the API's JSON response
        response_text = response.json()['choices'][0]['message']['content'].strip()

        # Send the generated response back to the user on Telegram
        send_message(chat_id, response_text)

    # Return a simple response to acknowledge receipt of the update
    return {
        "statusCode": 200,
        "body": json.dumps('ok')
    }

# Define a function to send messages via the Telegram Bot API
def send_message(chat_id, text):
    # Construct the URL for the sendMessage API endpoint
    url = f'https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage'

    # Define the payload to be sent in the POST request
    payload = {
        'chat_id': chat_id,
        'text': text
    }

    # Send the POST request with the payload
    requests.post(url, json=payload)
