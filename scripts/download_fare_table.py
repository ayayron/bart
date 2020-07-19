
import pandas

from bart.bart import Fares, get_stations

def get_fare_table():
    stations_abbr = [s.abbr for s in get_stations()]
    station_pairs = []
    for o in stations_abbr:
        for d in stations_abbr:
            if o != d:
                station_pairs.append((o, d))
    fares = Fares()
    fares.get_fares(station_pairs)

    df = pandas.DataFrame.from_dict(fares.fare_pairs, orient="index")
    index = pandas.MultiIndex.from_tuples(fares.fare_pairs, names = ['Origin', 'Destination'])
    df.index = index
    df.columns = ['Fares']
    df.to_csv('./data/fares.csv')


if __name__ == "__main__":
    get_fare_table()
