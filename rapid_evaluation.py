import json

import google.auth.transport.requests
import requests

creds, _ = google.auth.default()
auth_req = google.auth.transport.requests.Request()
creds.refresh(auth_req)
token = creds.token

API_ENDPOINT="us-central1-aiplatform.googleapis.com"
PROJECT_ID="geminipro1-5"
MODEL_ID="gemini-1.5-pro-preview-0409"
REGION="us-central1"

data = {
  # "exact_match_input" : {
  #   "metric_spec": {},
  #   "instances": [
  #     {
  #       "prediction": "Keyword: ironmountain",
  #       "reference": "Keyword: ironmountain"
  #     }
  #   ]
  # },
  "fulfillment_input": {
    "metric_spec": {},
    "instance": {
      "prediction": "bad",
      "instruction": "Find the keyword from the text below. The keyword is one word immediately following 'Keyword: '. Output the keyword in JSON format."
    }
  }
}

headers = {
  "Authorization": f"Bearer {token}"
}

uri = f'https://{REGION}-aiplatform.googleapis.com/v1beta1/projects/{PROJECT_ID}/locations/{REGION}:evaluateInstances'
result = requests.post(uri, headers=headers, json=data)

print(json.dumps(result.json(), indent=2))
