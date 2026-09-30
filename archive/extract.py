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

# Define dynamic start and end dates - from 12PM yesterday to 12AM
start_date = f"{yesterday_str}T12"
end_date = f"{yesterday_str}T23"

# API endpoint
url = "https://analytics.eu.amplitude.com/api/2/export"
params = {"start": start_date, "end": end_date}

# Create log directory and set up file logging
log_dir = "log"
os.makedirs(log_dir, exist_ok=True)
timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
log_filename = f"{log_dir}/amplitude_{timestamp}.log"

logging.basicConfig(
    filename=log_filename,
    format="%(asctime)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)

logger = logging.getLogger()
logger.info("Logger successfully initialised")

# Retry parameters
max_retry = 5
attempt = 0
delay = 10

while attempt < max_retry:
    response = requests.get(url, params=params, auth=(api_key, secret_key))
    status = response.status_code

    if status == 200:
        data_dir = "data"
        os.makedirs(data_dir, exist_ok=True)
        extract_folder = os.path.join(data_dir, f"amplitude_{timestamp}")
        os.makedirs(extract_folder, exist_ok=True)

        try:
            with zipfile.ZipFile(io.BytesIO(response.content)) as zip_file:
                for file_info in zip_file.infolist():
                    if file_info.is_dir():
                        continue

                    gz_bytes = zip_file.read(file_info.filename)
                    json_bytes = gzip.decompress(gz_bytes)

                    clean_filename = (
                        file_info.filename[:-3]
                        if file_info.filename.endswith(".gz")
                        else file_info.filename
                    )
                    output_path = os.path.join(
                        extract_folder, os.path.basename(clean_filename)
                    )

                    with open(output_path, "wb") as f:
                        f.write(json_bytes)

            logger.info(
                f"Status code {status}. Data extracted and decompressed to: {extract_folder}"
            )

        except Exception as e:
            logger.error(f"An error has occurred: {e}")

        break

    elif status == 400:
        logger.error(f"Status code {status}. File size too large (limit 4GB).")
        break

    elif status == 404:
        logger.warning(
            f"Status code {status}. No data available for requested time range."
        )
        break

    elif status < 200 or status >= 500:
        time.sleep(delay)
        attempt += 1
        logger.info(
            f"Status code: {status}. Retrying. Attempt number {attempt}"
        )

    else:
        logger.critical(f"Error. Status code {status}. Fixing required")
        break