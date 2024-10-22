import base64
import json

import httpx
import requests
import subprocess

MODEL = "claude-3-haiku@20240307"

# available_regions = ["us-east5", "europe-west1", "asia-southeast1"]
LOCATION = "us-east5"

PROJECT_ID = "cloud-llm-preview4"  # @param {type:"string"}
ENDPOINT = f"https://{LOCATION}-aiplatform.googleapis.com"

if not PROJECT_ID or PROJECT_ID == "[your-project-id]":
    raise ValueError("Please set your PROJECT_ID")

prompt = """"Please provide a concise summary of the following call transcription. Focus on the key topics discussed, any decisions made, and the overall sentiment of the conversation. Maximum of 150 words output:

<transcript>
(AH): Good morning, everyone. Thanks for joining this Project Nightingale status update. Let\'s start with a quick rundown of the key areas. Ben, can you give us an update on the software development progress?
(BC): Good morning, Amelia. The core functionality is largely complete. We\'ve successfully integrated the sentiment analysis module, and initial testing shows accuracy above 92%. We’re currently addressing a few minor bugs identified during internal testing. One pertains to the handling of unusual character sets in user inputs; we expect a fix by end of day. The other involves occasional latency spikes during peak usage – we’re optimizing database queries to mitigate this. We’re also working on finalizing the API documentation for third-party integrations, which should be ready by Tuesday.
(AH): Excellent progress, Ben. Chloe, how\'s the data science side shaping up? Are we on track for the initial data release?
(CD): Yes, Amelia. The initial data cleaning and pre-processing is complete. We’ve developed a robust pipeline for continuous data ingestion and updating of our models. The initial dataset is ready for deployment, and we are currently validating the model\'s performance against various demographic segments to ensure fairness and accuracy across different user groups. We\'ve identified a slight bias in the model\'s prediction concerning users aged 65+, which we\'re actively working to address using re-weighting techniques. We anticipate resolving this before the end of the week. The final report on data quality and model performance will be available by Friday.
(AH): Good work, Chloe. Addressing bias proactively is crucial. David, what\'s the status on the marketing and communications plan? Are we ready for the launch announcement?
(DL): We\'re almost ready, Amelia. The press release is finalized, and we’ve secured interviews with several key tech publications. We\'ve also created compelling social media content, and our initial influencer outreach has yielded positive results. We\'re planning a phased rollout, starting with a targeted announcement to our existing user base followed by a broader press release next week. We’ve also prepared FAQs and various support materials for user onboarding. We just need final sign-off on the marketing materials before we proceed with the launch sequence.
(AH): Perfect. Let’s schedule a quick review of the marketing materials tomorrow afternoon. Are there any roadblocks or concerns anyone wants to raise?
(BC): I do have one minor concern regarding the server capacity. While we’ve provisioned for a substantial initial user load, a sudden surge in popularity could potentially overload the system. We’re exploring options for scaling up rapidly if necessary.
(CD): I second Ben\'s concern. The model\'s processing power is directly linked to server capacity; increased load could negatively impact prediction accuracy.
(AH): That\'s a valid concern. Let\'s discuss potential scaling solutions during our meeting tomorrow. We need to ensure system stability during the launch. We should also consider implementing a queuing system to manage peak demand. Ben, can you investigate cloud-based scaling solutions overnight?
(BC): Absolutely, I\'ll prioritize that.
(AH): Excellent. Overall, I\'m pleased with the progress. We\'re on track for the launch, and addressing the identified issues proactively should ensure a smooth and successful rollout. Let\'s keep the momentum going. I\'ll send out a follow-up email with action items and meeting invites for tomorrow. Thank you all for your hard work and dedication.
(BC): Thanks, Amelia.
(CD): Thanks.
(DL): Thanks, Amelia. Have a good day.
(AH): You too. Have a great day everyone.
</transcript>
"""

data = {
    "anthropic_version": "vertex-2023-10-16",
    "messages": [{"role": "user", "content": prompt}],
    "temperature": 0.1,
    "max_tokens": 150,
    "stream": False,
}

process = subprocess.Popen(
    "gcloud auth print-access-token", stdout=subprocess.PIPE, shell=True
)
(access_token_bytes, err) = process.communicate()
access_token = access_token_bytes.decode("utf-8").strip()  # Strip newline

headers = {
    "Authorization": f"Bearer {access_token}",
    "Accept": "application/json",
}

url = f"{ENDPOINT}/v1/projects/{PROJECT_ID}/locations/{LOCATION}/publishers/anthropic/models/{MODEL}:rawPredict"

response = requests.post(url,
                        headers = headers,
                        json = data)

print(response.text)
