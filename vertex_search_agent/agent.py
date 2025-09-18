from google.adk.agents import Agent
from google.adk.tools import VertexAiSearchTool
from dotenv import load_dotenv

import os

load_dotenv()


# Configuration
DATASTORE_ID = os.getenv("VERTEX_AI_SEARCH_DATASTORE")


vertex_agent = Agent(
    name="vertex_search_agent",
    model="gemini-2.5-flash",
    instruction="Answer questions using Vertex AI Search to find information from internal documents. Always cite sources when available.",
    description="Enterprise document search assistant with Vertex AI Search capabilities",
    tools=[VertexAiSearchTool(data_store_id=DATASTORE_ID)]
)