from dotenv import load_dotenv
load_dotenv()

import os
from supabase import create_client

url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_KEY")
supabase= create_client(url, key)

# update data to DB
data = supabase.table("test_data").update({"address_city": "Napoli", "first_name": "Timothy"}).eq("first_name", "Tim").execute()

# read data from DB
data = supabase.table("users").select("*").eq("address_city", "Mantova").execute()
print("Pulled data:", data)

# Assert we pulled real data.
assert len(data.data) > 0