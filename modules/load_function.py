import os
import boto3
import logging

# Enable logging
logger = logging.getLogger()

# Create and define the function
def load_files_to_s3(data_dir:str, AWS_ACCESS_KEY:str, AWS_SECRET_ACCESS_KEY:str, AWS_BUCKET_NAME:str):
    """Uploads all files in the directory to s3.

    Args:
        data_dir (str): data directory
        AWS_ACCESS_KEY (str): Linked to AWS IAM User
        AWS_SECRET_ACCESS_KEY (str): Linked to AWS IAM User
        AWS_BUCKET_NAME (str): S3 bucket to upload to
    """

    # Setting up s3 client
    s3_client = boto3.client(
        's3',
        aws_access_key_id = AWS_ACCESS_KEY,
        aws_secret_access_key = AWS_SECRET_ACCESS_KEY
    )

    # Logging the data folder path
    print(f'Looking in {data_dir}.')


    # Setting up variables to upload files to s3
    folders_to_upload = os.listdir(data_dir)

    # For loop to upload files
    for folder in folders_to_upload:
        folder_path = f'{data_dir}/{folder}'
        files_to_upload = os.listdir(f'{data_dir}/{folder}')

        for file in files_to_upload:
            file_to_upload = f'{data_dir}/{folder}/{file}'

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

            # After all files in this folder are handled, remove the folder if it's empty
        if not os.listdir(folder_path):
            os.rmdir(folder_path)