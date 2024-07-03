# streamlit dashboard to manage database

import streamlit as st
import pandas as pd
from supabase import create_client, Client
from st_aggrid import AgGrid, GridOptionsBuilder
from st_aggrid.shared import GridUpdateMode
from io import BytesIO
import os
from dotenv import load_dotenv
load_dotenv()

# Initialize Supabase client
url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_KEY")
supabase: Client = create_client(url, key)

# Load data from Supabase
@st.cache_data(ttl=60)
def load_data():
    response = supabase.table('users').select('*').execute()
    return pd.DataFrame(response.data)

def update_data(data):
    for index, row in data.iterrows():
        supabase.table('users').update(row.to_dict()).eq('id', row['id']).execute()

# Page 1: View, Filter, Edit, and Download Data
def page_one():
    st.title("Manage Users Data")
    
    # Load data
    data = load_data()

    # Filter options
    st.sidebar.subheader('Filter Data')
    filter_city = st.sidebar.text_input('City')
    filter_event = st.sidebar.text_input('Event')

    if filter_city:
        data = data[data['address_city'].str.contains(filter_city, case=False, na=False)]
    
    if filter_event:
        data = data[data['tags'].apply(lambda x: filter_event in x)]

    # Editable data grid
    st.subheader("User Data")
    gb = GridOptionsBuilder.from_dataframe(data)
    gb.configure_pagination()
    gb.configure_default_column(editable=True)
    grid_options = gb.build()

    grid_response = AgGrid(
        data,
        gridOptions=grid_options,
        update_mode=GridUpdateMode.MODEL_CHANGED,
        allow_unsafe_jscode=True
    )

    updated_data = grid_response['data']
    selected_rows = grid_response['selected_rows']

    if st.button('Update Data'):
        update_data(pd.DataFrame(updated_data))
        st.success('Data updated successfully!')

    # Download data
    st.subheader("Download Data")
    csv_data = data.to_csv(index=False).encode()
    st.download_button(
        label="Download as CSV",
        data=csv_data,
        file_name='user_data.csv',
        mime='text/csv'
    )

# Page 2: Key Statistics
def page_two():
    st.title("User Statistics")
    
    data = load_data()

    st.subheader("Total Number of Users")
    total_users = data.shape[0]
    st.write(total_users)

    st.subheader("Number of Users with Phone Numbers")
    users_with_phones = data['phone_number'].dropna().nunique()
    st.write(users_with_phones)

    st.subheader("Most Popular Cities")
    popular_cities = data['address_city'].value_counts().head(10)
    st.write(popular_cities)

    st.subheader("Most Popular Tags")
    all_tags = data['tags'].explode().value_counts().head(10)
    st.write(all_tags)

# Sidebar Navigation
st.sidebar.title("Navigation")
page = st.sidebar.radio("Go to", ["Manage Data", "View Statistics"])

if page == "Manage Data":
    page_one()
else:
    page_two()
