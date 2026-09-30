# Import packages
import gzip  # decompresses the .gz files inside the ZIP
import io  # lets us treat the downloaded bytes as an in-memory file
import logging  # writes status / error messages
import os  # creates folders and builds file paths
import time  # used for the sleep between retries
import requests  # makes the HTTP call to the API
import zipfile  # opens the ZIP that the API returns

# Enable logger
logger = logging.getLogger()

# Defining the function
def extract_json(url:str, params:str, api_key:str, secret_key:str, timestamp:str, max_retry:int, delay:int):
    """Extracts JSON files from specified URL if they are in a ZIP files that has .gz files in it.

    Args:
        url (str): URL where API is being called from
        params (str): parameters for the timestamps to determine which data to pull from the API
        api_key (str): API access key
        secret_key (str): API Secret key
        timestamp (str): output's filename
        max_retry (int): the maximum number of times to try calling the api
        delay (int): how long to wait between retries (seconds)
    """
    # Defining attempt no
    attempt = 0

    # Keep trying until we've used up all the allowed attempts
    while attempt < max_retry:
        # Call the API; the key and secret are sent as basic auth (username, password)
        response = requests.get(url, params=params, auth=(api_key, secret_key))
        status = response.status_code

        # --- Success: got the data ---
        if status == 200:
            # Make sure a "data" folder exists (no error if it already does)
            data_dir = "data"
            os.makedirs(data_dir, exist_ok=True)
            # Make a subfolder for this run, named using the timestamp, e.g. data/amplitude_<timestamp>
            extract_folder = os.path.join(data_dir, f"amplitude_{timestamp}")
            os.makedirs(extract_folder, exist_ok=True)

            try:
                # response.content is the raw ZIP; BytesIO lets zipfile read it without saving it to disk first
                with zipfile.ZipFile(io.BytesIO(response.content)) as zip_file:
                    # Loop over everything inside the ZIP
                    for file_info in zip_file.infolist():
                        # Skip folder entries, we only want files
                        if file_info.is_dir():
                            continue

                        # Read the compressed .gz file out of the ZIP (as bytes)
                        gz_bytes = zip_file.read(file_info.filename)
                        # Decompress the .gz to get the actual JSON bytes
                        json_bytes = gzip.decompress(gz_bytes)

                        # Drop the ".gz" from the end of the filename so it becomes a normal .json file
                        clean_filename = (
                            file_info.filename[:-3]
                            if file_info.filename.endswith(".gz")
                            else file_info.filename
                        )
                        # Build the output path; basename strips any folders that were inside the ZIP,
                        # so every file lands directly in extract_folder
                        output_path = os.path.join(
                            extract_folder, os.path.basename(clean_filename)
                        )

                        # Write the decompressed JSON to disk ("wb" = write as bytes)
                        with open(output_path, "wb") as f:
                            f.write(json_bytes)

                # Log success once every file has been written
                logger.info(
                    f"Status code {status}. Data extracted and decompressed to: {extract_folder}"
                )

            # Catch anything that goes wrong while unzipping / decompressing / writing and log it
            except Exception as e:
                logger.error(f"An error has occurred: {e}")

            # Done (success or not) - exit the retry loop, no need to call the API again
            break

        # --- 400: bad request, retrying won't help ---
        elif status == 400:
            logger.error(f"Status code {status}. File size too large (limit 4GB).")
            break

        # --- 404: nothing exists for that time range, retrying won't help ---
        elif status == 404:
            logger.warning(
                f"Status code {status}. No data available for requested time range."
            )
            break

        # --- Server-side / unexpected codes (<200 or 500+): worth retrying ---
        elif status < 200 or status >= 500:
            time.sleep(delay)  # wait before trying again
            attempt += 1  # count this attempt so the while loop eventually stops
            logger.info(
                f"Status code: {status}. Retrying. Attempt number {attempt}"
            )

        # --- Any other status code (e.g. 401, 403, 429): not handled, log it and stop ---
        else:
            logger.critical(f"Error. Status code {status}. Fixing required")
            break