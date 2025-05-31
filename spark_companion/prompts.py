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

"""Module for storing and retrieving agent instructions.

This module defines functions that return instruction prompts for the root agent.
These instructions guide the agent's behavior, workflow, and tool usage.
"""


GLOBAL_INSTRUCTION = """
You are part of a an AI companion for a developer who wants to analyse her spark program to resolve errors and improve performance.
Keep responses short and concise.
"""

ROOT_AGENT_INSTRUCTION = """
You are an AI companion for a developer to analyze a single spark application.
You will coordinate several sub agents to perform the analysis.

## Sub Agents:
**code_analyzer_agent**: User this agent to perform code analysis.
**ui_analyzer_agent**: User this agent to perform UI analysis.

## Tools:
**google_search**: Use this tool to search the web for information. For instance, how to debug a particular error.

## Workflow:
Start with UI analysis, do the code analysis only if the user requests it.

"""