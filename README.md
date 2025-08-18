# Python Log + Weather Enricher

This project is a Python-based log parser and weather enricher, built as a demonstration of combining multiple Python libraries and functionalities into a single workflow. Its purpose is to showcase practical skills in scripting, data manipulation, API integration, error handling, and automated exporting. The script processes log files, filters for critical events, enriches them with live weather data from a public API, and exports the results in multiple formats.

# Features

- CLI Input: Accepts a CSV log file as a command-line argument.

- Critical Event Filtering: Reads logs and filters rows with level == "CRITICAL".

- Weather Enrichment: Pulls live weather data (temperature, condition) from a public API for a specified city.

- Export: Generates timestamped .csv and .json reports with enriched data.

- Zipped Output: Automatically archives the CSV and JSON reports into a single .zip file.

- Logging: Tracks script start/end, API success/failure, errors, and export operations.

# Functional Details
Command-line Interface:

Uses argparse to accept:
- csv: path to the log CSV file

- city: location for weather data

- --units: temperature units (Celsius or Fahrenheit, default F)

# Environment Variables:
Uses python-dotenv to securely load WEATHER_API_KEY from a .env file.

# CSV Processing:

- Reads input CSV using pandas.

- Filters only rows with level == "CRITICAL".

- Enriches filtered rows with weather data from API response.

# Weather API Integration:

- Requests live data from weatherapi.com or similar public API.

- Handles exceptions for missing API key, invalid JSON, request failures, and retries.

# Export & Archiving:

- Exports enriched data to timestamped CSV and JSON files (report_<timestamp>.csv / report_<timestamp>.json).

- Archives both files into a single zip (output_<timestamp>.zip) for easy delivery.

- Original CSV/JSON can optionally be deleted after zipping.

# Logging:

- Logs script operations to logs/main.log.

- Errors and exceptions are logged separately to logs/errors.log.

- Export operations are logged to logs/export.log.

# Learning Experience
 A key challenge was working with pandas to filter and enrich the data cleanly:

- Filtering CRITICAL rows and adding weather info required careful use of .copy() to avoid SettingWithCopyWarning.

- Tailoring the enrichment process ensured smooth and clean data handling.

- Managing exceptions and retrying API requests strengthened error resilience.

# This project also provided hands-on experience with:

- Handling timestamped files

- Dynamic export filenames

- Creating zip archives programmatically

- Clean and professional logging

# Try it out 
Get a weather api key
- from https://www.weatherapi.com/

Set up a virtual environment:
- python3 -m venv venv/

Activate Virtual Environment:
- source venv/bin/activate

Install dependencies:
- pip install -r requirements.txt

Try it out:
- python3 main.py logs.csv "Tokyo" --units C

Input: logs.csv (must include some CRITICAL events)

Output:   
critical_with_weather_<timestamp>.csv 
critical_with_weather_<timestamp>.json
critical_with_weather_<timestamp>.zip
