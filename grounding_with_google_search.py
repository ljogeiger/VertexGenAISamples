import vertexai
from vertexai.preview.generative_models import grounding
from vertexai.generative_models import GenerationConfig, GenerativeModel, Tool
import vertexai.preview.generative_models as generative_models

# Initialize Vertex AI
vertexai.init(project="cloud-llm-preview4", location="us-central1")

# Load the model
# gemini-1.5-pro-preview-0409
# gemini-1.0-pro-002
model = GenerativeModel(model_name="gemini-1.0-pro-002")

# Use Google Search for grounding
tool = Tool.from_google_search_retrieval(grounding.GoogleSearchRetrieval())

prompt = """
INSTRUCTIONS: Use the Google Search Retrival Tool. Your job is to:
1. Search for the following search term: Lukas Geiger. Return the top 10 websites.
2. Analyze the content of the websites for negative sentiment.
Think step by step.

If there are no websites with negative surface say "no negative sentiment found on this website" for each website.

The output should include the top 10 websites:
- The website link
- Summary of the content of the website
- Negative Sentiment score (%)

Example:
Search Query: Lukas Geiger
#1
Website Link: www.lukasgeiger.com
Summary: This website is about Lukas Geiger.
Negative Sentiment Score: 40%
#2
Website Link: www.wikipedia.com/lukasgeiger
Summary: This website is about Lukas Geiger.
Negative Sentiment Score: 67%
...
"""

safety_settings = {
    generative_models.HarmCategory.HARM_CATEGORY_HATE_SPEECH: generative_models.HarmBlockThreshold.BLOCK_NONE,
    generative_models.HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: generative_models.HarmBlockThreshold.BLOCK_NONE,
    generative_models.HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: generative_models.HarmBlockThreshold.BLOCK_NONE,
    generative_models.HarmCategory.HARM_CATEGORY_HARASSMENT: generative_models.HarmBlockThreshold.BLOCK_NONE,
}

response = model.generate_content(
    prompt,
    tools=[tool],
    generation_config=GenerationConfig(
        temperature=0.0,
    ),
    safety_settings=safety_settings,
)

print(response)
print(response.text)
