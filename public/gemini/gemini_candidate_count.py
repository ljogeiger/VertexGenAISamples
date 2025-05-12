from google import genai
from google.genai import types
import base64

def generate():
  client = genai.Client(
      vertexai=True,
      project="sandbox-aiml",
      location="global",
  )

  # Works with:
  # - gemini-2.0-flash-001
  # - gemini-2.5-flash-preview-04-17
  # - gemini-2.5-pro-preview-05-06
  model = "gemini-2.0-flash-lite-001"
  contents = [
    types.Content(
      role="user",
      parts=[
        types.Part.from_text(text="""What color is the sky?""")
      ]
    ),
  ]
  generate_content_config = types.GenerateContentConfig(
    temperature = 1,
    top_p = 0.95,
    seed = 0,
    max_output_tokens = 8192,
    response_modalities = ["TEXT"],
    safety_settings = [types.SafetySetting(
      category="HARM_CATEGORY_HATE_SPEECH",
      threshold="OFF"
    ),types.SafetySetting(
      category="HARM_CATEGORY_DANGEROUS_CONTENT",
      threshold="OFF"
    ),types.SafetySetting(
      category="HARM_CATEGORY_SEXUALLY_EXPLICIT",
      threshold="OFF"
    ),types.SafetySetting(
      category="HARM_CATEGORY_HARASSMENT",
      threshold="OFF"
    )],
    candidate_count = 3,
  )

  # Does not work with generate_content_stream()
  response = client.models.generate_content(
    model = model,
    contents = contents,
    config = generate_content_config,
    )
  print(response)

generate()

""" Example response:
candidates=[
            Candidate(content=Content(parts=[Part(video_metadata=None, thought=None, code_execution_result=None, executable_code=None, file_data=None, function_call=None, function_response=None, inline_data=None, text='The sky is blue on a clear day.\n')], role='model'), citation_metadata=None, finish_message=None, token_count=None, avg_logprobs=-0.2720562696456909, finish_reason=<FinishReason.STOP: 'STOP'>, grounding_metadata=None, index=None, logprobs_result=None, safety_ratings=None),
            Candidate(content=Content(parts=[Part(video_metadata=None, thought=None, code_execution_result=None, executable_code=None, file_data=None, function_call=None, function_response=None, inline_data=None, text='The sky is **blue** during the day.\n')], role='model'), citation_metadata=None, finish_message=None, token_count=None, avg_logprobs=-0.348779786716808, finish_reason=<FinishReason.STOP: 'STOP'>, grounding_metadata=None, index=1, logprobs_result=None, safety_ratings=None),
            Candidate(content=Content(parts=[Part(video_metadata=None, thought=None, code_execution_result=None, executable_code=None, file_data=None, function_call=None, function_response=None, inline_data=None, text='The sky appears blue to us most of the time. This is due to a phenomenon called Rayleigh scattering, where shorter wavelengths of light (like blue and violet) are scattered more by the atmosphere than longer wavelengths (like red and orange).\n')], role='model'), citation_metadata=None, finish_message=None, token_count=None, avg_logprobs=-0.14550956090291342, finish_reason=<FinishReason.STOP: 'STOP'>, grounding_metadata=None, index=2, logprobs_result=None, safety_ratings=None)
            ]
            model_version='gemini-2.0-flash-001' prompt_feedback=None usage_metadata=GenerateContentResponseUsageMetadata(cached_content_token_count=None, candidates_token_count=69, prompt_token_count=6, total_token_count=75) automatic_function_calling_history=[] parsed=None
"""
