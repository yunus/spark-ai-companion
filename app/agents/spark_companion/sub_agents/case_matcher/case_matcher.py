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
"""Code analyzer agent."""
from google.adk.agents import Agent
from google.adk.tools import VertexAiSearchTool, google_search

from app.core.config import settings
from .prompts import CASE_MATCHER_PROMPT

# Tool Instantiation
# You MUST provide your datastore ID here.
_search_tool = (
    VertexAiSearchTool(data_store_id=settings.agent_tools.vertex_ai_data_store_id)
    if settings.agent_tools.vertex_ai_data_store_enabled
    else google_search
)
# --- Agent Definition ---

case_matcher_agent = Agent(
    model=settings.agent_models.case_matcher,
    name="problem_analyzer_agent",
    description="Based on the developer's problem statement and facts on the system, match the problem with the existing cases and provide a list of actions to collect more information. Finally, provides the conclusion and return the control back to the root agent.",
    instruction=CASE_MATCHER_PROMPT,
    tools=[_search_tool],
)
