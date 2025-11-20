# Copyright 2025 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Top level agent for data agent multi-agents.

-- it coordinates the overall flow
-- first it delegates the request to the sub agent code analyser
-- then it handles control to screenshot analyser for Spark UI analysis
"""

import logging
import os

from dotenv import load_dotenv
from google.adk.agents import Agent
from google.adk.tools import agent_tool
from google.adk.tools import google_search

from tools.dataproc_helper import (
    get_dataproc_cluster_detatils,
    get_dataproc_cluster_list,
)
from tools.dataproc_job_helper import get_dataproc_job_output
from vertex_search_agent.agent import vertex_agent

from . import prompts

# Environment Loading (as before)
dotenv_path = os.path.join(os.path.dirname(__file__), "..", ".env")
load_dotenv(dotenv_path=dotenv_path, override=True)

logger = logging.getLogger(__name__)
print(f"ROOT_AGENT_MODEL: {os.getenv('ROOT_AGENT_MODEL')}")
# --- Agent Definition ---

search_agent = Agent(
    model='gemini-2.5-flash',
    name='GoogleSearchAgent',
    instruction="""
    You're a specialist in Google Search. You can search the web and return the results.
    """,
    tools=[google_search],
)

logger.info("creating the host agent.")
root_agent = Agent(
    name="AiCompanionHostAgent",
    model=os.getenv("ROOT_AGENT_MODEL"),  # type: ignore
    description="User-facing ai companion root agent. It delegates the requests to tools and other specialised agents",
    instruction=prompts.ROOT_AGENT_INSTRUCTION,
    # generate_content_config=types.GenerateContentConfig(response_modalities=["AUDIO"]),
    tools=[
        agent_tool.AgentTool(agent=vertex_agent),
        agent_tool.AgentTool(agent=search_agent),
        # get_dataproc_cluster_list,
        # get_dataproc_cluster_detatils,
        # get_dataproc_job_output,
    ],
)
logger.info(
    f"ADK Host Agent '{root_agent.name}' created with model '{os.getenv('ROOT_AGENT_MODEL')}'."
)
