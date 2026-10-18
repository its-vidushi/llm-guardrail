import requests
from keys import CF_ACCOUNT_ID, CF_API_TOKEN

URL = f"https://api.cloudflare.com/client/v4/accounts/{CF_ACCOUNT_ID}/ai/run/@cf/cloudflare/clef-flash"

def ask_clef(state, questions):
    r = requests.post(URL, headers={"Authorization": f"Bearer {CF_API_TOKEN}"},
                      json={"model": "clef-flash", "state": state, "questions": questions})
    r.raise_for_status()
    return r.json()["result"]["answers"]