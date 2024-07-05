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
#@st.cache_data(ttl=60)
def load_data(supabase_table):
    response = supabase.table(supabase_table).select('*').execute()
    return pd.DataFrame(response.data)

def update_data(data, supabase_table_name):
    for index, row in data.iterrows():
        #DEBUG
        st.write('updating:', index, row)
        supabase.table(supabase_table_name).update(row.to_dict()).eq('nationbuilder_id', row['nationbuilder_id']).execute()

def update_user(existing_user, new_data_on_user):
    row = new_data_on_user

    # For a given user, update their tag_list
    user_id = existing_user.data[0]['nationbuilder_id']
    current_tag_list = existing_user.data[0]['tag_list']

    # if new tags are being added, process them:
    tag_list = row['tag_list'] if 'tag_list' in row else []
    if tag_list:

        # Merge tags. Else if no prior tags, simply overwrite
        if current_tag_list:
            updated_tag_list = current_tag_list.split(',') + tag_list.split(',')

        else:
            updated_tag_list = tag_list.split(',')

        # Remove spaces, only keep unique values, format list into human friendly string. 
        updated_tag_list = [x.strip() for x in updated_tag_list]
        updated_tag_list = list(set(updated_tag_list))
        updated_tag_list = ', '.join(str(x) for x in updated_tag_list)
        new_data_on_user.data[0]['tag_list'] = updated_tag_list
    
    supabase.table(supabase_table).update(new_data_on_user.to_dict()).eq('nationbuilder_id', user_id).execute()
    return existing_user.data[0]

def upload_data(df, supabase_table):

    # List of rows that failed to upload. Shared as a report after. 
    error_list = []

    for index, row in df.iterrows():
        
     # search & match user by email
        try:
            # Check if user already exists
            existing_user = supabase.table(supabase_table).select('*').eq('email', row['email']).execute()
          
            if existing_user.data:
                update_user(existing_user, row)
                         
            else:
                # User does not exist, insert new record
                new_user = row.to_dict()
                supabase.table(supabase_table).insert(new_user).execute()

            
            

     # if no email, search & match user by phone number
        except:  
            try:
                # Check if user already exists
                existing_user = supabase.table(supabase_table).select('*').eq('phone_number', row['phone_number']).execute()
                if existing_user.data:
                    update_user(existing_user, row)
                            
                else:
                    # User does not exist, insert new record
                    new_user = row.to_dict()
                    supabase.table(supabase_table).insert(new_user).execute()
            
     # neither email, nor phone number, show error
            except: 
                error_list += [row]

     # display all the rows that had import errors
    if error_list:
        st.title('(!) error uploading')
        st.write('Some of your data was not uploaded. Every line needs either an email or phone number. Please check & re-upload.')
        st.dataframe(error_list)




# Page 1: View, Filter, Edit, and Download Data
def page_one(supabase_table):
    st.title("Manage User's Data")
    
    # Load data
    data = load_data(supabase_table)

    # Create three buttons in three columns side by side
    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button("Filter"):
            st.write("Choose your filters...")

    with col2:
        if st.button("Update data"):
            st.write("Your edits have been imported")

    with col3:
        if st.button("Download"):
            st.write("Downloading with filters...")


    # Filter options
    st.sidebar.subheader('Filter Data')
    filter_firstname = st.sidebar.text_input('First name')
    filter_lastname = st.sidebar.text_input('Last name')
    filter_city = st.sidebar.text_input('City')
    filter_tag = st.sidebar.text_input('Tag')

    if filter_firstname:
        data = data[data['first_name'].str.contains(filter_firstname, case=False, na=False)]

    if filter_lastname:
        data = data[data['last_name'].str.contains(filter_lastname, case=False, na=False)]

    if filter_city:
        data = data[data['address_city'].str.contains(filter_city, case=False, na=False)]
    
    if filter_tag:
        data = data[data['tag_list'].apply(lambda x: filter_tag in x)]

    # Editable data grid
    #st.subheader("User Data")
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

        update_data(pd.DataFrame(updated_data), supabase_table)
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
def page_two(supabase_table):
    st.title("User Statistics")
    
    data = load_data(supabase_table)

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
    
    # tags cleanly separated. Useful for reference and use.
    all_tags_separated = data['tag_list'].str.split(',')

    # frequency of tags. For combinations of tags remove [str.split()]
    all_tags = data['tag_list'].str.split(', ').explode().value_counts()
    st.write(all_tags)


# Page 3: Upload CSV and Match Columns
def page_three(supabase_table):
    st.title("Upload CSV Data")

    uploaded_file = st.file_uploader("Choose a CSV file", type="csv")
    if uploaded_file is not None:
        df = pd.read_csv(uploaded_file)
        st.subheader("1. Upload Data")
        st.write('Here is the file you uploaded:')
        st.write(df.head())
        st.write('')

        # Match columns
        st.subheader("2. Match Columns")
        supabase_columns = ['first_name','last_name', 'email', 'phone_number', 'address_city', 'tag_list']
        
        column_mapping = {}
        selected_columns = []
        
        for csv_column in df.columns:
            selected_column = st.selectbox(f'Match:   {csv_column}', [''] + supabase_columns)

            if selected_column:
                column_mapping[csv_column] = selected_column
                selected_columns.append(selected_column)
        
        # Rename & filter columns based on the mapping
        df.rename(columns=column_mapping, inplace=True)
        df = df[selected_columns]
        st.subheader("3. Review & Send to Database")
        st.write(df.head())

        if st.button('Upload Data'):
            upload_data(df[selected_columns],supabase_table)
            st.success('Data uploaded successfully!')

        

# Sidebar Navigation
st.sidebar.title("Navigation")
page = st.sidebar.radio("Go to", ["Manage Database", "Key Stats", "Import Data"])

supabase_table = 'db_2'

if page == "Manage Database":
    page_one(supabase_table)
elif page == "Key Stats":
    page_two(supabase_table)
elif page == "Import Data":
    page_three(supabase_table)
else:
    st.subtitle('Select a page')
