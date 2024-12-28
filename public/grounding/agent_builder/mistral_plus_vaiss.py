import streamlit as st
import json

import vertexai
from google.cloud import aiplatform
from vertexai.generative_models import GenerativeModel
from google.cloud import discoveryengine_v1 as discoveryengine
from google.protobuf.json_format import MessageToDict

project_id = "vertexsearchconversations"
vais_location = "global"
engine_id = "southwire-manuals-ocr_1713385393728"
region = "us-central1"

aiplatform.init(project=project_id, location=region)

client = discoveryengine.SearchServiceClient(client_options=None)
serving_config = f"projects/{project_id}/locations/{vais_location}/collections/default_collection/engines/{engine_id}/servingConfigs/default_config"

content_search_spec = discoveryengine.SearchRequest.ContentSearchSpec(
    extractive_content_spec=discoveryengine.SearchRequest.ContentSearchSpec.
    ExtractiveContentSpec(
        max_extractive_segment_count=1,
        return_extractive_segment_score=True,
        # num_previous_segments = 1,
        # num_next_segments = 1,
    ),
    summary_spec=discoveryengine.SearchRequest.ContentSearchSpec.SummarySpec(
        summary_result_count=5,
        include_citations=True,
        ignore_adversarial_query=True,
        ignore_non_summary_seeking_query=True,
        model_spec=discoveryengine.SearchRequest.ContentSearchSpec.SummarySpec.
        ModelSpec(
            version="gemini-1.5-flash-002",  # specify gemini-1.5-flash here
        ),
    ),
)

# Configs for Mistral Prediction

endpoint_name = "224614832391847936"
aip_endpoint_name = (
    f"projects/{project_id}/locations/{region}/endpoints/{endpoint_name}")
endpoint = aiplatform.Endpoint(aip_endpoint_name)

max_tokens = 500
temperature = 1.0
top_p = 1.0
top_k = 1
raw_response = False

# Logic for collecting parameters and chat functions


def get_answer_from_content(user_input, content):

    prompt = f"""
  You're a helpful production-level AI assistant. Given a user question and some Southwire manuals snippets, answer the user question and provide citations. If none of the articles answer the question, just say you don't know.

  Remember, you must return both an answer and citations. A citation consists of a VERBATIM quote that justifies the answer and the ID of the quote article. Return a citation for every quote across all articles that justify the answer. Use the following format for your final output:

  <cited_answer>
      <answer></answer>
      <citations>
          <citation><source_id></source_id><quote></quote></citation>
          <citation><source_id></source_id><quote></quote></citation>
          ...
      </citations>
  </cited_answer>

  <user-question>
  {user_input}
  </user-question>

  <content>
  {content}
  </content>
  """

    instances = [
        {
            "prompt": prompt,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "top_p": top_p,
            "top_k": top_k,
            "raw_response": raw_response,
        },
    ]
    response = endpoint.predict(instances=instances)

    return response.predictions[0]


# Vertex Search Logic


def execute_vaiss_query(input):  # 16 AWG, UF

    request = discoveryengine.SearchRequest(
        serving_config=serving_config,
        query=input,
        page_size=10,
        content_search_spec=content_search_spec,
        query_expansion_spec=discoveryengine.SearchRequest.QueryExpansionSpec(
            condition=discoveryengine.SearchRequest.QueryExpansionSpec.
            Condition.AUTO, ),
        spell_correction_spec=discoveryengine.SearchRequest.
        SpellCorrectionSpec(
            mode=discoveryengine.SearchRequest.SpellCorrectionSpec.Mode.AUTO),
    )
    response = client.search(request)
    print(response)

    extractive_segment_list = []
    for result in response.results:
        link = result.document.derived_struct_data.get("link", "Unknown Link")
        title = result.document.derived_struct_data.get(
            "title", "Unknown Title")
        relevance_score = result.document.derived_struct_data[
            "extractive_segments"][0].get("relevanceScore", "Unknown Score")
        content = result.document.derived_struct_data["extractive_segments"][
            0].get("content", "No content")
        page_number = result.document.derived_struct_data[
            "extractive_segments"][0].get("pageNumber", "No page number")
        extractive_segment = {
            "title": title,
            "link": link,
            "relevance_score": relevance_score,
            "content": content,
            "page_number": page_number
        }

        extractive_segment_list.append(extractive_segment)

    return extractive_segment_list[0:2], response.summary


# Streamlit Logic
st.title("Southwire Manual Search")
st.text(
    "This agent uses Southwire Manuals found publicly online and uses Mistral to summarize and answer the questions."
)

user_input = st.text_input(
    "Please ask your question here. Example: Please provide details for UF 16 AWG?"
)
button = st.button("Search")

if button and user_input:
    vaiss_response, summary = execute_vaiss_query(user_input)
    st.json(vaiss_response, expanded=False)
    st.text(getattr(summary, "summary_text", ""))
    st.text(getattr(summary, "summary_with_metadata", ""))
    # mistral_response = get_answer_from_content(user_input, vaiss_response)

    # st.markdown(mistral_response)
