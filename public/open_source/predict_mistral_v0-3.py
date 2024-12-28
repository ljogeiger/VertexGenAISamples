from google.cloud import aiplatform

PROJECT_ID = "vertexsearchconversations"
REGION = "us-central1"

aiplatform.init(project=PROJECT_ID, location=REGION)

endpoint_name = "224614832391847936"
aip_endpoint_name = (
    f"projects/{PROJECT_ID}/locations/{REGION}/endpoints/{endpoint_name}"
)
endpoint = aiplatform.Endpoint(aip_endpoint_name)

prompt = "What is a car?"
max_tokens = 200
temperature = 1.0
top_p = 1.0
top_k = 1
raw_response = False

# Overrides parameters for inferences.
instances = [
    {
        "prompt": prompt,
        "max_tokens": max_tokens,
        "temperature": temperature,
        "top_p": top_p,
        "top_k": top_k,
        "raw_response": raw_response,
    },
]
response = endpoint.predict(instances=instances)

for prediction in response.predictions:
    print(prediction)


