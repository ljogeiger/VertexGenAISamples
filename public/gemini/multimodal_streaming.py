import vertexai

from vertexai.generative_models import GenerativeModel, Part

# TODO(developer): Update & un-comment the lines below
# PROJECT_ID = "your-project-id"

vertexai.init(project="cloud-llm-preview4", location="us-central1")

model = GenerativeModel("gemini-1.5-flash-002")
responses = model.generate_content(
    [
        Part.from_uri(
            "gs://cloud-samples-data/generative-ai/video/animals.mp4", "video/mp4"
        ),
        Part.from_uri(
            "gs://cloud-samples-data/generative-ai/image/character.jpg",
            "image/jpeg",
        ),
        "Are these video and image correlated?",
    ],
    stream=True,
)

for response in responses:
    print(response)
