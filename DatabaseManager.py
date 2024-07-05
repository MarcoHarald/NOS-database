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
    response = supabase.table('user_data').select('*').execute()
    return pd.DataFrame(response.data)

def update_data(data):
    for index, row in data.iterrows():
        supabase.table('user_data').update(row.to_dict()).eq('id', row['id']).execute()

def upload_data(df):
    for index, row in df.iterrows():
        email = row['email']
        tag_list = row['tag_list'].split(',') if 'tag_list' in row else []
        
        # Check if user already exists
        existing_user = supabase.table('user_data').select('*').eq('email', email).execute()
        
        if existing_user.data:
            # User exists, update their tag_list
            user_id = existing_user.data[0]['id']
            current_tag_list = existing_user.data[0]['tag_list']
            updated_tag_list = list(set(current_tag_list + tag_list))
            supabase.table('user_data').update({'tag_list': updated_tag_list}).eq('id', user_id).execute()
        else:
            # User does not exist, insert new record
            new_user = row.to_dict()
            #new_user['tag_list'] = tag_list
            supabase.table('user_data').insert(new_user).execute()

# Page 1: View, Filter, Edit, and Download Data
def page_one():
    st.title("Manage Users Data")
    
    # Load data
    data = load_data()

    # Filter options
    st.sidebar.subheader('Filter Data')
    filter_city = st.sidebar.text_input('City')
    filter_tag = st.sidebar.text_input('Tag')

    if filter_city:
        data = data[data['address_city'].str.contains(filter_city, case=False, na=False)]
    
    if filter_tag:
        data = data[data['tag_list'].apply(lambda x: filter_tag in x)]

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
    all_tags = data['tag_list'].explode().value_counts().head(10)
    st.write(all_tags)

# Page 3: Upload CSV and Match Columns
def page_three():
    st.title("Upload CSV Data")

    uploaded_file = st.file_uploader("Choose a CSV file", type="csv")
    if uploaded_file is not None:
        df = pd.read_csv(uploaded_file)
        st.subheader("Uploaded Data")
        st.write(df.head())

        # Match columns
        st.subheader("Match Columns")
        supabase_columns = ['first_name','last_name', 'email', 'phone_number', 'address_city', 'tag_list']
        
        column_mapping = {}
        selected_columns = []
        
        for csv_column in df.columns:
            selected_column = st.selectbox(f'Match {csv_column}', [''] + supabase_columns)

            if selected_column:
                column_mapping[csv_column] = selected_column
                selected_columns.append(selected_column)
        
        # Rename & filter columns based on the mapping
        df.rename(columns=column_mapping, inplace=True)
        df = df[selected_columns]
        st.subheader("Selected Data")
        st.write(df.head())

        if st.button('Upload Data'):
            upload_data(df[selected_columns])
            st.success('Data uploaded successfully!')

# Sidebar Navigation
st.sidebar.title("Navigation")
page = st.sidebar.radio("Go to", ["Manage Data", "View Statistics", "Upload CSV"])

if page == "Manage Data":
    page_one()
elif page == "View Statistics":
    page_two()
else:
    page_three()
 