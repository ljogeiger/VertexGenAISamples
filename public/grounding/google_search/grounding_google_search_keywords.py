import base64
import vertexai
from vertexai.generative_models import GenerativeModel, Part, SafetySetting, FinishReason, Tool
import vertexai.preview.generative_models as generative_models


def generate():
    vertexai.init(project="cloud-llm-preview4", location="us-central1")
    model = GenerativeModel("gemini-1.5-flash-002-high-fidelity-preview",
                            tools=tools,
                            system_instruction=[textsi_1])
    response = model.generate_content(
        [text1],
        generation_config=generation_config,
        safety_settings=safety_settings,
        stream=False,
    )
    print(response, end="")


text1 = """Find allegations with the following company:
<input-name>
Seimens
</input-name>
"""
textsi_1 = """Your job is to provide a comprehensive report of negative news articles for a given input-name.

Follow these steps:
1. If input-name is a company map it to the legal business name.
2. Summarize and interpret Google Search results for a given input-name and all activies listed below. If there are no results for a given activity just skip it.
3. Come up with headline for the event and group results under the headline.

Your answer should be comprehensive: you must return all results over all time.

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
</activities>
"""

generation_config = {
    "max_output_tokens": 8192,
    "temperature": 0,
    "top_p": 0.95,
}

safety_settings = [
    SafetySetting(
        category=SafetySetting.HarmCategory.HARM_CATEGORY_HATE_SPEECH,
        threshold=SafetySetting.HarmBlockThreshold.BLOCK_NONE),
    SafetySetting(
        category=SafetySetting.HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT,
        threshold=SafetySetting.HarmBlockThreshold.BLOCK_NONE),
    SafetySetting(
        category=SafetySetting.HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT,
        threshold=SafetySetting.HarmBlockThreshold.BLOCK_NONE),
    SafetySetting(category=SafetySetting.HarmCategory.HARM_CATEGORY_HARASSMENT,
                  threshold=SafetySetting.HarmBlockThreshold.BLOCK_NONE),
]

tools = [
    Tool.from_google_search_retrieval(google_search_retrieval=generative_models
                                      .grounding.GoogleSearchRetrieval()),
]
generate()
