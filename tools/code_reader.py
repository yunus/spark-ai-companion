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

"""'code_reader' tool for Code Analyzer agent"""

import logging

from google.adk.tools import ToolContext
from shared_libraries import file_utils

logger = logging.getLogger(__name__)


def get_code(file_path: str, artifact_name: str, tool_context: ToolContext) -> dict:
    """Reads the code into artifacts to use later for code analysis

    Args:
      file_path: path to the code file provided by the user.
      artifact_name: the artifact name to save the code to.
      tool_context: ToolContext object.

    Returns:
      A dict with "status" and (optional) "error_message" keys.
    """

    output_filename = file_utils.read_text_file_from_path(
        file_path, artifact_name, tool_context
    )

    logger.info("Saved artifact %s", output_filename)
    return {"status": "ok"}
