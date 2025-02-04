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


def display_ground_truth_eval_result(eval_result, metrics=None):
    """Display the ground truth evaluation results."""

    summary_metrics, report_df, _ = eval_result
    metrics_df = pd.DataFrame.from_dict(summary_metrics, orient="index").T
    if metrics:
        metrics_df = metrics_df.filter([
            metric for metric in metrics_df.columns
            if any(selected_metric in metric for selected_metric in metrics)
        ])
        report_df = report_df.filter([
            metric for metric in report_df.columns
            if any(selected_metric in metric for selected_metric in metrics)
        ])

    # Display the title with Markdown for emphasis
    display(Markdown(f"## {title}"))

    # Display the metrics DataFrame
    display(Markdown("### Summary Metrics"))
    display(metrics_df)

    # Display the detailed report DataFrame
    display(Markdown("### Report Metrics"))
    display(report_df)


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


def save_ground_truth_eval_result(
        eval_result,
        metrics=None,
        file_name=f"ground_truth_{EXPERIMENT_NAME}_data.csv"):
    """Save the ground truth evaluation results to CSV file."""
    title, summary_metrics, report_df = eval_result
    metrics_df = pd.DataFrame.from_dict(summary_metrics, orient="index").T
    if metrics:
        metrics_df = metrics_df.filter([
            metric for metric in metrics_df.columns
            if any(selected_metric in metric for selected_metric in metrics)
        ])
        report_df = report_df.filter([
            metric for metric in report_df.columns
            if any(selected_metric in metric for selected_metric in metrics)
        ])
    report_df.to_csv(file_name, index=False)


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


# Define prompt and system instructions

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
entities = ["Seimens", "Lukas Geiger", "fujikara cars", "Mark Larson"]

responses = []
prompts = []
references = []
for entity in entities:
    response = execute_grounded_gemini_call(
        prompt=prompt.format(entity=entity),
        system_instructions=system_instructions,
        model="gemini-2.0-exp")  # gemini-1.5-flash-002-high-fidelity
    prompts.append(
        f"Instructions: {system_instructions}\n\nPrompt: {prompt.format(entity=entity)}"
    )
    responses.append(response.candidates[0].content.parts[0].text)

print(f"Gemini GwGS calls complete. Responses: \n{responses}")

# EVALUATIONS

### Custom Template. Your own definition of custom_text_quality.

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

## Pointwise model as a judge evaluation

# Setup

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

## Ground Truth Evaluations (Pairwise)

# Identify ground truth

ground_truth = [
    """**Headline:** Siemens Faces Allegations of Bribery, Fraud, and Violations of the Foreign Corrupt Practices Act (FCPA)

**Bribery and Corruption:**

*   Between March 2001 and December 2007, Siemens allegedly made approximately 4,283 illegal payments to government officials, totaling roughly $1.4 billion USD.  These payments allegedly resulted in approximately $1.1 billion USD in profits for the company.  The payments were allegedly made in connection with various projects across multiple countries, including Nigeria (telecommunications), Italy (power plants), Greece (communications), Venezuela (metro projects), China (metro and transmission lines), Israel (power plants), Bangladesh (mobile services), and Argentina.  While not illegal under German law at the time (and even tax-deductible), the payments violated the OECD Convention (ratified by Germany in 1999) and the FCPA (after Siemens listed on the New York Stock Exchange in 2001).  Siemens allegedly failed to implement necessary internal controls to prevent these payments and may have even encouraged and rewarded them.
*   In Greece, a bribery scandal emerged concerning deals with government officials related to security systems and purchases by OTE during the 1990s and the 2004 Olympics.  Allegations included bribes potentially reaching €100 million to secure state contracts.  Charges of money laundering and bribery were filed in July 2008, and one former Siemens executive fled to Germany to avoid arrest in 2009.  A former transport minister admitted to receiving payments from Siemens in a Swiss bank account.
*   In Iraq, Siemens and its subsidiaries allegedly made millions of dollars in improper payments related to the United Nations Oil for Food Program.
*   A 2024 settlement addressed allegations that Siemens used inaccurate data in an energy performance contract analysis for the Hamtramck Housing Commission, resulting in the U.S. paying a larger subsidy than it should have.

**Fraud:**

*   The inaccurate data used in the Hamtramck Housing Commission energy performance contract analysis constituted an allegation of fraud.  The settlement resolved allegations that Siemens relied on inaccurate data, leading to an inflated U.S. subsidy payment.

**Money Laundering:**

*   The Greek bribery scandal included charges of money laundering.  The alleged illegal payments to government officials between 2001 and 2007 were also subject to investigations for money laundering.

**Tax Evasion:**

*   Investigations into Siemens included allegations of tax evasion.

**Other Allegations:**

*   Investigations involved allegations of public corruption, criminal breaches of fiduciary duty (including embezzlement), and violations of the FCPA.  Siemens pleaded guilty in a U.S. federal court to charges of failing to maintain adequate internal controls and failing to comply with the FCPA's books and records provisions.  The company cooperated with investigations.

**Note:** This report is current as of December 5th, 2024.  Information may change over time.
""", """
There are no results found for Lukas Geiger.
""",
    """**Headline:** Fujikura Ltd. Pleads Guilty to Price-Fixing Conspiracy in Auto Parts Industry

Fujikura Ltd., a Tokyo-based manufacturer of automotive wire harnesses, pleaded guilty to a conspiracy to fix prices of automotive wire harnesses and related products.  The company agreed to pay a $20 million criminal fine, and to cooperate with an ongoing Department of Justice investigation.  The price-fixing allegedly occurred from at least January 2006 to February 2010, involving rigged bids and allocation of wire harness supply.  The conspiracy involved meetings in Japan to reach collusive agreements, and further communications to monitor and enforce these agreements.  Two Fujikura executives, Ryoji Fukudome and Toshihiko Nagashima, were later indicted for their roles in the conspiracy.  The price-fixing affected wire harnesses sold to Fuji Heavy Industries (Subaru) for installation in cars sold in the U.S. and elsewhere.  In a separate settlement, Fujikura agreed to pay $7.14 million to resolve allegations of price-fixing in a class action lawsuit.  This was part of a larger settlement involving multiple auto parts suppliers, with total payments exceeding $14.5 million to resolve allegations of price-fixing.  The DOJ's investigation into anti-competitive conduct in the automotive industry resulted in guilty pleas from three other foreign companies and over $748 million in fines.
""", """**Allegations Against Mark Larson**

**Sexual Assault Allegation:**  In March 2024, Mark Larson, a police officer with the Metropolitan Police Service, resigned while under investigation for sexual assault.  A hearing determined that, had he remained in service, he would have been dismissed for breaching professional behavior standards related to ""Discreditable Conduct"" following a sexual assault of a female.

**Negligent Homicide and Related Charges:** In 2004, Mark Theodore Larson was convicted of negligent homicide (a felony), driving under the influence, speeding, and failure to wear a seatbelt (misdemeanors).  The conviction was upheld on appeal.

**Lewdness Charges:** In January 2023, Mark A. Larson was found guilty of two counts of open and gross lewdness following a jury trial.

**Note:**  This information is current as of December 5th, 2024.  Further information may become available.
"""
]

# Create dataframe
ground_truth_eval_dataset = pd.DataFrame({
    "prompt": prompts,
    "response": responses,
    "reference": ground_truth,
})

# Optional: Custom metric

comprehensive_report_correctness_prompt_template = """
You are a professional negative news analyst. Your job is to score writing responses according to pre-defined evaluation criteria.

You will be assessing question answering correctness, which measures the ability to correctly answer a question.

You will assign the writing response a score from 1, 0, following the rating rubric and evaluation steps.

### Criteria:
Reference claim alignment: The response should contain all categories from the reference and should not contain categories that are not present in the reference.
Categories reference negative news categories such as 'Bribery' or 'Money Laundering'.

### Rating Rubric:
1 (correct): The response contains all categories from the reference and does not contain categories that are not present in the reference.
0 (incorrect): The response does not contain all categories from the reference, or the response contains categories that are not present in the reference.

### Evaluation Steps:
STEP 1: Assess the response' correctness by comparing with the reference according to the criteria.
STEP 2: Score based on the rubric.

Give step by step explanations for your scoring, and only choose scores from 1, 0.

# User Inputs and AI-generated Response
## User Inputs
### Prompt
{prompt}

## Reference
{reference}

## AI-generated Response
{response}
"""

comprehensive_report_correctness = PointwiseMetric(
    metric="comprehensive_report_correctness",
    metric_prompt_template=comprehensive_report_correctness_prompt_template,
)

# Run evaluations on grounded truth

ground_truth_answer_eval_task = EvalTask(
    dataset=ground_truth_eval_dataset,
    metrics=[comprehensive_report_correctness, "rouge", "bleu", "exact_match"],
    experiment="test-gwgs-ground-truth")

ground_truth_result = ground_truth_answer_eval_task.evaluate()
print(ground_truth_result)

display_eval_result(ground_truth_result)

save_eval_result(ground_truth_result)
