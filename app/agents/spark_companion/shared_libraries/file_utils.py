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

"""File-related utility functions for code analysis agent."""

import base64
import binascii
import io
import logging
import mimetypes
from collections.abc import Sequence
import requests
from google.adk.tools import ToolContext
from google.genai.types import Blob, Part

logger = logging.getLogger(__name__)


def download_file_from_url(
    url: str, output_filename: str, tool_context: ToolContext
) -> str:
    """Downloads a file from a URL and stores it in an artifact.

    Args:
      url: The URL to retrieve the file from.
      output_filename: The name of the artifact to store the file in.
      tool_context: The tool context.

    Returns:
      The name of the artifact.
    """
    logger.info("Downloading %s to %s", url, output_filename)
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()

        file_bytes = base64.b64encode(response.content)
        mime_type = response.headers.get("Content-Type", mimetypes.guess_type(url))
        artifact = Part(inline_data=Blob(data=file_bytes, mime_type=mime_type))
        tool_context.save_artifact(filename=output_filename, artifact=artifact)
        logger.info("Downloaded %s to artifact %s", url, output_filename)
        return output_filename

    except requests.exceptions.RequestException as e:
        logger.error("Error downloading file from URL: %s", e)
        return None


def read_text_file_from_path(
    file_path: str, output_filename: str, tool_context: ToolContext
) -> str:
    """Reads a text file from a path and stores it in an artifact.

    Args:
      file_path: The path to the file to read.
      output_filename: The name of the artifact to store the file in.
      tool_context: The tool context.

    Returns:
      The name of the artifact.
    """
    logger.info("Reading %s to %s", file_path, output_filename)
    try:
        with open(file_path, "r", encoding="utf-8") as file:
            file_content = file.read()
        artifact = Part(
            inline_data=Blob(
                data=base64.b64encode(file_content.encode("utf-8")),
                mime_type="text/plain",
            )
        )
        tool_context.save_artifact(filename=output_filename, artifact=artifact)
        logger.info("Saved %s to artifact %s", file_path, output_filename)
        return output_filename
    except Exception as e:
        logger.error("Error reading file from path: %s", e)
        return None


def read_blob_files_from_path(
    file_path: str, output_filename: str, tool_context: ToolContext
) -> str:
    """Reads a blob file from a path and stores it in an artifact.
    Determines the file type by its extension.

    Args:
      file_path: The path to the blob file to read.
      output_filename: The name of the artifact to store the blob file in.
      tool_context: The tool context.

    Returns:
      The name of the artifact.
    """
    logger.info("Reading blob file %s to %s", file_path, output_filename)
    try:
        mime_type, _ = mimetypes.guess_type(file_path)

        with open(file_path, "rb") as file:
            file_bytes = file.read()
        artifact = Part(
            inline_data=Blob(
                data=base64.b64encode(file_bytes.encode("utf-8")), mime_type=mime_type
            )
        )
        tool_context.save_artifact(filename=output_filename, artifact=artifact)
        logger.info("Saved %s to artifact %s", file_path, output_filename)
        return output_filename
    except Exception as e:
        logger.error("Error reading file from path: %s", e)
        return None


def extract_text_from_pdf_artifact(pdf_path: str, tool_context: ToolContext) -> str:
    """Extracts text from a PDF file stored in an artifact"""
    pdf_artifact = tool_context.load_artifact(pdf_path)
    try:
        with io.BytesIO(
            base64.b64decode(pdf_artifact.inline_data.data)
        ) as pdf_file_obj:
            pdf_text = ""
            with pdfplumber.open(pdf_file_obj) as pdf:
                for page in pdf.pages:
                    pdf_text += page.extract_text()
            return pdf_text
    except binascii.Error as e:
        logger.error("Error decoding PDF: %s", e)
        return None


def create_html_redline(text1: str, text2: str) -> str:
    """Creates an HTML redline doc of differences between text1 and text2."""
    d = dmp.diff_match_patch()
    diffs = d.diff_main(text2, text1)
    d.diff_cleanupSemantic(diffs)

    html_output = ""
    for op, text in diffs:
        if op == -1:  # Deletion
            html_output += f'<del style="background-color: #ffcccc;">{text}</del>'
        elif op == 1:  # Insertion
            html_output += f'<ins style="background-color: #ccffcc;">{text}</ins>'
        else:  # Unchanged
            html_output += text

    return html_output


def save_html_to_artifact(
    html_content: str, output_filename: str, tool_context: ToolContext
) -> str:
    """Saves HTML content to an artifact in UTF-8 encoding.

    Args:
      html_content: The HTML content to save.
      output_filename: The name of the artifact to store the HTML in.

    Returns:
      The name of the artifact.
    """
    artifact = Part(text=html_content)
    tool_context.save_artifact(filename=output_filename, artifact=artifact)
    logger.info("HTML content successfully saved to %s", output_filename)
    return output_filename


def main(argv: Sequence[str]) -> None:
    if len(argv) > 1:
        raise app.UsageError("Too many command-line arguments.")


if __name__ == "__main__":
    app.run(main)
