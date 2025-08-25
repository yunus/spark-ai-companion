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

from google.adk.agents import Agent
from google.adk.tools import agent_tool

from app.agents.spark_companion.sub_agents.case_matcher import case_matcher
import app.agents.spark_companion.prompts as prompts
from app.core.logging import get_logger
from app.core.config import settings


logger = get_logger(__name__)

logger.info("creating the host agent.")

root_agent = Agent(
    name="AiCompanionHostAgent",
    model=settings.agent_models.root,  # type: ignore
    description="User-facing ai companion root agent. It delegates the requests to tools and other specialised agents",
    instruction=prompts.ROOT_AGENT_INSTRUCTION,
    global_instruction=prompts.GLOBAL_INSTRUCTION,
    # sub_agents=[ui_analyzer.spark_ui_agent],
    # generate_content_config=types.GenerateContentConfig(response_modalities=["AUDIO"]),
    tools=[agent_tool.AgentTool(agent=case_matcher.case_matcher_agent)],
)

logger.info(
    f"ADK Host Agent '{root_agent.name}' created with model '{settings.agent_models.root}'"
)
