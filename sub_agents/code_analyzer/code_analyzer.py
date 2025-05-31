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
import os
from google.adk.agents import Agent
from google.adk.tools import load_artifacts
from tools.code_reader import get_code
from .prompts import CODE_ANALYZER_PROMPT

DEFAULT_MODEL = "gemini-2.5-flash-exp"  # Default model to use if env var is not set

code_analyzer_agent = Agent(
    model=os.getenv("CODE_ANALYZER_AGENT_MODEL", DEFAULT_MODEL),
    name="code_analyzer_agent",
    description="Gets the Apache Spark code from the user and analyzes it. Shares the response report with the user.",
    instruction=CODE_ANALYZER_PROMPT,
    
    tools=[get_code, load_artifacts]
)