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

"""Spark UI Analyzer agent."""

from google.adk.agents import Agent
from google.adk.tools import google_search

from .prompts import UI_ANALYZER_PROMPT
from app.core.config import settings

spark_ui_agent = Agent(
    model=settings.agent_models.ui_analyzer,  # type: ignore
    name="ui_analyzer_agent",
    description="Via screen sharing analyzes the Apache Spark UI. Shares the response report with the user.",
    instruction=UI_ANALYZER_PROMPT,
    tools=[google_search],
)
