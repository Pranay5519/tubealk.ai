import streamlit as st
import pandas as pd
import time

# Cache data loading
@st.cache_data
def load_data():
    # Simulate slow loading
    time.sleep(3)
    df = pd.read_csv("https://raw.githubusercontent.com/mwaskom/seaborn-data/master/iris.csv")
    return df

st.write("Loading data...")
data = load_data()  # Will be cached after first run
st.dataframe(data)
