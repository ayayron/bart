import altair
import pandas as pd
import pydeck

import streamlit as st

from .bart import get_stations

def get_daily_plot(df: pd.DataFrame):
    df_ty = df.loc[df['Year'] == 2020]
    df_ly = df.loc[df['Year'] == 2019]
    field = 'Count'
    data_ty = df_ty.groupby('Date')[field].sum().reset_index()
    data_ty['Date'] = pd.to_datetime(data_ty['Date'])
    data_ty = data_ty.set_index('Date')
    data_ly = df_ly.groupby('Date')[field].sum().reset_index()
    data_ly['Date'] = pd.to_datetime(data_ly['Date']) + pd.offsets.DateOffset(years=1)
    data_ly = data_ly.set_index('Date')

    merged_data = pd.merge(
        data_ly, data_ty, how='left', left_index=True, right_index=True, suffixes=("_2019", "_2020"))

    data = pd.melt(merged_data.reset_index(), 
        id_vars='Date', value_vars=[f'{field}_2019', f'{field}_2020'])

    data = data.replace({f'{field}_2019': '2019', f'{field}_2020': '2020'})
    return st.altair_chart(altair.Chart(data).mark_line().encode(
        x='Date:T',
        y='value',
        color='variable'
    ), use_container_width=True)

def in_out_yoy_scatter(df_ty: pd.DataFrame, df_ly: pd.DataFrame):
    field = 'Revenue'
    df_ty = df_ty.loc[df_ty['Date'] > '2020-03-01']
    data_ty = df_ty.groupby(['In', 'Out'])[field].sum().reset_index()
    data_ly = df_ly.groupby(['In', 'Out'])[field].sum().reset_index()

    merged_data = pd.merge(
        data_ly, data_ty, how='left', left_index=True, right_index=True, suffixes=("_2019", "_2020"))

    data = merged_data.drop(['In_2019', 'Out_2019'], axis=1).dropna()
    return altair.Chart(data).mark_circle(size=10).encode(
        x='Revenue_2019:Q',
        y='Revenue_2020:Q',
        tooltip=['In_2020', 'Out_2020', 'Revenue_2019', 'Revenue_2020']
    ).transform_filter(
        altair.FieldGTPredicate(field='Revenue_2019', gt=0))



def get_in_out_yoy_data(df: pd.DataFrame):
    df_ty = df.loc[df['Year'] == 2020]
    df_ly = df.loc[df['Year'] == 2019]
    field = 'Revenue'
    # df_ty = df_ty.loc[df_ty['Date'] > '2020-03-01']
    data_ty = df_ty.groupby(['In', 'Out'])[field].sum().reset_index()
    data_ly = df_ly.groupby(['In', 'Out'])[field].sum().reset_index()

    merged_data = pd.merge(
        data_ly, data_ty, how='left', left_index=True, right_index=True, suffixes=("_2019", "_2020"))

    data = merged_data.drop(['In_2019', 'Out_2019'], axis=1).dropna()
    data = data.loc[(data['Revenue_2019'] > 0) & (data['Revenue_2020'] > 0)]
    average_diff = data['Revenue_2020'].sum() / data['Revenue_2019'].sum()
    data['Ratio'] = 100 * (data['Revenue_2020'] / data['Revenue_2019'] - average_diff)
    return data

def in_out_yoy_map(df: pd.DataFrame):
    data = get_in_out_yoy_data(df)
    station_lat_lng = {s.abbr: (s.lat, s.lon) for s in get_stations()}
    data['in_lat'] = data.apply(lambda row: station_lat_lng[row['In_2020']][0], axis=1)
    data['in_lon'] = data.apply(lambda row: station_lat_lng[row['In_2020']][1], axis=1)
    data['out_lat'] = data.apply(lambda row: station_lat_lng[row['Out_2020']][0], axis=1)
    data['out_lon'] = data.apply(lambda row: station_lat_lng[row['Out_2020']][1], axis=1)

    breakpoint()
    COLOR_BREWER_BLUE_SCALE = [
        [240, 249, 232],
        [204, 235, 197],
        [168, 221, 181],
        [123, 204, 196],
        [67, 162, 202],
        [8, 104, 172],
    ]

    data_layer = pydeck.Layer(
        "HeatmapLayer",
        data=data,
        opacity=0.9,
        get_position=["in_lon", "in_lat"],
        color_range=COLOR_BREWER_BLUE_SCALE,
        aggregation='"MAX"',
        get_weight="Ratio",
        pickable=True,    
    )

    DATA_URL = "https://raw.githubusercontent.com/uber-common/deck.gl-data/master/website/bart-lines.json"
    routes = pd.read_json(DATA_URL)

    def hex_to_rgb(h):
        h = h.lstrip("#")
        return tuple(int(h[i : i + 2], 16) for i in (0, 2, 4))

    routes["color"] = routes["color"].apply(hex_to_rgb)


    route_layer = pydeck.Layer(
        type="PathLayer",
        data=routes,
        pickable=True,
        get_color="color",
        width_scale=20,
        width_min_pixels=2,
        get_path="path",
        get_width=5,
    )

    return st.pydeck_chart(
        pydeck.Deck(
            map_style="mapbox://styles/mapbox/light-v9",
            initial_view_state=pydeck.ViewState(
                        latitude=37.76, longitude=-122.4, zoom=11, bearing=0, pitch=0
                    ),
            layers=[data_layer],   
    ))


def in_out_yoy_heatmap(df: pd.DataFrame):
    return     st.altair_chart(altair.Chart(get_in_out_yoy_data(df)).mark_rect().encode(
        x='Out_2020:O',
        y='In_2020:O',
        color=altair.Color('Ratio:Q', scale=altair.Scale(scheme='blueorange')),
        tooltip=['In_2020', 'Out_2020', 'Ratio', 'Revenue_2020']
    ).interactive()
    ,use_container_width=True)


def in_out_heatmap(df: pd.DataFrame):
    data = df.groupby(['In', 'Out'])['Revenue'].sum().reset_index()
    return altair.Chart(data).mark_rect().encode(
        x='Out:O',
        y='In:O',
        color='Revenue:Q',
        tooltip=['In', 'Out', 'Revenue']
    ).interactive()
