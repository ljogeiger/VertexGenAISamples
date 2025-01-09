from google import genai
from google.genai import types
import json


def generate(prompt, system_instructions):
    client = genai.Client(vertexai=True,
                          project="cloud-llm-preview1",
                          location="us-central1")

    model = "gemini-2.0-flash-exp"
    contents = [
        types.Content(role="user", parts=[
            types.Part.from_text(prompt),
        ])
    ]
    tools = [types.Tool(google_search=types.GoogleSearch())]
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


# Adapted from https://github.com/ndebuhr/fishbot/blob/935684458f0cb6cb336d4d412da2eecdbc60e417/src/app.py#L37
def get_sources(response):
    """Return a list of sources corresponding with response citations"""
    metadata = response.candidates[0].grounding_metadata
    sources = {}
    source_titles = {}
    for support in metadata.grounding_supports:
        for chunk_index in support.grounding_chunk_indices:
            display_chunk_index = chunk_index + 1  # offset 0 list index
            if display_chunk_index not in source_titles:
                source_titles[display_chunk_index] = metadata.grounding_chunks[
                    chunk_index].web.title
                sources[display_chunk_index] = metadata.grounding_chunks[
                    chunk_index].web
    sorted_source_titles = dict(sorted(source_titles.items()))
    source_text = ""
    if sources:
        for i in sorted_source_titles:
            source_text += f"\n\n[[{i}] {sorted_source_titles[i]}]({sources[i]})"
    print(source_text)


prompt = """
Find allegations with the following entity:
<input_entity>
{entity}
</input_entity>
"""

system_instructions = """

Your job is to provide a comprehensive and professional report of negative news articles for a given input_entity. Input_entity can be a person, company, or ship.
Search thoroughly across all time.
Provide a date news article you cite.

For person names, strictly follow entity names.

If there are no negative news articles associates with the input_entity say "There are no results found for <input_entity>".

Follow these steps:
1. If input_entity is a company map it to the legal business name.
2. Summarize and interpret Google Search results for a given input_entity and all activities provided. If there are no results for a given activity just skip it.
3. Come up with headline for the event and group results under the headline.

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
entities = ["Seimens"]  #, "Lukas Geiger", "fujikara cars", "Mark Larson"]
for entity in entities:
    response = generate(prompt.format(entity=entity), system_instructions)
    print(response.text)
    # Get grounding information (sources, urls, confidence_scores, etc.)
    print(response.candidates[0].grounding_metadata)
    get_sources(response)
