import os
import requests
import io
import zipfile
from datetime import datetime
import time
import logging
from dotenv import load_dotenv

# Load .env file
load_dotenv()

# API connection variables
api_key = os.getenv('AMP_API_KEY')
secret_key = os.getenv('AMP_SECRET_KEY')

# API endpoint is the EU residency server
url = 'https://analytics.eu.amplitude.com/api/2/export'
params = {
    'start': '20260202T12',
    'end': '20260202T23'
}

# Make the GET request with basic authentication
response = requests.get(url, params=params, auth=(api_key, secret_key))

# Store status code
status = response.status_code

# Check status FIRST before attempting to process the file
if status == 200:
    
    # Create base data directory
    data_dir = 'data'
    os.makedirs(data_dir, exist_ok=True)

    # Create a unique output folder for this batch using a timestamp
    timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
    extract_folder = os.path.join(data_dir, f"amplitude_{timestamp}")

    # Read binary zip data directly from response and extract files
    with zipfile.ZipFile(io.BytesIO(response.content)) as zip_file:
        zip_file.extractall(extract_folder)

    print(f'Status code {status}. Success! Data extracted to: {extract_folder}')

# Print error comments
elif status == 400:
    print(f'Status code {status}. The file size of the exported data is too large. Shorten the time ranges and try again. The limit size is 4GB.')

elif status == 404:
    print(f'Status code {status}. No data available for the time range requested.')

elif status == 504:
    print(f'Status code {status}. The amount of data is large causing a timeout. For large amounts of data, use the Amazon S3 destination.')

else:
    print(f'Error. Status code {status}. Fixing required.')