from datetime import datetime, timedelta
from dotenv import load_dotenv
import os

from modules.extract_function import extract_json
from modules.log_initialise import setup_logging

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

# Used for the log filename and the output folder name
timestamp = yesterday_str

# Retry parameters
max_retry = 5
attempt = 0
delay = 10

# Initialise logging (creates logs/<timestamp>.log)
logger = setup_logging(log_dir="logs", timestamp=timestamp)
logger.info("Starting Amplitude extract")

extract_json(
    url=url,
    params=params,
    api_key=api_key,
    secret_key=secret_key,
    timestamp=timestamp,
    max_retry=max_retry,
    attempt=attempt,
    delay=delay,
)