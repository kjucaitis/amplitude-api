# Import packages
from datetime import datetime, timedelta
import gzip
import io
import logging
import os
import time
from dotenv import load_dotenv
import requests
import zipfile

# Load .env file
load_dotenv()

# API connection variables
api_key = os.getenv("AMP_API_KEY")
secret_key = os.getenv("AMP_SECRET_KEY")

# Calculate yesterday's date
yesterday = datetime.now() - timedelta(days=1)
yesterday_str = yesterday.strftime("%Y%m%d")

# Define dynamic start (12 PM / Noon) and end (12 AM / Midnight)
start_date = f"{yesterday_str}T12"
end_date = f"{yesterday_str}T23"

# API endpoint is the EU residency server
url = "https://analytics.eu.amplitude.com/api/2/export"
params = {"start": start_date, "end": end_date}

# Make the GET request with basic authentication
response = requests.get(url, params=params, auth=(api_key, secret_key))

# Store status code
status = response.status_code

# Check status FIRST before attempting to process the file
if status == 200:

    # Create base data directory
    data_dir = "data"
    os.makedirs(data_dir, exist_ok=True)

    # Create a unique output folder for this batch using a timestamp
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    extract_folder = os.path.join(data_dir, f"amplitude_{timestamp}")
    os.makedirs(extract_folder, exist_ok=True)

# # Read zip file data and extract the files
# with zipfile.ZipFile(io.BytesIO(response.content)) as zip_file:
#     zip_file.extractall(extract_folder)

# # Print response if positive
# print(f'Status code {status}. Success! Data extracted to: {extract_folder}')

    # Read binary zip data directly from response and decompress .json.gz files
    with zipfile.ZipFile(io.BytesIO(response.content)) as zip_file:
        for file_info in zip_file.infolist():
            if file_info.is_dir():
                continue

            # 1. Read gzipped bytes directly from zip file
            gz_bytes = zip_file.read(file_info.filename)

            # 2. Decompress gzip stream into uncompressed JSON bytes
            json_bytes = gzip.decompress(gz_bytes)

            # 3. Strip .gz from filename (e.g. 12345_2026-02-02_12#0.json.gz -> 12345_2026-02-02_12#0.json)
            clean_filename = (
                file_info.filename[:-3]
                if file_info.filename.endswith(".gz")
                else file_info.filename
            )
            output_filename = os.path.basename(clean_filename)
            output_path = os.path.join(extract_folder, output_filename)

            # 4. Save plain JSON file to disk
            with open(output_path, "wb") as f:
                f.write(json_bytes)

    print(
        f"Status code {status}. Success! Data extracted and decompressed to: {extract_folder}"
    )

# Print error comments
elif status == 400:
    print(
        f"Status code {status}. The file size of the exported data is too large. Shorten the time ranges and try again. The limit size is 4GB."
    )

elif status == 404:
    print(
        f"Status code {status}. No data available for the time range requested."
    )

elif status == 504:
    print(
        f"Status code {status}. The amount of data is large causing a timeout. For large amounts of data, use the Amazon S3 destination."
    )

else:
    print(f"Error. Status code {status}. Fixing required.")