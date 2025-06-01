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
import os
from datetime import date
from typing import Optional
import logging

from google.genai import types

from google.adk.agents import Agent
from google.adk.agents.callback_context import CallbackContext
from google.adk.tools import google_search, agent_tool
from sub_agents.case_matcher import case_matcher
from sub_agents.spark_ui_analyzer import ui_analyzer 

from . import prompts

from dotenv import load_dotenv

# Environment Loading (as before)
dotenv_path = os.path.join(os.path.dirname(__file__), '..', '.env')
load_dotenv(dotenv_path=dotenv_path, override=True)

logger = logging.getLogger(__name__)
print(f"ROOT_AGENT_MODEL: {os.getenv('ROOT_AGENT_MODEL')}")
# --- Agent Definition ---


logger.info(f"creating the host agent.")
host_agent = Agent(
    name="AiCompanionHostAgent",
    model=os.getenv("ROOT_AGENT_MODEL"), # type: ignore
    description="User-facing ai companion root agent. It delegates the requests to tools and other specialised agents",
    instruction=prompts.ROOT_AGENT_INSTRUCTION,
    global_instruction=prompts.GLOBAL_INSTRUCTION,
    sub_agents=[ui_analyzer.spark_ui_agent],
    #generate_content_config=types.GenerateContentConfig(response_modalities=["AUDIO"]),
    tools=[google_search, agent_tool.AgentTool(agent=case_matcher.case_matcher_agent)],
)
logger.info(f"ADK Host Agent '{host_agent.name}' created with model '{os.getenv("ROOT_AGENT_MODEL")}'.")
   