# Wanderlust AI — Travel Concierge

Wanderlust AI is an intelligent, full-stack travel concierge agent built with the **Google Agent Development Kit (ADK)** and deployed on **Google Cloud Agent Platform**. It helps travelers discover destination recommendations, calculate itemized trip budgets, record allergy guidelines in cross-session memory, generate custom postcard images and promotional videos, and save personalized trip itineraries.

![Wanderlust AI Live Demo](./demo.gif)

---

## 🌟 Key Capabilities & Integrated Services

Wanderlust AI is built on the following Google Cloud services, AI models, and real-time APIs:

* **Vertex AI Agent Platform & ADK (`google-adk`)**: Powered by `gemini-2.5-flash` running on Google Cloud Agent Engine.
* **Cross-Session Memory Bank**: Integrated with **Vertex AI Memory Bank Service** (`331295497832628224`) using `PreloadMemoryTool` to automatically record, retain, and respect user dietary allergies, medical sensitivities, and travel preferences across chat sessions.
* **Google Cloud Firestore**: Connected to Firestore collections (`destinations` and `trips`) in `qwiklabs-gcp-03-fbbc64cbc886` to retrieve destination catalog items and store saved travel itineraries.
* **Google Cloud Storage**: Public assets bucket (`travel-concierge-assets-03fbbc`) used for storing generated destination images and videos.
* **Postcard Image Generation**: Uses Google's `gemini-3.1-flash-lite-image` model in the `global` region to create custom destination postcards saved to Cloud Storage and ADK `ToolContext` artifacts.
* **Short Promo Video Generation**: Uses Google's Omni model (`gemini-omni-flash-preview`) in the `global` region via the Vertex AI Interactions API to generate promotional travel videos.
* **Python Code Execution & Budget Calculator**: Uses Python code execution (`BuiltinTools.code_execution`) to perform math and itemized budget calculations for flights, accommodations, dining, and activities.
* **Live Exchange Rates**: Real-time currency conversions (`USD`, `EUR`, `JPY`, `GBP`, `IDR`, `ISK`) via Frankfurter API.
* **Local Time & Weather**: Real-time time zone lookups via `zoneinfo` and live weather forecasts via Open-Meteo.
* **A2UI v0.8 Rich Layouts**: Structured output rendering using A2UI schema components (`Card`, `Column`, `Row`, `Text`, `Image`, `Video`, `Button`).
* **FastAPI Proxy & Web UI**: Includes a minimal FastAPI backend proxy (`frontend/main.py`) and a responsive, dark-mode-enabled chat web interface (`frontend/static/index.html`).

---

## 🛠️ Project Structure

```text
.
├── app/
│   ├── agent.py               # Root ADK agent configuration & instructions
│   ├── tools.py               # Custom tools (Firestore, GCS, GenAI Image/Video, Exchange Rates)
│   ├── a2ui_utils.py          # A2UI callback and surface update builders
│   └── memory_bank_tool.py    # Vertex AI Memory Bank tool integration
├── frontend/
│   ├── main.py                # FastAPI proxy server for Agent Platform
│   ├── requirements.txt       # Frontend dependencies (fastapi, uvicorn, google-genai)
│   ├── Dockerfile             # Container definition for Cloud Run deployment
│   └── static/
│       └── index.html         # Dialogue UI with prompt chips, dark mode & avatars
├── agents-cli-manifest.yaml    # Agents CLI deployment manifest
└── demo.gif                   # Live demonstration recording
```

---

## 🚀 Local Setup & Running Instructions

### Prerequisites
* Python 3.11+
* Google Cloud SDK (`gcloud`) authenticated to your GCP project with Vertex AI, Firestore, and GCS enabled.

### 1. Environment Setup

Clone the repository and install dependencies:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r frontend/requirements.txt
```

Set required environment variables:

```bash
export GOOGLE_CLOUD_PROJECT="qwiklabs-gcp-03-fbbc64cbc886"
export GOOGLE_CLOUD_LOCATION="us-central1"
export GOOGLE_GENAI_USE_VERTEXAI="true"
```

### 2. Running the Agent Locally

Run the ADK agent playground or local CLI server:

```bash
agents-cli run
```

### 3. Running the Frontend Locally

Start the FastAPI proxy server pointing at your agent:

```bash
cd frontend
export AGENT_DIRECTORY="app"
uvicorn main:app --host 0.0.0.0 --port 8080 --reload
```

Open your browser to the local server address displayed by Uvicorn (default: `http://127.0.0.1:8080`).

---

## ☁️ Deployment Commands

### Deploying the Agent Engine Backend

Deploy the root ADK agent to Vertex AI Agent Platform:

```bash
agents-cli deploy --project $GOOGLE_CLOUD_PROJECT --region $GOOGLE_CLOUD_LOCATION
```

### Deploying the Web Frontend to Cloud Run

Build and deploy the proxy UI to Cloud Run:

```bash
gcloud run deploy travel-concierge-frontend \
  --source ./frontend \
  --project $GOOGLE_CLOUD_PROJECT \
  --region $GOOGLE_CLOUD_LOCATION \
  --allow-unauthenticated \
  --set-env-vars AGENT_ENGINE_RESOURCE_NAME="projects/$GOOGLE_CLOUD_PROJECT/locations/$GOOGLE_CLOUD_LOCATION/reasoningEngines/<RESOURCE_ID>",AGENT_DIRECTORY="app"
```
