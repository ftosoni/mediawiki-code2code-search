import os
from dotenv import load_dotenv
load_dotenv()
token = os.getenv("HF_TOKEN")
if token:
    print(f"Token found: {token[:5]}...{token[-5:]}")
else:
    print("❌ Token NOT found in environment.")
