import os
import requests
from dotenv import load_dotenv

load_dotenv()

USERNAME = os.environ["SF_USERNAME"].strip()
PASSWORD = os.environ["SF_PASSWORD"].strip()
TOKEN = os.environ["SF_TOKEN"].strip()
CLIENT_ID = os.environ["SF_CLIENT_ID"].strip()
CLIENT_SECRET = os.environ["SF_CLIENT_SECRET"].strip()

print("lens:", len(USERNAME), len(PASSWORD), len(TOKEN), len(CLIENT_ID), len(CLIENT_SECRET))

LOGIN_URL = "https://orgfarm-376d9615b0-dev-ed.develop.my.salesforce.com/services/oauth2/token"
API_VERSION = "v65.0"

# 1) Authenticate
resp = requests.post(LOGIN_URL, data={
    "grant_type": "password",
    "client_id": CLIENT_ID,
    "client_secret": CLIENT_SECRET,
    "username": USERNAME,
    "password": PASSWORD
})
if resp.status_code != 200:
    print("Status:", resp.status_code)
    print("Response:", resp.text)
    raise SystemExit(1)

auth = resp.json()

access_token = auth["access_token"]
instance_url = auth["instance_url"]

# 2) Query (SOQL)
soql = """
SELECT Id, Name, Amount, StageName, CloseDate, CreatedDate,
       IsClosed, IsWon, LeadSource, Type, AccountId
FROM Opportunity
ORDER BY CreatedDate DESC
LIMIT 10
"""

q = requests.get(
    f"{instance_url}/services/data/{API_VERSION}/query",
    headers={"Authorization": f"Bearer {access_token}"},
    params={"q": soql}
)
q.raise_for_status()

records = q.json()["records"]
print(f"Pulled {len(records)} opportunities")
print("Sample record:", {k: records[0].get(k) for k in ["Id","Name","StageName","Amount","CloseDate"]})