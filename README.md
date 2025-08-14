# Spark AI Companion

The Spark AI Companion is an intelligent assistant designed to help developers diagnose and optimize their Apache Spark and Airflow applications on Google Cloud. It provides an interactive, conversational interface where developers can describe their problems in natural language and receive guided assistance, performance analysis, and best-practice recommendations.

The application leverages the Google Agent Development Kit (ADK) and Gemini models to create a multi-agent system that can analyze user problems, search a knowledge base, and guide users through complex user interfaces like the Spark UI and Google Cloud Console.

## ✨ Features

-   **Conversational Interaction**: Communicate with the agent via text or real-time voice streaming through a web interface.
-   **Intelligent Problem Analysis**: Describe a problem (e.g., "My Dataproc job is slow"), and the agent will identify potential causes.
-   **Guided Troubleshooting**: The agent provides step-by-step instructions to navigate the Spark UI and Google Cloud Console to collect necessary metrics and logs.
-   **Knowledge Base Integration**: Utilizes Vertex AI Search to match user problems against a curated knowledge base of known issues and solutions.
-   **Spark Code Analysis**: The agent can analyze Spark code to identify common performance bottlenecks and suggest improvements (e.g., preferring `coalesce` over `repartition`).
-   **Multi-Agent Architecture**: A host agent coordinates specialized sub-agents for different tasks like case matching and UI analysis.

## 🏗️ Architecture

The application is built with a modern Python stack, designed for scalability and maintainability.

-   **Backend Framework**: **FastAPI** for high-performance, asynchronous API endpoints and WebSocket communication.
-   **AI and Agents**: **Google Agent Development Kit (ADK)** orchestrates the agentic workflow, powered by **Google Gemini** models.
-   **Database**: **PostgreSQL** for data persistence, with **Alembic** for handling schema migrations.
-   **Authentication**: **Firebase Authentication** for securing user access.
-   **Containerization**: **Docker** and **Docker Compose** for consistent development and deployment environments.
-   **Development Tooling**: A comprehensive **Makefile** provides commands for setup, development, code quality checks, and Docker management.

## 🚀 Getting Started

Follow these instructions to get the Spark AI Companion running on your local machine.

### Prerequisites

-   **Python 3.11+**
-   **uv**: The project uses `uv` for fast dependency management. Install it via `pip install uv`.
-   **Docker & Docker Compose**: Required for the containerized setup. The `Makefile` will automatically detect `docker compose` (v2) or `docker-compose` (v1).
-   **Google Cloud SDK**: The `gcloud` CLI is needed for authentication.
-   **Google Cloud Project**: You need a GCP project with the **Vertex AI API** enabled.

### 1. Clone the Repository

```sh
git clone https://github.com/yunus/spark-ai-companion
cd spark-ai-companion
```

### 2. Configuration

The application uses environment variables for configuration. Choose the appropriate environment file based on your development setup:

#### For Docker Compose Development
If you want to run the application using Docker Compose, copy the Docker environment file:

```sh
cp .env.docker .env
```

#### For Local Development (VS Code/PyCharm)
If you want to debug locally using VS Code, PyCharm, or run the application directly on your machine, copy the sample environment file:

```sh
cp .env.sample .env
```

After copying the appropriate file, edit the `.env` file and fill in the required values for your specific environment.

#### **Authentication**

1.  **Google Cloud Authentication**: Log in to your GCP account to set up Application Default Credentials (ADC).
    ```sh
    gcloud auth application-default login
    ```
    This will create a credentials file. Find its path by running:
    ```sh
    gcloud auth application-default print-access-token
    # Look for the credentials file path in the output, typically in ~/.config/gcloud/
    ```
    Set `GOOGLE_APPLICATION_CREDENTIALS` in your `.env` file to this path.

2.  **Firebase Authentication**:
    -   Go to your Firebase project settings > Service accounts.
    -   Generate a new private key and download the JSON file.
    -   Set `FIREBASE_CREDENTIALS_PATH` in your `.env` file to the path of this downloaded file.

#### **Database**

The default `docker-compose.yml` sets up a PostgreSQL database. The default connection string in `.env` should work out-of-the-box for the Docker setup.

```ini
# .env
POSTGRES_DSN="postgresql+psycopg://user:password@localhost:5432/spark-companion"
```

#### **Vertex AI Search**

Update these variables with your Vertex AI Search data store details:

```ini
# .env
AGENT_TOOLS_VERTEX_AI_DATA_STORE_ENABLED=true
AGENT_TOOLS_VERTEX_AI_DATA_STORE_ID="your-datastore-id"
```

### 3. Running the Application

You can run the project either directly on your machine (native) or using Docker.

#### Option A: Running with Docker (Recommended)

This is the easiest way to get started, as it includes the database.

1.  **Set Docker Credential Paths**: In your `.env` file, make sure the `DOCKER_GOOGLE_APPLICATION_CREDENTIALS` variables point to your GCP and Firebase JSON key files on your **host machine**.

    ```ini
    # .env
    DOCKER_GOOGLE_APPLICATION_CREDENTIALS=/path/on/your/host/to/google-credentials.json
    DOCKER_FIREBASE_CREDENTIALS_PATH=/path/on/your/host/to/firebase-credentials.json
    ```

2.  **Build and Start Services**:
    ```sh
    # Build the Docker images
    make docker-build

    # Start the backend API and PostgreSQL database in the background
    make docker-up
    ```

3.  **View Logs**:
    ```sh
    make docker-logs
    ```

The application will be available at `http://localhost:8181`.

#### Option B: Running Locally (Native)

This method requires you to have PostgreSQL running on your host machine.

1.  **Initialize Environment**: This command creates a virtual environment (`.venv`) and installs all dependencies using `uv`.
    ```sh
    make init
    ```

2.  **Run Database Migrations**: This applies the necessary database schemas.
    ```sh
    make upgrade
    ```

3.  **Run the Server**:
    ```sh
    make run
    ```

The application will be available at `http://localhost:8181` with auto-reload enabled.

## 🛠️ Development

A `Makefile` is included to streamline common development tasks.

### Makefile Commands

-   `make help`: Shows a list of all available commands.
-   `make init`: Sets up the local Python virtual environment.
-   `make run`: Runs the FastAPI server locally.
-   `make migrate m="<message>"`: Creates a new database migration file.
-   `make upgrade`: Applies pending database migrations.

**Code Quality:**
-   `make lint`: Checks for linting errors with Ruff.
-   `make format`: Formats code with Black and Ruff.
-   `make check`: Runs both linting and formatting with auto-fixes.

**Docker:**
-   `make docker-build`: Builds the application's Docker image.
-   `make docker-up`: Starts all services using Docker Compose.
-   `make docker-down`: Stops and removes all Docker containers.
-   `make docker-logs`: Tails the logs from the backend container.

**Housekeeping:**
-   `make clean`: Removes the virtual environment and `__pycache__` directories.

### Project Structure

```
.
├── app/                    # Main application source code
│   ├── agents/             # ADK agent definitions and prompts
│   ├── api/                # FastAPI routes, dependencies, and schemas
│   ├── core/               # Core logic, configuration, and exceptions
│   ├── domain/             # Business logic, DTOs, and services
│   └── infrastructure/     # Database models, repositories, external clients
├── migrations/             # Alembic database migration scripts
├── static/                 # Frontend HTML, CSS, and JavaScript files
├── .env                    # Local environment variables (gitignored)
├── .env.example            # Example environment file
├── Dockerfile              # Defines the production Docker image
├── docker-compose.yml      # Defines services for Docker development
├── Makefile                # Development command shortcuts
└── pyproject.toml          # Project metadata and dependencies
```

### Adding New Cases to the Knowledge Base

The agent's ability to solve problems is enhanced by a knowledge base of existing cases. To add a new case:

1.  **Update the Google Sheet**: Add new problem descriptions, analysis steps, and solutions to the [master Google Sheet](https://docs.google.com/spreadsheets/d/1y3ZBCgio05DUl--Vd_z-ORiv3JyVp_8gxTYPVBYqGOo/edit?gid=0#gid=0).
2.  **Sync to BigQuery**: A nightly pipeline syncs the sheet to a native BigQuery table. This can also be triggered manually in the GCP Console.
3.  **Re-index Vertex AI Search**: The Vertex AI Search data store is configured to use the BigQuery table as a data source. It re-indexes nightly, but you can trigger a manual re-index from the Gen App Builder console to make new cases available immediately.

## 📜 License

This project is licensed under the Apache License, Version 2.0. See the [LICENSE](LICENSE) file for details.
