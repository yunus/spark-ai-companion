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
import os
from google.adk.agents import Agent
from google.adk.tools import load_artifacts
from tools.blob_reader import get_blob
from .prompts import UI_ANALYZER_PROMPT

from dotenv import load_dotenv
# Environment Loading (as before)
dotenv_path = os.path.join(os.path.dirname(__file__), '..', '..', '.env')
load_dotenv(dotenv_path=dotenv_path, override=True)

print(f"UI_ANALYZER_AGENT_MODEL: {os.getenv('UI_ANALYZER_AGENT_MODEL')}")

spark_ui_agent = Agent(
    model=os.getenv("UI_ANALYZER_AGENT_MODEL", "gemini-2.5-flash-exp"), # type: ignore
    name="ui_analyzer_agent",
    description="Via screen sharing analyzes the Apache Spark UI. Shares the response report with the user.",
    instruction=UI_ANALYZER_PROMPT,
    tools=[get_blob, load_artifacts]
)