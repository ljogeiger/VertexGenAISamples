# Vertex AI Generative AI Samples - ljogeiger

This repository contains a collection of sample code and demos showcasing the capabilities of Google Cloud's Vertex AI services (including generative AI). It's designed to provide practical examples and starting points for developers and businesses looking to leverage the power of generative AI in their applications.

The content of this repository is maintained by a Google Cloud Customer Engineer for demo purposes.

## Repository Structure

The repository is organized into the following main sections:

Directory structure:
└── ljogeiger-VertexGenAISamples/
    ├── sample_output/
    │   ├── test-gwgs_data.csv
    │   └── custom_search_api_output.txt
    ├── README
    ├── public/
    │   ├── nl2sql/
    │   │   └── [External]_Text_BisonNLtoBQSQL.ipynb
    │   ├── open_source/
    │   │   ├── mistral_chat.py
    │   │   ├── haiku_call_transcript_summary.py
    │   │   └── predict_mistral_v0-3.py
    │   ├── gemini/
    │   │   ├── gemini_call_transcript_summary.py
    │   │   └── multimodal_streaming.py
    │   ├── embeddings/
    │   │   └── multimodalembedding/
    │   │       ├── predict_request_gapic.py
    │   │       └── requirements.txt
    │   ├── use_cases/
    │   │   ├── negative_articles/
    │   │   │   └── gwgs_evaluation_script.py
    │   │   └── sports/
    │   │       ├── sport_video_evaluations.ipynb
    │   │       └── chapterization_gemini_sports.py
    │   ├── misc/
    │   │   ├── video_intelligence_api.py
    │   │   ├── vision_api.py
    │   │   └── custom_search_api_text.py
    │   ├── grounding/
    │   │   ├── google_search/
    │   │   │   ├── grounding_google_search_keywords.py
    │   │   │   ├── grounding_with_google_search_keywords_v1.py
    │   │   │   └── simple_gwgs_gemini_prompt.py
    │   │   └── agent_builder/
    │   │       ├── mistral_plus_vaiss.py
    │   │       ├── grounding_with_vertex_search_and_vertex_search_retrieval.py
    │   │       ├── collect_params_gemini_plus_vaiss.py
    │   │       └── multi_datastore_agent.py
    │   └── mlops/
    │       └── DeployMistralPipeline.ipynb
    ├── README.md
    └── utils/
        └── files/
            ├── images/
            └── text/
                ├── request.json
                └── vision_request.json


## Getting Started

1.  **Clone the repository:**

    ```bash
    git clone <repository URL>
    ```

2.  **Navigate to the demo you're interested in:**

    ```bash
    cd public/gemini/gemini_call_transcript_summary
    ```

3.  **Follow the instructions within the demo's folder.** Each demo may have specific setup requirements (e.g., installing dependencies, setting up a Vertex AI project, configuring API keys).

## Contributing

Contributions to the public demos and examples are welcome! Please follow these guidelines:

1.  Fork the repository.
2.  Create a new branch for your feature or bug fix.
3.  Make your changes and test thoroughly.
4.  Submit a pull request, clearly describing your changes and the problem they solve.

## Disclaimer

The code in this repository is provided for demonstration purposes only. It is not intended for production use without thorough testing and adaptation.

## Contact

For questions or feedback regarding this repository, please contact lukasgeiger@google.com
