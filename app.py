from dataclasses import dataclass
from enum import Enum
import os

import streamlit as st
import pandas as pd

import bart.bart as bart
import bart.plot as plot

FILEPATH = './data/date-hour-soo-dest-{}.csv.gz'
TMP_FILE_DIR = "./data"

class Aggregates(Enum):
    ymd = 'aggregate_od_Year-Month-Day.feather'
    inout = 'aggregate_od_Year-In-Out.feather'

    def __str__(self):
        return self.value


@st.cache
def load_data(agg_type: Aggregates):
    with st.spinner("Loading data..."):
        df = pd.read_feather(os.path.join(TMP_FILE_DIR, str(agg_type)))
        if {'Year', 'Month', 'Day'}.issubset(set(df.columns)):
            df['Date'] = df.apply(
                lambda row: f"{row['Year']}-{str(row['Month']).zfill(2)}-{str(row['Day']).zfill(2)}"
                , axis=1)
        
        if {'In', 'Out'}.issubset(set(df.columns)):
            fares = load_fares()
            df = pd.merge(df, fares, how='left', left_on=['In', 'Out'], right_on=['Origin', 'Destination'])
            df['Revenue'] = df['Count'] * df['Fares']
            df['Revenue'] = df['Revenue'].fillna(0)
        return df

@st.cache
def load_fares():
    return pd.read_csv(TMP_FILE_DIR + '/fares.csv')

@dataclass(frozen=True)
class SidebarSelection:
    analysis_type: str
    origin: str
    destination: str
    hour: int

def generate_sidebar() -> SidebarSelection:
    selected_analysis = st.sidebar.radio('Analyses', options=['Summary', 'By Station'])
    stations = [None, *[s.name for s in bart.get_stations()]]
    origin = st.sidebar.selectbox('Origin', options=stations)
    destination = st.sidebar.selectbox('Destination', options=stations)
    hour = st.sidebar.slider('Hours', 0, 23, 9)
    return SidebarSelection(
        analysis_type=selected_analysis, origin=origin, destination=destination,
        hour=hour)


def run():
    st.title("BART Financials")
    sb = generate_sidebar()
    st.subheader(sb.analysis_type)
    if sb.analysis_type == 'Summary':
        ymd_data = load_data(Aggregates.ymd)
        plot.get_daily_plot(ymd_data)
        
    if sb.analysis_type == 'By Station':
        inout_data = load_data(Aggregates.inout)
        plot.in_out_yoy_heatmap(inout_data)
        plot.in_out_yoy_map(inout_data)


if __name__ == "__main__":
    run()