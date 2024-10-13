# Gemini XML Parser

A Python script for parsing product data from a Gemini XML feed and exporting the results to a CSV file.

## Features

- Fetches product data from a specified Gemini XML URL.
- Parses product details including price, availability, images, and more.
- Excludes specified product codes from the output.
- Allows customization of price calculation through a configurable multiplier.
- Outputs the parsed data to a CSV file.

## Requirements

To run this project, you need to install the following Python packages:

- `requests`
- `beautifulsoup4`
- `tqdm`


```bash
pip install -r requirements.txt
