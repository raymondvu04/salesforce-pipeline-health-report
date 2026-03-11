import os
import requests
from dotenv import load_dotenv

load_dotenv()

CLIENT_ID = os.environ["SF_CLIENT_ID"].strip()
CLIENT_SECRET = os.environ["SF_CLIENT_SECRET"].strip()
REFRESH_TOKEN = os.environ["SF_REFRESH_TOKEN"].strip()

# Refresh token exchange via global login host (more reliable)
TOKEN_URL = "https://login.salesforce.com/services/oauth2/token"

# Your org instance for queries (from earlier)
INSTANCE_URL = "https://orgfarm-376d9615b0-dev-ed.develop.my.salesforce.com"
API_VERSION = "v65.0"

session = requests.Session()

# 1) Exchange refresh token for access token
resp = session.post(
    TOKEN_URL,
    data={
        "grant_type": "refresh_token",
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "refresh_token": REFRESH_TOKEN,
    },
    headers={"Content-Type": "application/x-www-form-urlencoded"},
    timeout=30,
)

if resp.status_code != 200:
    print("Status:", resp.status_code)
    print("Response:", resp.text)
    raise SystemExit(1)

auth = resp.json()
access_token = auth["access_token"]
instance_url = auth.get("instance_url", INSTANCE_URL)

# 2) Query Opportunities
soql = """
SELECT Id, Name, Amount, StageName, CloseDate, CreatedDate,
       IsClosed, IsWon, LeadSource, Type, AccountId
FROM Opportunity
LIMIT 5
"""
q = session.get(
    f"{instance_url}/services/data/{API_VERSION}/query",
    headers={"Authorization": f"Bearer {access_token}"},
    params={"q": soql},
    timeout=30,
)
q.raise_for_status()

records = q.json()["records"]
print(f"✅ Pulled {len(records)} opportunities via refresh token")
print({k: records[0].get(k) for k in ["Id","Name","StageName","Amount"]})