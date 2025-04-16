# Aura Project

# Aura Backend

This is the backend service for the Aura AI Assistant project. It provides a RESTful API built with FastAPI to handle user authentication, data storage (notes, reminders, logs with embeddings), processing user commands via a hybrid NLU system, and generating context-aware responses using Large Language Models (LLMs).

## Features

* **User Authentication:** Secure user registration and login using JWT tokens. Profile updates (e.g., full name).
* **Data Management & Embeddings:** CRUD operations for various user data types. Notes content is automatically embedded using `sentence-transformers` and stored using `pgvector` for semantic search.
    * Notes (Global & Date-Associated, with embeddings)
    * Reminders (DB storage, basic scheduling placeholders)
    * Spending Logs (with currency support)
    * Investment Notes
    * Medical Logs
* **Hybrid NLU:** Processes user text input using a combination of rule-based matching (for common commands) and fallback to a configured LLM (OpenAI, Gemini, Ollama) for more complex intent classification and entity extraction.
* **LLM Integration:** Configurable integration with different LLM providers for tasks like:
    * Natural Language Understanding (Intent/Entity fallback)
    * Question Answering (using Retrieval-Augmented Generation - RAG)
    * Summarization (Daily logs, Notes, Spending)
    * General conversational fallback.
* **Retrieval-Augmented Generation (RAG):** Uses `pgvector` semantic search on note embeddings to retrieve relevant context from past notes to enhance LLM responses for question answering.
* **Data Querying Intents:** Handles specific requests to retrieve data (e.g., "list my reminders for today", "how much did I spend last month?").
* **Modular Structure:** Organized codebase for better maintainability and scalability.
* **Database Integration:** Uses SQLAlchemy ORM with PostgreSQL and the `pgvector` extension.

## Tech Stack

* **Framework:** FastAPI
* **Database:** PostgreSQL with `pgvector` extension
* **ORM:** SQLAlchemy
* **Vector Embeddings:** `sentence-transformers` (e.g., `all-MiniLM-L6-v2`)
* **Vector Database:** `pgvector` (integrated via PostgreSQL)
* **LLM Integration:** `openai`, `google-generativeai`, `httpx` (for Ollama)
* **Authentication:** JWT (`python-jose`, `PyJWT`), Passlib (for password hashing)
* **Data Validation:** Pydantic
* **Configuration:** `pydantic-settings`, `python-dotenv`
* **Migrations:** Alembic
* **Date Parsing:** `python-dateutil`
* **Language:** Python 3.8+

## Prerequisites

* Python 3.8 or higher
* `pip` (Python package installer)
* PostgreSQL Server (running locally or accessible)
    * **Crucially:** The `vector` extension must be enabled in your target PostgreSQL database (`CREATE EXTENSION IF NOT EXISTS vector;`).
* Git (optional, for cloning)
* Access/API Keys for desired LLM services (OpenAI, Google AI) OR a running Ollama instance.

## Setup Instructions

1.  **Clone the Repository (if applicable):**
    ```bash
    git clone <your-repo-url>
    cd aura-project/backend
    ```
    *(If you don't have a repo, just navigate to your `backend` directory)*

2.  **Create and Activate Virtual Environment:**
    * macOS/Linux:
        ```bash
        python3 -m venv venv
        source venv/bin/activate
        ```
    * Windows:
        ```bash
        python -m venv venv
        .\venv\Scripts\activate
        ```

3.  **Install Dependencies:**
    ```bash
    pip install -r requirements.txt
    ```
    *(Note: This might take some time, especially downloading the sentence-transformer model).*

4.  **Configure PostgreSQL:**
    * Ensure PostgreSQL is running.
    * Connect to PostgreSQL (e.g., using `psql`).
    * Create the database if it doesn't exist (e.g., `CREATE DATABASE aura_db;`).
    * Create the user if needed (e.g., `CREATE USER aura WITH PASSWORD 'your_password';`).
    * Grant privileges (e.g., `GRANT ALL PRIVILEGES ON DATABASE aura_db TO aura;`).
    * **Enable the `vector` extension:**
        ```sql
        \c aura_db
        CREATE EXTENSION IF NOT EXISTS vector;
        ```

5.  **Configure Environment Variables:**
    * Copy the example environment file:
        ```bash
        cp .env.example .env
        ```
    * **Edit `.env`:** Fill in your specific values (see Configuration section below).

6.  **Database Migrations:**
    * Apply database migrations using Alembic to create/update tables based on the models:
        ```bash
        # If you haven't initialized alembic before: alembic init alembic
        # Ensure alembic.ini and alembic/env.py are configured (see previous instructions)
        alembic upgrade head
        ```

## Configuration (`.env` file)

The application uses a `.env` file in the `backend` directory. Key variables:

* `DATABASE_URL`: Your PostgreSQL connection string.
    * Format: `postgresql://<user>:<password>@<host>:<port>/<database_name>`
    * Example: `DATABASE_URL=postgresql://aura:aura@localhost:5432/auradb`
* `SECRET_KEY`: **Replace the default!** Generate a strong secret key (e.g., `python -c 'import secrets; print(secrets.token_hex(32))'`) for JWT security.
* `LOG_LEVEL`: Set logging level (e.g., `INFO`, `DEBUG`). `DEBUG` is useful for development.
* `DEFAULT_LLM_PROVIDER`: Choose the primary LLM to use: `"openai"`, `"gemini"`, or `"ollama"`.
* `OPENAI_API_KEY`: Required if `DEFAULT_LLM_PROVIDER="openai"`. Get from OpenAI.
* `OPENAI_MODEL_NAME`: Specify the OpenAI model (e.g., `"gpt-4o"`, `"gpt-3.5-turbo"`). Defaults to `"gpt-4o"`.
* `GOOGLE_API_KEY`: Required if `DEFAULT_LLM_PROVIDER="gemini"`. Get from Google AI Studio.
* `OLLAMA_BASE_URL`: Required if `DEFAULT_LLM_PROVIDER="ollama"`. The URL where your Ollama instance is running (defaults to `"http://localhost:11434"`).
* `OLLAMA_DEFAULT_MODEL`: The default Ollama model to use (e.g., `"llama3"`, `"mistral"`).

## Running the Server

1.  **Make sure your virtual environment is activated.**
2.  **Ensure PostgreSQL and Ollama (if used) are running.**
3.  **Navigate to the project root directory** (e.g., `aura-project/`).
4.  **Run the Uvicorn server:**
    ```bash
    uvicorn backend.main:app --reload --port 8000
    ```
    * `--reload` enables auto-reloading for development. Remove for production.

The API should now be running at `http://localhost:8000`. Access the interactive API documentation (Swagger UI) at `http://localhost:8000/docs`.

*(Note: The first time you run the app after installing dependencies, the `sentence-transformers` library will download the embedding model, which may take a few moments).*

## API Structure

* The main API is versioned under `/api/v1`.
* Key endpoint groups include:
    * `/auth`: Token generation, user registration.
    * `/users`: User information (`/me` GET/PUT).
    * `/process`: Main endpoint for processing natural language text commands.
    * `/notes`: CRUD for notes, including date/tag/keyword/semantic search (semantic search via `/process` QA).
    * `/reminders`: CRUD for reminders, including filtering.
    * `/spending`: CRUD for spending logs, including date/category filtering.
    * `/investments`: CRUD for investment notes, including date filtering.
    * `/medical`: CRUD for medical logs, including date/type filtering.
    * `/summary`: Endpoints for generating summaries (daily, notes).

## TODO / Future Enhancements

* Implement actual reminder scheduling using a task queue (Celery, RQ).
* Replace placeholder NLU rules with a more robust solution (Rasa, spaCy, fine-tuned LLM).
* Implement full CRUD logic for placeholder functions (spending queries, note search).
* Add proper indexing (e.g., HNSW) for the `pgvector` column via Alembic.
* Implement persistent context management (e.g., Redis).
* Add more comprehensive error handling and user feedback.
* Implement user preferences/settings API and UI.
* Add voice input/output capabilities.

![image](https://github.com/user-attachments/assets/6b8b1936-90f3-4698-af54-e6cac8c040a7)
