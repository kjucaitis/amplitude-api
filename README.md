# Amplitude to S3 Pipeline

A small Python pipeline that pulls raw event data from the [Amplitude Export API](https://amplitude.com/docs/apis/analytics/export) and loads it into an AWS S3 bucket.

The Amplitude export comes back as a **zip archive containing `.gz` files**, each of which holds newline-delimited JSON. The pipeline unpacks both layers and uploads the resulting `.json` files to S3.

## How it works

The pipeline runs in two steps:

1. **`extract.py`**
   - Requests yesterday's events from the Amplitude Export API (EU endpoint).
   - Unzips the response in memory, decompresses each `.gz` file, and writes the JSON to `data/amplitude_<timestamp>/`.
   - Retries up to 5 times (10 second delay) on server errors.
2. **`load.py`**
   - Uploads every file under `data/` to S3, keeping the folder name as the key prefix.
   - Deletes each local file once it has uploaded successfully.

Both scripts write a timestamped log file to `log/`.

## Project structure

```
.
├── extract.py          # Download and decompress Amplitude data
├── load.py             # Upload extracted files to S3
├── requirements.txt    # Python dependencies
├── .env                # Credentials (not committed)
├── data/               # Temporary local storage for extracted JSON (created on run)
└── log/                # Log files (created on run)
```

## Prerequisites

- Python 3.9+
- An Amplitude project with an API key and secret key
- An AWS account with an S3 bucket, and an IAM user with permission to write to it (`s3:PutObject`)

## Setup

1. Clone the repo:

   ```bash
   git clone https://github.com/<your-username>/<your-repo>.git
   cd <your-repo>
   ```

2. Create and activate a virtual environment:

   ```bash
   python -m venv venv

   # macOS / Linux
   source venv/bin/activate

   # Windows
   venv\Scripts\activate
   ```

3. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

4. Create a `.env` file in the project root:

   ```env
   AMP_API_KEY=your_amplitude_api_key
   AMP_SECRET_KEY=your_amplitude_secret_key
   AWS_ACCESS_KEY=your_aws_access_key_id
   AWS_SECRET_ACCESS_KEY=your_aws_secret_access_key
   AWS_BUCKET_NAME=your_s3_bucket_name
   ```

   > **Never commit your `.env` file.** Make sure `.env`, `data/` and `log/` are listed in `.gitignore`.

### Environment variables

| Variable                | Used by      | Description                                |
| ----------------------- | ------------ | ------------------------------------------ |
| `AMP_API_KEY`           | `extract.py` | Amplitude project API key                  |
| `AMP_SECRET_KEY`        | `extract.py` | Amplitude project secret key               |
| `AWS_ACCESS_KEY`        | `load.py`    | AWS access key ID                          |
| `AWS_SECRET_ACCESS_KEY` | `load.py`    | AWS secret access key                      |
| `AWS_BUCKET_NAME`       | `load.py`    | Name of the destination S3 bucket          |

## Usage

Run the two steps in order:

```bash
python extract.py
python load.py
```

### Time range

By default `extract.py` requests **yesterday, from 12:00 to 23:59**. The range is set by these two lines:

```python
start_date = f"{yesterday_str}T12"
end_date = f"{yesterday_str}T23"
```

Change the hour suffixes to adjust the window (e.g. `T00` to `T23` for the full day). Amplitude expects the format `YYYYMMDDTHH`.

### Amplitude region

The script uses the EU endpoint (`analytics.eu.amplitude.com`). If your Amplitude project is hosted in the US, change the `url` in `extract.py` to `https://amplitude.com/api/2/export`.

## S3 output

Files are uploaded with the extraction folder as the key prefix:

```
s3://<bucket>/amplitude_<YYYY-MM-DD_HH-MM-SS>/<file>.json
```

Each file contains newline-delimited JSON (one event per line).

## Logging and error handling

Logs are written to `log/amplitude_<timestamp>.log`.

`extract.py` handles Amplitude response codes as follows:

| Status      | Behaviour                                              |
| ----------- | ------------------------------------------------------ |
| `200`       | Unzip, decompress and save the data                    |
| `400`       | Log an error (export exceeds the 4 GB limit) and stop  |
| `404`       | Log a warning (no data for the time range) and stop    |
| `5xx`       | Wait 10 seconds and retry, up to 5 attempts            |
| Anything else | Log a critical error and stop                        |

In `load.py`, a failed upload is logged and the local file is kept, so it will be picked up on the next run.

## Notes and limitations

- The whole Amplitude response is held in memory during extraction, so very large exports may need a narrower time window.
- Running `load.py` uploads everything currently in `data/`, not just the latest extract.
- Amplitude's Export API has rate limits; see the [Amplitude docs](https://amplitude.com/docs/apis/analytics/export) for details.
