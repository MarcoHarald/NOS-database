import os
import pandas as pd
from supabase import create_client, Client
from dotenv import load_dotenv
load_dotenv()

# Initialize Supabase client
url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_KEY")
supabase: Client = create_client(url, key)

# Function to create a table
def create_table():
    supabase.table("users").create_table(
        columns=[
            {"name": "id", "type": "int8", "primary_key": True, "auto_increment": True},
            {"name": "username", "type": "text", "unique": True},
            {"name": "email", "type": "text", "unique": True},
            {"name": "phone_number", "type": "text"},
            {"name": "city", "type": "text"},
            {"name": "events", "type": "text[]"}
        ]
    )

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
        existing_user  = supabase.table("users").select("*").eq("email", email).execute()

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


# Sample usage
if __name__ == "__main__":
    # Uncomment the line below to create the table initially
    # create_table()

    # Sample CSV file path
    csv_file_path = 'path-to-your-csv-file.csv'
    
    # Load data from CSV
    df = pd.read_csv('sampleData1.csv')
    
    # Import data into Supabase
    import_data(df)
