from google import genai
from google.genai import types
import json


def generate(user_query,
             input_image_bytes,
             example_one_input_text,
             example_one_image_bytes,
             example_one_output_text,
             example_two_input_text,
             example_two_image_bytes,
             example_two_output_text,
             system_instructions):
    client = genai.Client(vertexai=True,
                          project="sandbox-aiml",
                          location="us-central1")

    model = "gemini-2.0-flash-001"
    contents = [
        types.Content(role="user", parts=[
            types.Part.from_text(user_query),
            types.Part.from_bytes(data=input_image_bytes, mime_type="image/jpeg"),
            types.Part.from_text(example_one_input_text),
            types.Part.from_bytes(data=example_one_image_bytes, mime_type="image/jpeg"),
            types.Part.from_text(example_one_output_text),
            types.Part.from_text(example_two_input_text),
            types.Part.from_bytes(data=example_two_image_bytes, mime_type="image/jpeg"),
            types.Part.from_text(example_two_output_text),
        ])
    ]
    tools = []
    generate_content_config = types.GenerateContentConfig(
        temperature=1,
        top_p=0.95,
        max_output_tokens=8192,
        response_modalities=["TEXT"],
        safety_settings=[
            types.SafetySetting(category="HARM_CATEGORY_HATE_SPEECH",
                                threshold="OFF"),
            types.SafetySetting(category="HARM_CATEGORY_DANGEROUS_CONTENT",
                                threshold="OFF"),
            types.SafetySetting(category="HARM_CATEGORY_SEXUALLY_EXPLICIT",
                                threshold="OFF"),
            types.SafetySetting(category="HARM_CATEGORY_HARASSMENT",
                                threshold="OFF")
        ],
        tools=tools,
        system_instruction=[types.Part.from_text(system_instructions)],
    )

    response = client.models.generate_content(
        model=model,
        contents=contents,
        config=generate_content_config,
    )

    return response

user_query = """
User Query: dogs
"""

INPUT_IMAGE_PATH = '/Users/lukasgeiger/Desktop/VertexGenAISamples/public/utils/files/images/puppies.jpg'
with open(INPUT_IMAGE_PATH, 'rb') as f:
    input_image_bytes = f.read()

example_one_input_text = """
<ExampleOne>
<UserQuery>
Owl
</UserQuery>"""
EXAMPLE_ONE_IMAGE_PATH = '/Users/lukasgeiger/Desktop/VertexGenAISamples/public/utils/files/images/owl.jpg'
with open(EXAMPLE_ONE_IMAGE_PATH, 'rb') as f:
    example_one_image_bytes = f.read()
example_one_output_text = """
<Output>
{'score':2,'reason':'The image of a green horned owl is relevant to the user query, owl.'}
</Output>
</ExampleOne>"""

example_two_input_text = """
<ExampleTwo>
<UserQuery>
proboscis monkeys
</UserQuery>"""
EXAMPLE_TWO_IMAGE_PATH = '/Users/lukasgeiger/Desktop/VertexGenAISamples/public/utils/files/images/monkey.jpg'
with open(EXAMPLE_TWO_IMAGE_PATH, 'rb') as f:
    example_two_image_bytes = f.read()
example_two_output_text = """
<Output>
{'score':3,'reason':'The image of a monkey is relevant to the user query, proboscis monkeys, a species of monkey'}
</Output>
</ExampleTwo>"""

# Seperate call to measure specificity.
# Specificity is a measure of precision or detail of a query. A highly specific query or item is narrowly focused, while a less specific one is broader.
system_instructions = """
Given an image and a user query, your job is to measure how relevant the image is to the user query.

Provide an integer score from a scale of 0 to 2.

0 = represents that the image is irrelevant to the query,
1 = represents that the image is somewhat relevant to the query,
2 = represents that the image is highly relevant to the query.

Relevance is refers to how well a retrieved item matches the user's information need or query. It's about the degree to which the retrieved item satisfies the user's requirements.

Split this problem into steps:
    1. Consider the underlying intent of the search query.
    2. Measure how well the image matches the intent of the query.

Your output must also explain your reasoning.
Structure your output in JSON.
Output example:
{'score':<INT, image_score>,'reason':<STRING, reason_for_score>}
"""

response = generate(user_query,
                    input_image_bytes,
                    example_one_input_text,
                    example_one_image_bytes,
                    example_one_output_text,
                    example_two_input_text,
                    example_two_image_bytes,
                    example_two_output_text,
                    system_instructions,)
print(response.text)
