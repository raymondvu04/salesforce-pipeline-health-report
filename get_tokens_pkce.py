import os
import requests
from dotenv import load_dotenv

load_dotenv()

CLIENT_ID = os.environ["SF_CLIENT_ID"].strip()
CLIENT_SECRET = os.environ["SF_CLIENT_SECRET"].strip()

INSTANCE = "https://orgfarm-376d9615b0-dev-ed.develop.my.salesforce.com"
TOKEN_URL = f"{INSTANCE}/services/oauth2/token"
REDIRECT_URI = "http://localhost:8080/callback"

AUTH_CODE = "aPrx.ppuB8UlvcG9aX9vbL_Jx460rTp4pgpzYuEJeea1TebUwQLx3Sp2umRaqM..uJHIAyNyCT.IDNxGPEbVq981HsLoEiE="
CODE_VERIFIER = "VYbTcm2NnU34UTwd_2StUzROrfc09EFQaOGjOQt35mE"

resp = requests.post(TOKEN_URL, data={
    "grant_type": "authorization_code",
    "client_id": CLIENT_ID,
    "client_secret": CLIENT_SECRET,
    "redirect_uri": REDIRECT_URI,
    "code": AUTH_CODE,
    "code_verifier": CODE_VERIFIER,
})

print("Status:", resp.status_code)
print("Response:", resp.text)
resp.raise_for_status()