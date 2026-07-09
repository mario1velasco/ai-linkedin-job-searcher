import json
import os
import secrets
import webbrowser
from pathlib import Path
from urllib.parse import urlencode

import requests
import yaml
from dotenv import load_dotenv

load_dotenv()

CALLBACK_DATA_PATH = Path(__file__).resolve().parent / "callback_data.yaml"

state = secrets.token_urlsafe()
params = {
    "response_type": "code",
    "client_id": os.environ["CLIENT_ID"],
    "redirect_uri": os.environ["REDIRECT_URI"],
    "state": state,
    "scope": "openid profile email",
}

url = f"https://www.linkedin.com/oauth/v2/authorization?{urlencode(params)}"

webbrowser.open(url)

input("Press Enter after you have been redirected back to the application...")

with open(CALLBACK_DATA_PATH) as file:
    callback_data = yaml.safe_load(file)

    if callback_data["state"] != state:
        raise ValueError("State does not match! Possible CSRF attack.")

params = {
    "grant_type": "authorization_code",
    "code": callback_data["code"],
    "client_id": os.environ["CLIENT_ID"],
    "client_secret": os.environ["CLIENT_SECRET"],
    "redirect_uri": os.environ["REDIRECT_URI"],
}

response = requests.post("https://www.linkedin.com/oauth/v2/accessToken", data=params)

response.raise_for_status()

token = response.json()["access_token"]

response = requests.get(
    "https://api.linkedin.com/v2/userinfo", headers={"Authorization": f"Bearer {token}"}
)

print(json.dumps(response.json(), indent=4))
