import os
import sys
import logging
from dotenv import load_dotenv
from datetime import datetime
import requests
import argparse
import time
import json
from pathlib import Path
import csv
import pandas as pd
import zipfile

# Load .env file if present
load_dotenv()
API_KEY = os.getenv("WEATHER_API_KEY")

if not API_KEY:
    logging.error("API key missing.")
    print("⚠️ Missing API key. Please set WEATHER_API_KEY in .env")
    sys.exit(1)

# ---- Project folders ----
LOG_DIR = os.path.join(os.path.dirname(__file__), "logs")
os.makedirs(LOG_DIR, exist_ok=True)

# ---- Main Logger (basicConfig) ----
main_log_file = os.path.join(LOG_DIR, "main.log")
file_handler = logging.FileHandler(main_log_file)
console_handler = logging.StreamHandler(sys.stdout)

logging.basicConfig(
    level=logging.INFO,
    handlers=[file_handler, console_handler],
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)

logger = logging.getLogger("main")  # general purpose

# ---- Specialized Logger: Errors ----
errors_logger = logging.getLogger("errors_logger")
errors_logger.setLevel(logging.WARNING)
errors_handler = logging.FileHandler(os.path.join(LOG_DIR, "errors.log"))
errors_formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")
errors_handler.setFormatter(errors_formatter)
errors_logger.addHandler(errors_handler)

# ---- Specialized Logger: Export ----
export_logger = logging.getLogger("export_logger")
export_logger.setLevel(logging.INFO)
export_handler = logging.FileHandler(os.path.join(LOG_DIR, "export.log"))
export_formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")
export_handler.setFormatter(export_formatter)
export_logger.addHandler(export_handler)

# ---- Argument Parsing ----
parser = argparse.ArgumentParser(description="File parser with logging and error detection")
parser.add_argument("csv", help="Path to the CSV log file to process")
parser.add_argument("city", help="City to fetch weather for")
parser.add_argument(
    "--units",
    choices=["C", "F"],
    default="F",
    help="Temperature units (C or F)"
)
args = parser.parse_args()

if not os.path.isfile(args.csv):
    errors_logger.error(f"CSV file not found: {args.csv}")
    print(f"Error: CSV file not found: {args.csv}")
    sys.exit(1)

logger.info(f"CSV file found: {args.csv}")


# Construct URL
url = f"https://api.weatherapi.com/v1/current.json?q={args.city}&key={API_KEY}"
logger.info("Script start")

# Retry logic
for attempt in range(3):
    try:
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            break
        else:
            logging.warning(f"Attempt {attempt+1}: API returned {response.status_code}")
    except requests.exceptions.RequestException as e:
        logging.warning(f"Attempt {attempt+1}: {e}")
    time.sleep(2)
else:
    print("All attempts failed.")
    errors_logger.error("All API attempts failed.")
    exit(1)

# Process successful response
try:
    data = response.json()
    location = f"{data['location']['name']}, {data['location']['country']}"
    if args.units == "F":
        temp = data["current"]["temp_f"]
        unit_symbol = "°F"
    else:
        temp = data["current"]["temp_c"]
        unit_symbol = "°C"
    condition = data["current"]["condition"]["text"]
    logger.info(f"Weather location: {args.city}")
except (KeyError, ValueError, json.JSONDecodeError) as e:
    errors_logger.exception("Error parsing weather API response")
    print("Error: Weather API returned unexpected data format.")
    sys.exit(1)

# Filter CRITICAL rows
try:
    df = pd.read_csv(args.csv)
    logger.info(f"CSV file loaded: {args.csv}")
except pd.errors.EmptyDataError:
    errors_logger.error(f"CSV file is empty: {args.csv}")
    print("Error: CSV file is empty.")
    sys.exit(1)
except Exception as e:
    errors_logger.exception(f"Error reading CSV file: {args.csv}")
    print(f"Unexpected error reading {args.csv}")
    sys.exit(1)

if 'level' not in df.columns:
    errors_logger.error("Column 'level' not found in CSV.")
    print("Error: Column 'level' not found in CSV.")
    sys.exit(1)  # stop script, no point continuing

critical_rows = df[df['level'] == 'CRITICAL'].copy()

if critical_rows.empty:
    logger.warning("No CRITICAL rows found in CSV.")
else:
    logger.info(f"Found {len(critical_rows)} critical rows")

# Enrich Data 
try:
    critical_rows.loc[:, "weather_location"] = location
    critical_rows.loc[:, "weather_temp"] = temp
    critical_rows.loc[:, "weather_unit"] = unit_symbol
    critical_rows.loc[:, "weather_condition"] = condition
    logger.info(f"Weather enrichment added for {len(critical_rows)} rows")
except Exception as e:
    errors_logger.exception("Error enriching CSV data")
    print("Error: Could not enrich CSV data.")
    sys.exit(1)

# Export
timestamp = datetime.now().strftime("%Y%m%d_%H%M")
csv_filename = f"critical_with_weather_{timestamp}.csv"
json_filename = f"critical_with_weather_{timestamp}.json"
zip_filename = f"critical_with_weather_{timestamp}.zip"

try:
    # Save CSV
    critical_rows.to_csv(csv_filename, index=False)
    export_logger.info(f"Enriched CSV saved: {csv_filename}")
    print(f"✅ CSV saved: {csv_filename}")

    # Save JSON
    critical_rows.to_json(json_filename, orient="records", lines=True)
    export_logger.info(f"Enriched JSON saved: {json_filename}")
    print(f"✅ JSON saved: {json_filename}")

except Exception as e:
    errors_logger.exception("Error exporting CSV/JSON")
    print("Error: Could not export CSV/JSON files.")
    sys.exit(1)

# --- Zip Files ---
try:
    with zipfile.ZipFile(zip_filename, "w", zipfile.ZIP_DEFLATED) as zipf:
        zipf.write(csv_filename, arcname=os.path.basename(csv_filename))
        zipf.write(json_filename, arcname=os.path.basename(json_filename))
    export_logger.info(f"Files zipped into {zip_filename}")
    print(f"📦 Files zipped into {zip_filename}")

# Ask user if they want to delete the original files
    while True:
        user_input = input("Do you want to delete the original CSV and JSON files? (yes/no/quit): ").strip().lower()
        if user_input in ("yes", "y"):
            try:
                for f in (csv_filename, json_filename):
                    if os.path.exists(f):
                        os.remove(f)
                export_logger.info("Original CSV and JSON removed after zipping")
                print("✅ Original files deleted.")
            except OSError as e:
                errors_logger.exception("Error deleting original files")
                print(f"Error: Could not delete files ({e}).")
            break
        elif user_input in ("no", "n", "q", "quit"):
            print("❎ Original files kept.")
            break
        else:
            print("Please enter 'yes', 'no', or 'quit'.")

except (OSError, IOError, zipfile.BadZipFile) as e:
    errors_logger.exception("Error creating ZIP archive")
    print("Error: Could not create ZIP archive.")
    sys.exit(1)

logging.info("Script end")
