import os
import requests
from typing import List

import pandas as pd

URL = 'http://64.111.127.166/origin-destination/'
FILENAME = 'date-hour-soo-dest-{}.csv.gz'
ALL_FILE = 'od_count_all_time.feather'
DATA_DIR = './data/'

ALL_FILE_PATH = os.path.join(DATA_DIR, ALL_FILE)

def download_files():
    dataframes = []
    for year in range(2016, 2021):
        file_year = FILENAME.format(year)
        filename = os.path.join(DATA_DIR, file_year)
        if file_year not in os.listdir(DATA_DIR):
            print(f'Getting file {file_year}')
            resp = requests.get(URL + file_year)
            with open(filename, 'wb') as f:
                f.write(resp.content)
        
        df = pd.read_csv(filename)
        df.columns = ['Date', 'Hour', 'In', 'Out', 'Count']
        df.index = pd.DatetimeIndex(df['Date'])
        df['Year'] = df.index.year
        df['Month'] = df.index.month
        df['Day'] = df.index.day
        df['DOW'] = df.index.weekday
        df = df.drop('Date', axis=1)
        df = df.reset_index()
        df = df.drop('Date', axis=1)
        dataframes.append(df)
    
    all_df = pd.concat(dataframes)
    all_df.reset_index().to_feather(ALL_FILE_PATH)

def aggregate(prefix: str, groupings: List, fields: List):
    filename = f"aggregate_{prefix}_{'-'.join(groupings).replace(' ', '')}.feather"
    agg_file = os.path.join(DATA_DIR, filename)
    if filename not in os.listdir(DATA_DIR):
        print(f'Creating {filename}')
        all_df = pd.read_feather(ALL_FILE_PATH)
        agg_df = all_df.groupby(groupings)[fields].sum().reset_index()
        agg_df.reset_index().to_feather(agg_file)

if __name__ == "__main__":
    if ALL_FILE not in os.listdir(DATA_DIR):
        print('Downloading data...')
        download_files()
        print(f'All file written to {ALL_FILE}')
    aggregate('od', ['Year', 'Month', 'Day'], ['Count'])
    aggregate('od', ['Year', 'In', 'Out'], ['Count'])
