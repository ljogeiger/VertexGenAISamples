from google.cloud import discoveryengine_v1 as discoveryengine
import pandas as pd
import vertexai
from vertexai.evaluation import EvalTask, PointwiseMetric, PointwiseMetricPromptTemplate
from IPython.display import Markdown, display

# Initialize set variables and clients
PROJECT_NUMBER = "807698966239"
PROJECT_ID = "vertexsearchconversations"
LOCATION = "us-central1"
EXPERIMENT_NAME = "test-gwgs"  # Must follow regex [a-z0-9][a-z0-9-]{0,127}

client = discoveryengine.GroundedGenerationServiceClient()

vertexai.init(project=PROJECT_NUMBER, location=LOCATION)

# Helper functions for Evaluations


def display_eval_result(eval_result, metrics=None):
    """Display the evaluation results."""
    summary_metrics, metrics_table = (
        eval_result.summary_metrics,
        eval_result.metrics_table,
    )

    metrics_df = pd.DataFrame.from_dict(summary_metrics, orient="index").T
    if metrics:
        metrics_df = metrics_df.filter([
            metric for metric in metrics_df.columns
            if any(selected_metric in metric for selected_metric in metrics)
        ])
        metrics_table = metrics_table.filter([
            metric for metric in metrics_table.columns
            if any(selected_metric in metric for selected_metric in metrics)
        ])

    # Display the summary metrics
    display(Markdown("### Summary Metrics"))
    display(metrics_df)
    # Display the metrics table
    display(Markdown("### Row-based Metrics"))
    display(metrics_table)


def execute_grounded_gemini_call(
    prompt,
    system_instructions,
    model="gemini-1.5-flash-002",
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

    # Handle the response
    return response
    # print(response)


# Define prompt and system instructions

prompt = """
Find allegations with the following company:
<input-name>
{entity}
</input-name>
"""

system_instructions = """
Your job is to provide a comprehensive report of negative news articles for a given input-name.
Search thoroughly across all time.
Provide a date news article you cite.

Follow these steps:
1. If input-name is a company map it to the legal business name.
2. Summarize and interpret Google Search results for a given input-name and all activies listed below. If there are no results for a given activity just skip it.
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

# Conduct evaluations

# Your own definition of text_quality.

metric_prompt_template = PointwiseMetricPromptTemplate(
    criteria={
        "fluency":
        "Sentences flow smoothly and are easy to read, avoiding awkward phrasing or run-on sentences. Ideas and sentences connect logically, using transitions effectively where needed.",
        "entertaining":
        "Short, amusing text that incorporates emojis, exclamations and questions to convey quick and spontaneous communication and diversion.",
    },
    rating_rubric={
        "1": "The response performs well on both criteria.",
        "0": "The response is somewhat aligned with both criteria",
        "-1": "The response falls short on both criteria",
    },
)

text_quality = PointwiseMetric(
    metric="text_quality",
    metric_prompt_template=metric_prompt_template,
)

# Get responses from Gemini with GwGS
entities = ["Seimens", "Lukas Geiger", "fujikara cars", "Mark Larson"]

responses = []
for entity in entities:
    response = execute_grounded_gemini_call(
        prompt=prompt.format(entity=entity),
        system_instructions=system_instructions,
        model="gemini-1.5-flash-002-high-fidelity")
    responses.append(response.candidates[0].content.parts[0].text)

print(f"Gemini GwGS calls complete. Responses: \n{responses}")

eval_dataset = pd.DataFrame({
    "response": responses,
})

# Run evaluations

eval_task = EvalTask(dataset=eval_dataset,
                     metrics=[text_quality, "fluency"],
                     experiment=EXPERIMENT_NAME)

eval_result = eval_task.evaluate()

# Display the results

display_eval_result(eval_result)
