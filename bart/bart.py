from dataclasses import dataclass
import requests
import time
from typing import Dict, List

import json

import streamlit as st

from .config import API_TOKEN

API_URL = 'https://api.bart.gov/api/{}.aspx'

@dataclass(frozen=True)
class Station:
    name: str
    abbr: str
    lat: float
    lon: float
    address: str
    city: str
    county: str
    state: str
    zipcode: str
     

class Stations:
    def __init__(self, stations):
        self.stations = stations



def make_request(path, cmd, params=None) -> Dict:
    default_params = {'cmd': cmd, 'key': API_TOKEN, 'json': 'y'}
    params = {**params, **default_params} if params else default_params
    response = requests.get(
        API_URL.format(path),
        params=params)
    return json.loads(response.text)

@st.cache
def get_stations() -> List[Station]:
    stations = make_request('stn', 'stns')['root']['stations']['station']
    return [get_station(s) for s in stations]


def get_station(s: Dict) -> Station:
    return Station(
        name=s['name'], abbr=s['abbr'], lat=s['gtfs_latitude'],
        lon=s['gtfs_longitude'], address=s['address'], city=s['city'],
        county=s['county'], state=s['state'], zipcode=s['zipcode'])



class Fares:
    def __init__(self):
        self.fare_pairs = dict()
        
    def get_fare(self, in_station, out_station):
        if (in_station, out_station) not in self.fare_pairs:
            if len(self.fare_pairs.values()) % 50 == 0:
                print(len(self.fare_pairs.values()))
            response = make_request(
                'sched', 'fare', {'orig': in_station.lower(), 'dest':out_station.lower()})

            self.fare_pairs[(in_station, out_station)] = float(response['root']['trip']['fare'])
            self.fare_pairs[(out_station, in_station)] = float(response['root']['trip']['fare'])
        return self.fare_pairs[(in_station, out_station)]

    def get_fares(self, pairs):
        return [self.get_fare(*p) for p in pairs]
