# Cyfuture AI Chatbot

Cyfuture AI Chatbot is an end-to-end customer support solution that leverages LLMs, vector search, and a modern UI to automate complaint handling and information retrieval for Cyfuture. It features document ingestion, semantic search, ticket creation, and a conversational interface.

---

## Features

- **Streamlit Chat UI**: User-friendly chat interface for interacting with the AI assistant.
- **FastAPI Backend**: RESTful API for chatbot, complaint management, and document ingestion.
- **Document Ingestion**: Upload and vectorize PDF documents for semantic search.
- **Milvus Vector Database**: Stores and retrieves document embeddings for context-aware responses.
- **OpenAI Integration**: Uses Azure OpenAI for embeddings and chat completions.
- **SQLite Analytics**: Tracks conversations, complaints, and user details.
- **Session Management**: Each user gets a unique session for personalized experience.

---

## Project Structure

```
.
├── main.py                      # FastAPI backend entrypoint
├── streamlit_chatbot_ui.py      # Streamlit chat UI
├── config.py                    # Configuration classes
├── requirements.txt             # Python dependencies
├── .env                         # Environment variables (API keys, endpoints)
├── data/
│   ├── cyfuture.db              # SQLite database
│   └── Frequently-asked-questions-2022-15092022.pdf  # Example PDF
├── src/
│   ├── bot.py                   # Chatbot logic
│   ├── decorators.py            # Utility decorators
│   ├── prompts.py               # Prompt templates
│   ├── types.py                 # Pydantic models
│   ├── upload_helper.py         # Document ingestion logic
│   ├── utils.py                 # Utility functions
│   └── adapters/                # Integrations (Milvus, OpenAI, SQLite, logging)
└── logs.log                     # Application logs
```

---

## Setup Instructions

### 1. Clone the Repository

```sh
git clone <your-repo-url>
cd customerCare_RAG
```

### 2. Python Environment

Create and activate a Python 3.12+ virtual environment:

```sh
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies

```sh
pip install -r requirements.txt
```

**Note:**  
- You may need to install system dependencies for [Milvus](https://milvus.io/docs/install_standalone-docker.md) and [tiktoken](https://pypi.org/project/tiktoken/).
- The `doclingss` package is required for PDF ingestion.

### 4. Environment Variables

Copy `example.env` to `.env` and fill in your credentials:

```sh
cp example.env .env
```

Edit `.env` and set:
- `OPENAI_API_KEY` (Azure OpenAI key)
- `OPENAI_ENDPOINT` (Azure OpenAI endpoint)
- `MILVUS_HOST` and `MILVUS_PORT` (Milvus server, default: localhost:19530)

### 5. Start Milvus

You must have a running Milvus instance.  
For local development, use Docker:

```sh
wget https://github.com/milvus-io/milvus/releases/download/v2.5.13/milvus-standalone-docker-compose.yml -O docker-compose.yml

sudo docker compose -f docker-compose.yml up -d
```

Or follow [Milvus installation docs](https://milvus.io/docs/install_standalone-docker.md).

### 6. Ingest Documents

Start the backend (see below), then call the upload endpoint to ingest the sample PDF:

```sh
curl -X POST http://localhost:8083/upload_docs
```

### 7. Database Initialization

Create the SQLite database and tables by calling the `/create_tables` endpoint:

```sh
curl -X POST http://localhost:8083/create_tables
```

---

## Running the Application

### 1. Start the FastAPI Backend

```sh
python main.py
```

- The API will be available at [http://localhost:8083](http://localhost:8083)
- Endpoints:
  - `/chatbot` (POST): Chatbot interaction
  - `/complaints` (POST/GET): Complaint management
  - `/upload_docs` (POST): Document ingestion

### 2. Start the Streamlit Chat UI

In a new terminal (with the same virtual environment):

```sh
streamlit run streamlit_chatbot_ui.py
```

- Access the UI at [http://localhost:8501](http://localhost:8501)

---

## Usage

- **Chat**: Ask questions or file complaints via the chat UI.
- **Complaint Tracking**: The bot will collect your details and raise a ticket.
- **Status Check**: Ask for the status of your complaint using the complaint ID.
- **Contextual Answers**: The bot uses ingested documents to answer queries.

---

## Troubleshooting

- **Milvus Connection Errors**: Ensure Milvus is running and accessible at the configured host/port.
- **OpenAI Errors**: Check your API key and endpoint in `.env`.
- **PDF Ingestion Issues**: Make sure `doclingss` and its dependencies are installed.
- **Database Issues**: The SQLite DB is created automatically; check file permissions if errors occur.

---

## Extending

- Add more PDF documents to the `data/` folder and re-run the `/upload_docs` endpoint.
- Customize prompt logic in [`src/prompts.py`](src/prompts.py).
- Extend complaint analytics or user models in [`src/types.py`](src/types.py).

---

## Authors

- Abhishek M Sharma
- AI/ML Software Developer Engineer