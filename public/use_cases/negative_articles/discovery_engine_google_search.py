from google.cloud import discoveryengine_v1 as discoveryengine
import vertexai, re

# Initialize set variables and clients
PROJECT_NUMBER = "807698966239"
PROJECT_ID = "vertexsearchconversations"
LOCATION = "us-central1"

client = discoveryengine.GroundedGenerationServiceClient()

vertexai.init(project=PROJECT_NUMBER, location=LOCATION)


# Response Type: https://cloud.google.com/python/docs/reference/discoveryengine/latest/google.cloud.discoveryengine_v1beta.types.GenerateGroundedContentResponse
def execute_grounded_gemini_call(
    prompt,
    system_instructions,
    model="gemini-2.0-exp",
):
    # Function to execute the request

    request = discoveryengine.GenerateGroundedContentRequest(
        # The full resource name of the location.
        # Format: projects/{PROJECT_NUMBER}/locations/{location}
        location=client.common_location_path(project=PROJECT_NUMBER,
                                             location="global"),
        generation_spec=discoveryengine.GenerateGroundedContentRequest.
        GenerationSpec(
            model_id=model,
        ),  # Could use gemini-1.5-flash-002, gemini-1.5-pro-002 or gemini-1.5-flash-002-high-fidelity
        # Conversation between user and model
        contents=[
            discoveryengine.GroundedGenerationContent(
                role="user",
                parts=[
                    discoveryengine.GroundedGenerationContent.Part(text=prompt)
                ],
            )
        ],
        system_instruction=discoveryengine.GroundedGenerationContent(parts=[
            discoveryengine.GroundedGenerationContent.Part(
                text=system_instructions)
        ], ),
        # What to ground on.
        grounding_spec=discoveryengine.GenerateGroundedContentRequest.
        GroundingSpec(grounding_sources=[
            discoveryengine.GenerateGroundedContentRequest.GroundingSource(
                google_search_source=discoveryengine.
                GenerateGroundedContentRequest.GroundingSource.
                GoogleSearchSource(
                    # Optional: For Dynamic Retrieval
                    # dynamic_retrieval_config=discoveryengine.
                    # GenerateGroundedContentRequest.DynamicRetrievalConfiguration(
                    #     predictor=discoveryengine.GenerateGroundedContentRequest.
                    #     DynamicRetrievalConfiguration.DynamicRetrievalPredictor(
                    #         threshold=0.7))
                )),
        ]),
    )

    response = client.generate_grounded_content(request)

    print(response)

    # Handle the response
    return response

def insert_citation(text, segment, citation, case_sensitive=False):
    """
    Finds a text segment within a larger text and inserts a citation after it.

    Args:
        text: The larger text string.
        segment: The text segment to search for.
        citation: The citation string to insert.
        case_sensitive: Boolean, if True performs a case-sensitive search,
                        else case-insensitive (default).

    Returns:
        The modified text with the citation inserted, or the original text if
        the segment is not found.  Returns an error message if there's a problem.
    """

    flags = 0  # Default no flags
    if not case_sensitive:
        flags = re.IGNORECASE

    try:
        # Escape special characters in the segment for regular expression
        escaped_segment = re.escape(segment)

        # Find all occurrences of the segment
        matches = list(re.finditer(escaped_segment, text, flags))

        if not matches:
            return text  # Segment not found

        # For now, let's just insert the citation after the FIRST match.
        # You can modify this to handle multiple matches differently if needed.
        match = matches[0]
        start_index = match.start()
        end_index = match.end()

        modified_text = text[:end_index] + " " + citation + text[end_index:]
        return modified_text

    except re.error as e:
        return f"Error with regular expression: {e}"
    except Exception as e: # Catch any other potential error
        return f"An unexpected error occurred: {e}"

def add_sources(response):
    """Add simple numbered citations to the response."""
    text = response.candidates[0].content.parts[0].text
    metadata = response.candidates[0].grounding_metadata

    print(metadata)

    source_text = ""
    # Get sources to list at bottom of response.text
    for index, source in enumerate(metadata.support_chunks):
        source_text += f"[{index}] - [{source.source_metadata["domain"]}]({source.source_metadata["uri"]})\n\n"

    # Get grounding_supports and insert citations
    for support in metadata.grounding_support:
        text = insert_citation(text, support.claim_text, f"{[citation for citation in support.support_chunk_indices]}")

    # Add source list at the bottom

    return f"{text}\n{source_text}"


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

# Get responses from Gemini with GwGS
entities = ["Seimens"]  #, "Lukas Geiger", "fujikara cars", "Mark Larson"]

responses = []
references = []
for entity in entities:
    response = execute_grounded_gemini_call(
        prompt=prompt.format(entity=entity),
        system_instructions=system_instructions,
        model="gemini-2.0-flash-exp")  # gemini-1.5-flash-002-high-fidelity
    print(response.candidates[0].content.parts[0].text)
    modified_text = add_sources(response)
    responses.append(response.candidates[0].content.parts[0].text)

print(f"Gemini GwGS calls complete. Responses: \n{modified_text}")
