import streamlit as st
import pandas as pd
import json
import matplotlib.pyplot as plt
import seaborn as sns
import folium
from folium.plugins import HeatMap
from st_folium import st_folium

# DistrictConverter class to read district JSON file
class DistrictConverter:
    def __init__(self):
        self.districts = self.__read_district_file()

    def __read_district_file(self):
        with open('district.json', 'r', encoding='utf-8') as f:
            return json.load(f)

    def get_district_list(self):
        return self.districts.keys()

def load_data(si_do_name, start_date, end_date):
    # Load your data here
    data = pd.read_csv("your_data_file.csv")  # Change to your actual data file

    # 날짜 형식 변환
    data['date'] = pd.to_datetime(data['date'], errors='coerce')
    data.dropna(subset=['date'], inplace=True)  # NaT 제거
    data = data[(data['date'] >= start_date) & (data['date'] <= end_date)]
    
    # 지역 필터링
    data = data[data['district'] == si_do_name]

    return data

def visualize_data(data):
    # Ensure the date column is in datetime format
    data['date'] = pd.to_datetime(data['date'], errors='coerce')
    data.dropna(subset=['date'], inplace=True)

    # Monthly average prices
    monthly_avg = data.groupby(data['date'].dt.to_period('M')).mean()

    # Histogram
    plt.figure(figsize=(10, 6))
    sns.histplot(data['price'], kde=True)
    plt.title('Price Distribution')
    plt.xlabel('Price')
    plt.ylabel('Frequency')
    st.pyplot(plt)

    # Boxplot
    plt.figure(figsize=(10, 6))
    sns.boxplot(x='district', y='price', data=data)
    plt.title('Price Distribution by District')
    plt.xlabel('District')
    plt.ylabel('Price')
    st.pyplot(plt)

    # Time series graph
    plt.figure(figsize=(10, 6))
    plt.plot(monthly_avg.index.astype(str), monthly_avg['price'], marker='o')
    plt.title('Monthly Average Price')
    plt.xlabel('Month')
    plt.ylabel('Average Price')
    st.pyplot(plt)

    # Scatter plot
    plt.figure(figsize=(10, 6))
    sns.scatterplot(x='area', y='price', data=data)
    plt.title('Price vs Area')
    plt.xlabel('Area (m²)')
    plt.ylabel('Price')
    st.pyplot(plt)

    # Heatmap
    map_center = [data['latitude'].mean(), data['longitude'].mean()]
    heatmap = folium.Map(location=map_center, zoom_start=13)
    heat_data = [[row['latitude'], row['longitude'], row['price']] for index, row in data.iterrows()]
    HeatMap(heat_data).add_to(heatmap)

    st_folium(heatmap)

# Streamlit app layout
st.title("Real Estate Data Analysis")
district_converter = DistrictConverter()
district_list = district_converter.get_district_list()

si_do_name = st.selectbox("Select District", district_list)
start_date = st.date_input("Start Date")
end_date = st.date_input("End Date")

if st.button("Load Data"):
    data = load_data(si_do_name, start_date, end_date)

    if data.empty:
        st.error("No data found for the selected criteria.")
    else:
        # Display the data in a table with proper width
        table_width = 800  # Adjust width as necessary
        st.dataframe(data.style.set_properties(**{'text-align': 'left'}), width=table_width)

        # Call the visualization function
        visualize_data(data)

        # Display additional information
        st.markdown(f"**Current District:** {si_do_name}")
        st.markdown(f"**Progress:** {len(data)} records loaded.")
        progress_percentage = min(len(data) / 100, 1.0)  # Adjust as necessary for actual progress
        st.progress(progress_percentage)
