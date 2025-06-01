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
from google.adk.tools import google_search
from .prompts import CASE_MATCHER_PROMPT
import logging

from dotenv import load_dotenv

# Environment Loading (as before)
dotenv_path = os.path.join(os.path.dirname(__file__), '..', '..', '.env')
load_dotenv(dotenv_path=dotenv_path, override=True)

logger = logging.getLogger(__name__)
print(f"CASE_MATCHER_AGENT_MODEL: {os.getenv('CASE_MATCHER_AGENT_MODEL')}")
# --- Agent Definition ---

DEFAULT_MODEL = "gemini-2.5-flash-exp"  # Default model to use if env var is not set

case_matcher_agent = Agent(
    model=os.getenv("CASE_MATCHER_AGENT_MODEL", DEFAULT_MODEL),
    name="problem_analyzer_agent",
    description=
    "Based on the developer's problem statement and facts on the system, match the problem with the existing cases and provide a list of actions to collect more information. Finally, provides the conclusion and return the control back to the root agent.",
    instruction=CASE_MATCHER_PROMPT,
    tools=[google_search])
