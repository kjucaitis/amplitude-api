from datetime import datetime, timedelta
from dotenv import load_dotenv
import os

from modules.extract_function import extract_json
from modules.log_initialise import setup_logging
from modules.load_function import load_files_to_s3

# Load .env file
load_dotenv()

# Defining data directory
data_dir = 'data'

# API connection variables
api_key = os.getenv("AMP_API_KEY")
secret_key = os.getenv("AMP_SECRET_KEY")

# Bring through our keys for AWS
AWS_ACCESS_KEY = os.getenv('AWS_ACCESS_KEY')
AWS_SECRET_ACCESS_KEY = os.getenv('AWS_SECRET_ACCESS_KEY')
AWS_BUCKET_NAME = os.getenv('AWS_BUCKET_NAME')

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
delay = 10

# Initialise logging (creates logs/<timestamp>.log)
logger = setup_logging(log_dir="logs", timestamp=timestamp)
logger.info("Starting Amplitude extract")

# Running functions
extract_json(url,params,api_key,secret_key,data_dir,timestamp,max_retry,delay)
load_files_to_s3(data_dir,AWS_ACCESS_KEY,AWS_SECRET_ACCESS_KEY,AWS_BUCKET_NAME)