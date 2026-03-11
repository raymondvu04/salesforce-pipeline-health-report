import os
import requests
import pandas as pd
from dotenv import load_dotenv

load_dotenv()

CLIENT_ID = os.environ["SF_CLIENT_ID"].strip()
CLIENT_SECRET = os.environ["SF_CLIENT_SECRET"].strip()
REFRESH_TOKEN = os.environ["SF_REFRESH_TOKEN"].strip()

TOKEN_URL = "https://login.salesforce.com/services/oauth2/token"
API_VERSION = "v65.0"

def get_access_token():
    r = requests.post(
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
    r.raise_for_status()
    j = r.json()
    return j["access_token"], j["instance_url"]

def soql_query_all(session, instance_url, access_token, soql):
    url = f"{instance_url}/services/data/{API_VERSION}/query"
    headers = {"Authorization": f"Bearer {access_token}"}
    params = {"q": soql}

    records = []
    while True:
        resp = session.get(url, headers=headers, params=params, timeout=30)
        resp.raise_for_status()
        j = resp.json()
        records.extend(j["records"])
        if j.get("done"):
            break
        url = instance_url + j["nextRecordsUrl"]
        params = None
    for r in records:
        r.pop("attributes", None)
    return records

def main():
    os.makedirs("data/raw", exist_ok=True)

    access_token, instance_url = get_access_token()
    session = requests.Session()

    opps = soql_query_all(session, instance_url, access_token, """
        SELECT Id, Name, Amount, StageName, CloseDate, CreatedDate, LastModifiedDate,
               IsClosed, IsWon, LeadSource, Type, AccountId, OwnerId
        FROM Opportunity
    """)
    accts = soql_query_all(session, instance_url, access_token, """
        SELECT Id, Name, Industry, BillingCountry, BillingState, AnnualRevenue
        FROM Account
    """)

    pd.DataFrame(opps).to_csv("data/raw/opportunities.csv", index=False)
    pd.DataFrame(accts).to_csv("data/raw/accounts.csv", index=False)

    print(f"Saved {len(opps)} opportunities to data/raw/opportunities.csv")
    print(f"Saved {len(accts)} accounts to data/raw/accounts.csv")

if __name__ == "__main__":
    main()
