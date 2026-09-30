import os
import boto3
from dotenv import load_dotenv
import logging
from datetime import datetime

# Load the .env file to access our variables
load_dotenv()

# Bring through our keys
AWS_ACCESS_KEY = os.getenv('AWS_ACCESS_KEY')
AWS_SECRET_ACCESS_KEY = os.getenv('AWS_SECRET_ACCESS_KEY')
AWS_BUCKET_NAME = os.getenv('AWS_BUCKET_NAME')

# Setting up s3 client
s3_client = boto3.client(
    's3',
    aws_access_key_id = AWS_ACCESS_KEY,
    aws_secret_access_key = AWS_SECRET_ACCESS_KEY
)

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

# Create a logger and confirm that it has been successfully set up
logger = logging.getLogger()
logger.info('Logger successfully initialised')

# Setting up variables to upload files to s3
folders_to_upload = os.listdir('data')

for folder in folders_to_upload:
    files_to_upload = os.listdir(f'data/{folder}')

    for file in files_to_upload:
        file_to_upload = f'data/{folder}/{file}'

        try:
            #Uploading files to s3
            s3_client.upload_file(file_to_upload,AWS_BUCKET_NAME,f'{folder}/{file}')
            print(f'{file_to_upload} uploaded successfuly.')

            # Logging success
            logger.info(f'File {file_to_upload} uploaded successfuly.')

            # Removing the file from our local device
            os.remove(file_to_upload)

        # Error handling
        except Exception as e:
            print(f'An error has occured: {e}.')

            # Logging failure
            logger.error(f'An error has occured: {e}.')


