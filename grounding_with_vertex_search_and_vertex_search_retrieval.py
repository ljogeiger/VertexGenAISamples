import base64, re
import vertexai
from vertexai.generative_models import GenerativeModel, Part, FinishReason, Tool
import vertexai.preview.generative_models as generative_models
from google.cloud import discoveryengine as discoveryengine
from google.api_core.client_options import ClientOptions
from typing import List

PROJECT_ID = "cloud-llm-preview4"  # @param {type:"string"}
LOCATION = "global"

def generate():
  vertexai.init(project="cloud-llm-preview4", location="us-central1")
  tools = [
      Tool.from_retrieval(
          retrieval=generative_models.grounding.Retrieval(
              source=generative_models.grounding.VertexAISearch(datastore="projects/cloud-llm-preview4/locations/global/collections/default_collection/dataStores/pwc-basic_1712090697116"),
              disable_attribution=False,
          )
      ),
  ]
  prompt = """
  INSTRUCTIONS: Use the grounding retrival tool on my datastore. Your job is to search for the following search term: Donald Trump. Return the top 10 results.


The output should include the top 10 websites:
- The retrieval result link
- Summary of the content of the result
  """

  model = GenerativeModel("gemini-1.5-pro-preview-0409", tools=tools)
  response = model.generate_content(
      [prompt],
      generation_config=generation_config,
      safety_settings=safety_settings,
      stream=False,
  )

  print(response)
  print(response.text)

generation_config = {
    "max_output_tokens": 8192,
    "temperature": 1,
    "top_p": 0.95,
}

safety_settings = {
    generative_models.HarmCategory.HARM_CATEGORY_HATE_SPEECH: generative_models.HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
    generative_models.HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: generative_models.HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
    generative_models.HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: generative_models.HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
    generative_models.HarmCategory.HARM_CATEGORY_HARASSMENT: generative_models.HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
}

# generate()


def search_sample(
    project_id: str,
    location: str,
    data_store_id: str,
    search_query: str,
) -> List[discoveryengine.SearchResponse]:
    #  For more information, refer to:
    # https://cloud.google.com/generative-ai-app-builder/docs/locations#specify_a_multi-region_for_your_data_store
    client_options = (
        ClientOptions(api_endpoint=f"{location}-discoveryengine.googleapis.com")
        if LOCATION != "global"
        else None
    )

    # Create a client
    client = discoveryengine.SearchServiceClient(client_options=client_options)

    # The full resource name of the search engine serving config
    # e.g. projects/{project_id}/locations/{location}/dataStores/{data_store_id}/servingConfigs/{serving_config_id}
    serving_config = client.serving_config_path(
        project=project_id,
        location=location,
        data_store=data_store_id,
        serving_config="default_config",
    )

    # Optional: Configuration options for search
    # Refer to the `ContentSearchSpec` reference for all supported fields:
    # https://cloud.google.com/python/docs/reference/discoveryengine/latest/google.cloud.discoveryengine_v1.types.SearchRequest.ContentSearchSpec
    content_search_spec = discoveryengine.SearchRequest.ContentSearchSpec(
        # For information about snippets, refer to:
        # https://cloud.google.com/generative-ai-app-builder/docs/snippets
        snippet_spec=discoveryengine.SearchRequest.ContentSearchSpec.SnippetSpec(
            return_snippet=True
        ),
        # For information about search summaries, refer to:
        # https://cloud.google.com/generative-ai-app-builder/docs/get-search-summaries
    )

    # Refer to the `SearchRequest` reference for all supported fields:
    # https://cloud.google.com/python/docs/reference/discoveryengine/latest/google.cloud.discoveryengine_v1.types.SearchRequest
    request = discoveryengine.SearchRequest(
        serving_config=serving_config,
        query=search_query,
        page_size=10, # adjust this to get more results
        content_search_spec=content_search_spec,
        query_expansion_spec=discoveryengine.SearchRequest.QueryExpansionSpec(
            condition=discoveryengine.SearchRequest.QueryExpansionSpec.Condition.AUTO,
        ),
        spell_correction_spec=discoveryengine.SearchRequest.SpellCorrectionSpec(
            mode=discoveryengine.SearchRequest.SpellCorrectionSpec.Mode.AUTO
        ),
        filter="lr:\"lang_en\"" #lang_zh-CN
    )


    response = client.search(request)
    # print(response)
    return response


query = "WOO Ying-ming" #廉政專員 - WOO Ying-ming

response = search_sample(PROJECT_ID, LOCATION, "pwc-basic_1712090697116", query)

retrieved_data = ""

for result in response.results:
  id = result.id
  data = result.document.derived_struct_data
  if not data:
      continue

  snippets: List[str] = [
      re.sub("<[^>]*>", "", snippet_item.get("snippet", ""))
      for snippet_item in data.get("snippets", [])
      if snippet_item.get("snippet")
  ]

  if snippets:
      link = data.get("link", "Unknown Link")
      title = data.get("title", "Unknown Title")
      retrieved_data += f"RESULT #{int(id) + 1} - {link}\n"
      retrieved_data += f"--- Snippets from Document: {title} ---\n{''.join(snippets)}\n\n"

print(retrieved_data)
