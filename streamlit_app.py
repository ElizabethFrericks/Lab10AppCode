import streamlit as st
import pandas as pd
import folium
from folium.plugins import MarkerCluster
from streamlit_folium import st_folium
import matplotlib.pyplot as plt

st.set_page_config(layout="wide")

st.title("Water Quality Analysis Dashboard")

# File uploaders
st.sidebar.header("Upload Data Files")
station_file = st.sidebar.file_uploader("Upload Station Data (CSV)", type=["csv"])
result_file = st.sidebar.file_uploader("Upload Water Quality Results (CSV)", type=["csv"])

if station_file and result_file:
    # Load files
    station_df = pd.read_csv(station_file)
    result_df = pd.read_csv(result_file)

    # Filter out invalid values
    result_df = result_df[result_df['CharacteristicName'].apply(lambda x: isinstance(x, str))]

    # Convert columns
    result_df['ActivityStartDate'] = pd.to_datetime(result_df['ActivityStartDate'], errors='coerce')
    result_df['ResultMeasureValue'] = pd.to_numeric(result_df['ResultMeasureValue'], errors='coerce')
    result_df = result_df.dropna(subset=['ActivityStartDate', 'ResultMeasureValue'])

    # Select contaminant
    st.sidebar.header("Filter Options")
    contaminants = sorted(result_df['CharacteristicName'].dropna().unique())
    selected_contaminant = st.sidebar.selectbox("Select a Contaminant", contaminants)

    # Filter for selected contaminant
    filtered_df = result_df[result_df['CharacteristicName'] == selected_contaminant]

    # Date range selector
    min_date = filtered_df['ActivityStartDate'].min()
    max_date = filtered_df['ActivityStartDate'].max()
    date_range = st.sidebar.date_input("Select Date Range", [min_date, max_date], min_value=min_date, max_value=max_date)

    # Value range selector
    min_value = float(filtered_df['ResultMeasureValue'].min())
    max_value = float(filtered_df['ResultMeasureValue'].max())
    value_range = st.sidebar.slider("Select Value Range", min_value, max_value, (min_value, max_value))

    # Apply all filters
    filtered_df = filtered_df[(filtered_df['ActivityStartDate'] >= pd.to_datetime(date_range[0])) &
                               (filtered_df['ActivityStartDate'] <= pd.to_datetime(date_range[1])) &
                               (filtered_df['ResultMeasureValue'] >= value_range[0]) &
                               (filtered_df['ResultMeasureValue'] <= value_range[1])]

    # Merge with station data
    merged_df = pd.merge(filtered_df, station_df, on='MonitoringLocationIdentifier', how='inner')
    merged_df = merged_df.dropna(subset=['LatitudeMeasure', 'LongitudeMeasure'])

    # Map section
    st.subheader("Station Locations")
    if not merged_df.empty:
        m = folium.Map(location=[merged_df['LatitudeMeasure'].mean(), merged_df['LongitudeMeasure'].mean()], zoom_start=7)
        marker_cluster = MarkerCluster().add_to(m)
        for _, row in merged_df.iterrows():
            folium.Marker(
                location=[row['LatitudeMeasure'], row['LongitudeMeasure']],
                popup=f"{row['MonitoringLocationName']}<br>{selected_contaminant}: {row['ResultMeasureValue']}",
                tooltip=row['MonitoringLocationName']
            ).add_to(marker_cluster)
        st_data = st_folium(m, width=1200)
    else:
        st.warning("No data matches your filters.")

    # Trend section
    st.subheader("Contaminant Trend Over Time")
    if not merged_df.empty:
        fig, ax = plt.subplots(figsize=(12, 6))
        for site, group in merged_df.groupby('MonitoringLocationIdentifier'):
            group = group.sort_values('ActivityStartDate')
            ax.plot(group['ActivityStartDate'], group['ResultMeasureValue'], label=site)
        ax.set_title(f"{selected_contaminant} Levels Over Time")
        ax.set_xlabel("Date")
        ax.set_ylabel("Measured Value")
        ax.legend(title="Station", bbox_to_anchor=(1.05, 1), loc='upper left')
        ax.grid(True)
        st.pyplot(fig)
else:
    st.info("Please upload both data files to begin.")

