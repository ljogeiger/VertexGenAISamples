from google.cloud import discoveryengine_v1 as discoveryengine
import pandas as pd
import vertexai
from vertexai.evaluation import EvalTask, PointwiseMetric, PointwiseMetricPromptTemplate, MetricPromptTemplateExamples
from IPython.display import Markdown, display, HTML
import plotly.graph_objects as go

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


def save_eval_result(eval_result,
                     metrics=None,
                     file_name=f"{EXPERIMENT_NAME}_data.csv"):
    """Save the evaluation results to CSV file."""
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
    metrics_table.to_csv(file_name, index=False)


def display_explanations(df, metrics=None, n=1):
    style = "white-space: pre-wrap; width: 800px; overflow-x: auto;"
    df = df.sample(n=n)
    if metrics:
        df = df.filter([
            "instruction", "context", "reference", "completed_prompt",
            "response"
        ] + [
            metric
            for metric in df.columns if any(selected_metric in metric
                                            for selected_metric in metrics)
        ])

    for index, row in df.iterrows():
        for col in df.columns:
            display(HTML(f"{col}: {row[col]}"))
        display(HTML(""))


def plot_radar_plot(eval_results, max_score=5, metrics=None):
    fig = go.Figure()

    for eval_result in eval_results:
        title, summary_metrics, report_df = eval_result

        if metrics:
            summary_metrics = {
                k: summary_metrics[k]
                for k, v in summary_metrics.items()
                if any(selected_metric in k for selected_metric in metrics)
            }

        fig.add_trace(
            go.Scatterpolar(
                r=list(summary_metrics.values()),
                theta=list(summary_metrics.keys()),
                fill="toself",
                name=title,
            ))

    fig.update_layout(
        polar=dict(radialaxis=dict(visible=True, range=[0, max_score])),
        showlegend=True)

    fig.show()


def plot_bar_plot(eval_results, metrics=None):
    fig = go.Figure()
    data = []

    for eval_result in eval_results:
        title, summary_metrics, _ = eval_result
        if metrics:
            summary_metrics = {
                k: summary_metrics[k]
                for k, v in summary_metrics.items()
                if any(selected_metric in k for selected_metric in metrics)
            }

        data.append(
            go.Bar(
                x=list(summary_metrics.keys()),
                y=list(summary_metrics.values()),
                name=title,
            ))

    fig = go.Figure(data=data)

    # Change the bar mode
    fig.update_layout(barmode="group")
    fig.show()


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
Your job is to provide a comprehensive and professional report of negative news articles for a given input-name.
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

# Your own definition of custom_text_quality.

metric_prompt_template = PointwiseMetricPromptTemplate(
    criteria={
        "professional":
        "Sentences flow smoothly and are easy to read, avoiding awkward phrasing or run-on sentences. Ideas and sentences connect logically, using transitions effectively where needed.",
    },
    rating_rubric={
        "5": "The response performs well.",
        "2.5": "The response is somewhat aligned.",
        "0": "The response falls short.",
    },
)

custom_text_quality = PointwiseMetric(
    metric="custom_text_quality",
    metric_prompt_template=metric_prompt_template,
)

# Get responses from Gemini with GwGS
entities = ["Seimens", "Lukas Geiger", "fujikara cars", "Mark Larson"]

responses = []
prompts = []
for entity in entities:
    response = execute_grounded_gemini_call(
        prompt=prompt.format(entity=entity),
        system_instructions=system_instructions,
        model="gemini-1.5-flash-002-high-fidelity")
    prompts.append(
        f"Instructions: {system_instructions}\n\nPrompt: {prompt.format(entity=entity)}"
    )
    responses.append(response.candidates[0].content.parts[0].text)

print(f"Gemini GwGS calls complete. Responses: \n{responses}")

eval_dataset = pd.DataFrame({
    "prompt": prompts,
    "response": responses,
})

# Run evaluations
# For existing prompt template (MetricPromptTemplateExamples) details
# go here: https://cloud.google.com/vertex-ai/generative-ai/docs/models/metrics-templates#structure-template

eval_task = EvalTask(
    dataset=eval_dataset,
    metrics=[
        custom_text_quality,
        MetricPromptTemplateExamples.Pointwise.FLUENCY,
        MetricPromptTemplateExamples.Pointwise.COHERENCE,
        MetricPromptTemplateExamples.Pointwise.INSTRUCTION_FOLLOWING,
    ],
    experiment=EXPERIMENT_NAME)

eval_result = eval_task.evaluate()

# Display the results

display_eval_result(eval_result)

# Save the results to a CSV file

save_eval_result(eval_result)

# Create a bar chart with summary results

eval_results = []
eval_results.append(
    ("GwGS", eval_result.summary_metrics, eval_result.metrics_table))
plot_bar_plot(
    eval_results,
    metrics=[
        f"{metric}/mean"
        # Edit your list of metrics here if you used other metrics in evaluation.
        for metric in [
            "custom_text_quality", "fluency", "coherence",
            "instruction_following"
        ]
    ],
)
