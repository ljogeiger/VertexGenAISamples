import vertexai
from vertexai.preview.generative_models import grounding
from vertexai.generative_models import GenerationConfig, GenerativeModel, Tool
import vertexai.preview.generative_models as generative_models

# Initialize Vertex AI
vertexai.init(project="geminipro1-5", location="us-central1")

# Load the model
# gemini-1.5-pro-preview-0409
# gemini-1.0-pro-002
model = GenerativeModel(model_name="gemini-1.5-flash-001",
                        system_instruction=
                        """You are a production agent whose job it is to return top 10 websites for a given search term.
                        You must return 10 websites links and a detailed description based on the contents of each website.

                        You are also given a list of domains to exclude.
                        For each domain in the list check if your resulting sites contain the domain. If it does you must not include the result in the final result JSON object.

                        The output must be in the following JSON format:
                        {
                          "Result number":"<result-number>",
                          "Website Link":"<website-link>",
                          "Description":"<website-description>"
                        }
                        Think step by step.""")

# Use Google Search for grounding
tool = Tool.from_google_search_retrieval(grounding.GoogleSearchRetrieval())

prompt = """
Prompt: Search term: Vladmir Putin
Domains to exclude: britannica.com, bbc.com, nytimes.com, cfr.org, theguardian.com, cnn.com
"""
# #2
# Website Link: https://www.linkedin.com/in/ljogeiger
# Summary: This website is a LinkedIn site about Lukas Geiger and his career path. There is no negative sentiment on this site likely because it was authored by Lukas.

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
        response_mime_type="application/json",
    ),
    safety_settings=safety_settings,
)

print(response)
print(response.text)
