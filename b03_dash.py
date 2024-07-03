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
        events = row['tag_list'].split(',') if 'tag_list' in row else []
        
        # Check if user already exists
        existing_user = supabase.table('user_data').select('*').eq('email', email).execute()
        
        if existing_user.data:
            # User exists, update their events
            user_id = existing_user.data[0]['id']
            current_events = existing_user.data[0]['tag_list']
            updated_events = list(set(current_events + events))
            supabase.table('user_data').update({'tag_list': updated_events}).eq('id', user_id).execute()
        else:
            # User does not exist, insert new record
            new_user = row.to_dict()
            new_user['tag_list'] = events
            supabase.table('user_data').insert(new_user).execute()

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
        data = data[data['city'].str.contains(filter_city, case=False, na=False)]
    
    if filter_event:
        data = data[data['tag_list'].apply(lambda x: filter_event in x)]

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
    popular_cities = data['city'].value_counts().head(10)
    st.write(popular_cities)

    st.subheader("Most Popular Events Attended")
    all_events = data['tag_list'].explode().value_counts().head(10)
    st.write(all_events)

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
        supabase_columns = ['','first_name', 'last_name', 'email', 'phone_number', 'address_city', 'tag_list','address_country']
        csv_columns = df.columns.tolist()

        # for each Supabase column, match a column from the file
#        column_mapping = {}
#        for column in supabase_columns:
#            column_mapping[column] = st.selectbox(f'Match {column}', csv_columns)

        # for each file column, match the relevant Supabase column
        column_mapping = {}
        for column in csv_columns:
            column_mapping[column] = st.selectbox(f'Match {column}', supabase_columns)

        # Swap values in dictionary to get the supabase column names. Exclude blanks.
        column_mapping_2 = {} # swap index of dictionary
        for column in column_mapping.items():
            if(column[1] == ''): # if the column was left blank, remove it from the dictionary
                # column_mapping.pop(column[0], None)
                st.write('popping', column[0])

            else: # map chosen columns
                column_mapping_2[column[1]] = column[0]

        # DEBUG
        st.write(column_mapping)
        st.write(column_mapping_2)
        st.write('...............')
        st.write(column_mapping_2.keys())
        st.write(df.head())


        # Rename columns based on the mapping
        df.rename(columns=column_mapping_2, inplace=True)
        df2 = df[column_mapping_2.keys()]
        st.write(df.head())
        st.write(df2.head())

        if st.button('Upload Data'):
            upload_data(df)
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
