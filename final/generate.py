from csv import Sniffer
import os
from calendar import month_name
from datetime import date

from requests import HTTPError, Session
from tqdm import tqdm
import sys

SKIP_DOWNLOAD = sys.argv[1] == "nodl"

def download():
    MONTHS = []
    TARGET_MONTH = date.today().month - 1

    for i in range(1, TARGET_MONTH): # aware that this will be 2 months behind today, that is the goal.
        MONTHS.append(month_name[i].lower())

    session = Session()
    session.headers.update({
        'User-Agent': "Mozilla/5.0 (X11; Linux x86_64; rv:109.0) Gecko/20100101 Firefox/118.0"
    })

    print("Downloading data... please wait. These files are **large**.")
    for month in MONTHS:
        response = session.get(f"https://live.mybirdbuddy.com/metadata/all_metadata_{month}.csv", stream=True)
        total_size_in_bytes= int(response.headers.get('content-length', 0))
        block_size = 1024 #1 Kibibyte
        try:
            response.raise_for_status()
            print(f"{month}...")
            progress_bar = tqdm(total=total_size_in_bytes, unit='iB', unit_scale=True)
        except HTTPError as e:
            print(f"Error fetching data for {month}")
            print(e)
            continue

        with open(f"inputs/{month}.csv", "wb") as f:
            for data in response.iter_content(block_size):
                progress_bar.update(len(data))
                f.write(data)
            progress_bar.close()
            print(f"Saved to inputs/{month}.csv")


def detect_delimiter(file_path):
    with open(file_path, 'r', newline='') as file:
        line = file.readline()
        dialect = Sniffer().sniff(line)
        return dialect.delimiter


def combine():
    import pandas as pd

    try:
        csv_files = [f for f in os.listdir('inputs') if f.endswith('.csv')]
        output = None

        for csv_file in csv_files:
            csv_path = os.path.join('inputs', csv_file)
            print(f'Reading data from {csv_path}')

            try:
                delim = detect_delimiter(csv_path)
                print(f'Detected delimiter: {delim}')
                for chunk in pd.read_csv(csv_path, delimiter=delim, chunksize=100_000_000):
                    if output is None:
                        output = chunk
                    else:
                        output = pd.concat([output, chunk], ignore_index=True)

            except pd.errors.ParserError as e:
                print(f'Error while parsing {csv_path}: {str(e)}')

        output.to_csv('data.csv', index=False)
        print(f'Combined data saved to data.csv')

    except Exception as ex:
        print(f'An error occurred: {str(ex)}')

if not SKIP_DOWNLOAD:
    download()

combine()

    
    