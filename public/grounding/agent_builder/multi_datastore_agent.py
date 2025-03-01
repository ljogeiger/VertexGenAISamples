import streamlit as st
import json
from typing import Dict, List, Optional, Tuple

import vertexai
from google.cloud import aiplatform
from vertexai.generative_models import GenerativeModel
from google.cloud import discoveryengine_v1 as discoveryengine
from google.protobuf.json_format import MessageToDict

project_id = "irm-agentbld-demo"
vais_location = "global"
legal_engine_id = "legal_global"
risk_engine_id = "risk_global"
infosec_engine_id = "infosec_global"

legal_serving_config = f"projects/{project_id}/locations/{vais_location}/collections/default_collection/engines/{legal_engine_id}/servingConfigs/default_config"
risk_serving_config = f"projects/{project_id}/locations/{vais_location}/collections/default_collection/engines/{risk_engine_id}/servingConfigs/default_config"
infosec_serving_config = f"projects/{project_id}/locations/{vais_location}/collections/default_collection/engines/{infosec_engine_id}/servingConfigs/default_config"

client = discoveryengine.SearchServiceClient(client_options=None)

content_search_spec = discoveryengine.SearchRequest.ContentSearchSpec(
    snippet_spec=discoveryengine.SearchRequest.ContentSearchSpec.SnippetSpec(
        return_snippet=True),
    summary_spec=discoveryengine.SearchRequest.ContentSearchSpec.SummarySpec(
        summary_result_count=5,
        include_citations=True,
        ignore_adversarial_query=True,
        ignore_non_summary_seeking_query=True,
        # model_prompt_spec=discoveryengine.SearchRequest.ContentSearchSpec.SummarySpec.ModelPromptSpec(
        #     preamble="YOUR_CUSTOM_PROMPT"
        # ),
        model_spec=discoveryengine.SearchRequest.ContentSearchSpec.SummarySpec.
        ModelSpec(version="gemini-1.5-flash-002/answer_gen/v1", ),
    ),
)

# Logic for collecting parameters and chat functions


def start_chat_session():
    vertexai.init(project=project_id, location="us-central1")

    system_instruction = '''
  You are a friendly and helpful conversational chatbot. You can answer a wide range of questions.
  The user might greet you or jump directly into asking questions. If they greet you, greet them back and give them instructions on how to interact with you.

  You should politely ask the user if they have a question regarding legal, risk or information security.
  You cannot have multiple categories. If the user says something not related to these categories say: "That is outside the scope of this system. Please consult internal documentation for help." and ask again.

  If the user indicated they aren't sure, tell them the following: "The legal agent can provide help with questions regarding legal terms and conditions, risk agent can help with questions regarding risk managment, and the information security agent can assist with questions regarding information security policies."

  * **Question Type:** Is your question related to legal, risk, or information security?
  * **User Question:** What is your question?

  *Rule*
  If field is not fulfilled value should be an empty string.

  Once you have gathered all the necessary information, let the user know you have everything you need. You don't need to make the prediction yourself, just gather the data.
  {
    "response": "<your response>",
    "fulfilled": <true or false (true only if all fields are filled)>,
    "question_type":  <a string or empty if not fulfilled (must be legal, risk, or information security)>
    "user_query":  <a string or empty if not fulfilled>
  }
  **Output your responses in this JSON format:**
  '''

    chatbot_generation_config = {
        "max_output_tokens": 8192,
        "temperature": 1,
        "top_p": 0.95,
        "response_mime_type": "application/json",
    }

    chat_model = GenerativeModel(
        "gemini-2.0-flash-exp",
        system_instruction=system_instruction,
        generation_config=chatbot_generation_config,
    )
    chat = chat_model.start_chat()
    return chat


def get_enterprise_search_results(
    response: discoveryengine.SearchResponse, ) -> List[Dict[str, str | List]]:
    """
    Extract Results from Enterprise Search Response
    """

    count = 0
    return [
        {
            "title":
            result.document.derived_struct_data["title"],
            "htmlTitle":
            result.document.derived_struct_data.get(
                "htmlTitle", result.document.derived_struct_data["title"]),
            "link":
            result.document.derived_struct_data["link"],
            # "displayLink": result.document.derived_struct_data["displayLink"],
            "snippets": [
                s.get("htmlSnippet", s.get("snippet", ""))
                for s in result.document.derived_struct_data.get(
                    "snippets", [])
            ],
            "extractiveAnswers": [
                e["content"] for e in result.document.derived_struct_data.get(
                    "extractive_answers", [])
            ],
            "extractiveSegments": [
                e["content"] for e in result.document.derived_struct_data.get(
                    "extractive_segments", [])
            ],
            # "thumbnailImage": get_thumbnail_image(result.document.derived_struct_data),
            "resultJson":
            discoveryengine.SearchResponse.SearchResult.to_json(
                result, including_default_value_fields=True, indent=2),
        } for result in response.results
    ]


# Vertex Search Logic


def check_question_llm(user_query):
    vertexai.init(project=project_id, location="us-central1")

    system_instruction = '''
  Your job is to check syntax, grammar, spelling, and content of a user inputed query. You will then pass this query to a retrieval augemented generation application.

  Ensure that the user query has spelled the question correctly.
  Your output question must be as close to the user question as possible.

  *Rule*
  If field is not fulfilled value should be an empty string.

  Once you have gathered all the necessary information, let the user know you have everything you need.
  {
    "user_query": "<user_query>",
    "output": "<string or empty if not generated>"
  }
  **Output your responses in this JSON format:**
  '''

    chatbot_generation_config = {
        "max_output_tokens": 8192,
        "temperature": 1,
        "top_p": 0.95,
        "response_mime_type": "application/json",
    }

    user_query_check_model = GenerativeModel(
        "gemini-1.5-flash-001",
        system_instruction=system_instruction,
        generation_config=chatbot_generation_config,
    )
    llm_checked_question = user_query_check_model.generate_content(
        f"<user_input>{user_query}</user_input>")
    return llm_checked_question


def execute_vaiss_query(serving_config, search_query):
    request = discoveryengine.SearchRequest(
        serving_config=serving_config,
        query=search_query,
        page_size=10,
        content_search_spec=content_search_spec,
        query_expansion_spec=discoveryengine.SearchRequest.QueryExpansionSpec(
            condition=discoveryengine.SearchRequest.QueryExpansionSpec.
            Condition.AUTO, ),
        spell_correction_spec=discoveryengine.SearchRequest.
        SpellCorrectionSpec(
            mode=discoveryengine.SearchRequest.SpellCorrectionSpec.Mode.AUTO),
    )
    response_pager = client.search(request)
    # print(response)

    # Parse response
    response = discoveryengine.SearchResponse(
        results=response_pager.results,
        facets=response_pager.facets,
        total_size=response_pager.total_size,
        attribution_token=response_pager.attribution_token,
        next_page_token=response_pager.next_page_token,
        corrected_query=response_pager.corrected_query,
        summary=response_pager.summary,
    )

    results = get_enterprise_search_results(response)
    summary = getattr(response.summary, "summary_text", "")

    output_object_list = []
    try:
        for r in range(0, 5):
            output_object = {
                "Citation": r + 1,
                "Title": results[r]["title"],
                "Link": results[r]["link"],
                "Snippet": results[r]["snippets"]
            }
            output_object_list.append(output_object)
    except Exception as e:
        output_object_list = []
        print("no results", e)
        pass

    # response_text = f"Summary: {response.summary.summary_text}\nCitations: {response.summary.references}"
    return summary, output_object_list


# Main app logic

chat = start_chat_session()

# Streamlit Logic

if "chat" not in st.session_state:
    st.session_state.chat = start_chat_session()
else:
    chat = st.session_state.chat

if "history" not in st.session_state:
    st.session_state.history = st.session_state.chat.history

st.title("AI Chatbot")

for message in st.session_state.history:
    with st.chat_message(message.role):
        st.markdown(message.parts[0].text)

if prompt := st.chat_input("How can I help you today?"):

    with st.chat_message("user"):
        st.markdown(prompt)

    response = chat.send_message(prompt)

    text_output = json.loads(response.candidates[0].content.parts[0].text)

    with st.chat_message("assistant"):
        st.markdown(response.candidates[0].content.parts[0].text)
        # st.markdown(response.candidates[0].content.parts[0].text)
    if text_output["fulfilled"] == True:
        llm_check_response = check_question_llm(text_output["user_query"])
        llm_check_query = json.loads(
            llm_check_response.candidates[0].content.parts[0].text)
        print(llm_check_query)
        if text_output["question_type"].lower() == "legal":
            summary, response_list = execute_vaiss_query(
                legal_serving_config, llm_check_query["output"])
            st.markdown(summary)
            for r in response_list:
                st.json(r)
        elif text_output["question_type"].lower() == "risk":
            summary, response_list = execute_vaiss_query(
                risk_serving_config, llm_check_query["output"])
            st.markdown(summary)
            for r in response_list:
                st.json(r)
        elif text_output["question_type"].lower() == "information security":
            summary, response_list = execute_vaiss_query(
                infosec_serving_config, llm_check_query["output"])
            st.markdown(summary)
            for r in response_list:
                st.json(r)
