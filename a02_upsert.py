import os
import json
import pandas as pd
from supabase import create_client, Client
from dotenv import load_dotenv
load_dotenv()

# Initialize Supabase client
url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_KEY")
supabase: Client = create_client(url, key)


# Function to check if user exists and append tags if so
def import_data(df: pd.DataFrame):
    for index, row in df.iterrows():
        first_name = row['first_name']
        last_name = row['last_name']
        email = row['email']
        phone_number = row['phone_number']
        address_city = row['address_city']
        tags = row['tags'] # when not defined as an array use:  .split(',') 

        # Check if user already exists inside table
        existing_user  = supabase.table("users").select("*").eq("first_name", first_name).execute()

        if existing_user.data:
            # User exists, update their tags
            user_id = existing_user.data[0]['id']
            current_tags = existing_user.data[0]['tags']

            try:
                current_tags = current_tags+", "+tags # if user has existing tags
            except:
                current_tags = tags # if user has no tags

            updated_tags = current_tags

            supabase.table('users').update({'tags': updated_tags}).eq('id', user_id).execute()

            # DEBUG
            print('Updating tags for', user_id, email)

        else:
            # User does not exist, insert new record
            new_user = {
                "first_name": first_name,
                "last_name": last_name,
                "email": email,
                "phone_number": phone_number,
                "address_city": address_city,
                "tags": tags
            }
            supabase.table('users').insert(new_user).execute()

            # DEBUG
            print('Creating new user', email)

def uploadData(df):
    data = supabase.table("users").upsert(df).execute() # , on_conflict='email'
    print(data)
  

# Sample usage
if __name__ == "__main__":

    # Load data from CSV
    csv_file_path = 'sampleData1.csv'
    df = pd.read_csv(csv_file_path) # readin data
    df_json = df.to_json(orient='records')  # upsert requires JSON format
    df_json = json.loads(df_json) # convert to list

    # Import data into Supabase
    response = supabase.table('users').upsert(df_json, on_conflict='email').execute() # ,
    print('Response', response)
