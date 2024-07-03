from dotenv import load_dotenv
load_dotenv()

import os
from supabase import create_client
# from gotrue.exceptions import APIError

url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_KEY")
supabase= create_client(url, key)


def login(users_email, users_password):
    # LOGIN an existing user
    session = None
    try:
        session = supabase.auth.sign_in_with_password({ "email": users_email, "password": users_password })
    except:
        print("Login failed. Check credentials.")

    return session


email : str = "mh.conticini@gmail.com"
password : str = "password1"

# SIGN UP a new user
# user = supabase.auth.sign_up({ "email": users_email, "password": users_password })


# LOGIN an existing user
session = login(email, password)
print("New access token:", session.session.access_token)

# UPDATE CREDENTIALS FOR API CALL using access token for row level security
supabase.postgrest.auth(session.session.access_token)

# LOGOUT. The terminal will get stuck if you don't logout
try:
    supabase.auth.sign_out()
    print("Signed out.")

except:
    print("Finished.")