import base64
import vertexai
from vertexai.generative_models import GenerativeModel, Part, SafetySetting, FinishReason, Tool
import vertexai.preview.generative_models as generative_models


def generate():
  vertexai.init(project="cloud-llm-preview4", location="us-central1")
  model = GenerativeModel(
    "gemini-1.5-flash-001",
    tools=tools,
    system_instruction=[textsi_1]
  )
  responses = model.generate_content(
      [text1],
      generation_config=generation_config,
      safety_settings=safety_settings,
      stream=True,
  )

  for response in responses:
    if not response.candidates[0].content.parts:
      continue
    print(response.text, end="")

text1 = """Find allegations with the following company:
<input-name>
fujikura automotive
</input-name>

Refer to each activity that has allegations in a paragraph, naming the activity as heading. If there are no allegations  just skip the section for that activity."""
textsi_1 = """You are a production search assistant. Your job is to summarize and interpret Google Search tool results for a given input-name and all keywords listed below. The input-name can be a person or business name. In your summary and interpretation explain why the article from Google Search tool is relevant to the keyword.
You must cite your sources.

<activities>
Money Laundering
Forgery
Bribery and Corruption
Human Trafficking
War Crimes
Human Rights Violation
Piracy / Counterfeiting
Tax Evasion / Tax Fraud
Antitrust Violations
Arms Trafficking
Environmental Crimes
Pharmaceutical Product Trafficking
Extortion
Fraud
Drug / Narcotics Trafficking
Organized Crime / Racketeering
Illicit Trafficking in Stolen and Other Goods
Falsifying Information on Official Documents
Robbery / Theft
Currency Counterfeiting
Embezzlement
Terrorism / Terror Financing
Cybercrime / Hacking / Phishing
Sanction Violations
Civil Lawsuit
Securities Fraud / Insider Trading
Hostage Taking / Kidnapping
</activities>"""

generation_config = {
    "max_output_tokens": 8192,
    "temperature": 0,
    "top_p": 0.95,
}

safety_settings = [
    SafetySetting(
        category=SafetySetting.HarmCategory.HARM_CATEGORY_HATE_SPEECH,
        threshold=SafetySetting.HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE
    ),
    SafetySetting(
        category=SafetySetting.HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT,
        threshold=SafetySetting.HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE
    ),
    SafetySetting(
        category=SafetySetting.HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT,
        threshold=SafetySetting.HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE
    ),
    SafetySetting(
        category=SafetySetting.HarmCategory.HARM_CATEGORY_HARASSMENT,
        threshold=SafetySetting.HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE
    ),
]

tools = [
    Tool.from_google_search_retrieval(
        google_search_retrieval=generative_models.grounding.GoogleSearchRetrieval(disable_attribution=False)
    ),
]
generate()
