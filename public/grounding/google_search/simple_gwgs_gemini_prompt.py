import vertexai
from vertexai.preview.generative_models import grounding
from vertexai.generative_models import GenerationConfig, GenerativeModel, Tool
import vertexai.preview.generative_models as generative_models

# Initialize Vertex AI
vertexai.init(project="geminipro1-5", location="us-central1")

# Load the model
# gemini-1.5-pro-preview-0409
# gemini-1.0-pro-002
model = GenerativeModel(model_name="gemini-1.5-flash-001")

# Use Google Search for grounding
tool = Tool.from_google_search_retrieval(grounding.GoogleSearchRetrieval())

prompt = """
What is the weather today?
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
        temperature=0.1,
    ),
    safety_settings=safety_settings,
)

print(response)
print(response.text)
