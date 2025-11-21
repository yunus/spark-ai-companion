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

import asyncio
import base64
import json
import logging
import os
import warnings
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, WebSocket
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from google.adk.agents.live_request_queue import LiveRequestQueue
from google.adk.agents.run_config import RunConfig
from google.adk.events import Event, EventActions
from google.adk.runners import InMemoryRunner
from google.genai import types as genai_types

# import agentops
from google.genai.types import Blob, Content, Modality, Part
from starlette.websockets import WebSocketDisconnect

from spark_companion.agent import root_agent

warnings.filterwarnings("ignore", category=UserWarning, module="pydantic")
# Load Gemini API Key
load_dotenv()
# Configure logging
logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
)

logger = logging.getLogger(__name__)

# Disable uvicorn access logs
logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
logging.getLogger("google_adk").setLevel(logging.INFO)

# agentops.init(
#     api_key=os.getenv("AGENTOPS_API_KEY"),  # Your AgentOps API Key
#     trace_name="ai-companion-trace"  # Optional: A name for your trace
#     # auto_start_session=True is the default.
#     # Set to False if you want to manually control session start/end.
# )

APP_NAME = "AI Companion"


async def start_agent_session(user_id: str, is_audio=True):
    """Starts an agent session"""

    # Create a Runner
    runner = InMemoryRunner(
        app_name=APP_NAME,
        agent=root_agent,
    )
    logger.info(f"The model of the root agent is {root_agent.model}")

    # Create a Session
    session = await runner.session_service.create_session(
        app_name=APP_NAME,
        user_id=user_id,  # Replace with actual user ID
    )

    # Set response modality
    speech_config = genai_types.SpeechConfig(language_code="en-US")

    modality = Modality.AUDIO if is_audio else Modality.TEXT
    run_config = RunConfig(
        response_modalities=[modality],
        speech_config=speech_config,
        output_audio_transcription=genai_types.AudioTranscriptionConfig(),  # with this, audio responses are transcriped to text additionally.
        input_audio_transcription=genai_types.AudioTranscriptionConfig(),
        # proactivity=genai_types.ProactivityConfig(proactive_audio=True), -> supported with native audio model. This enables model to ignore messages that are not directed to it.
        # enable_affective_dialog=True, # -> responds to emotional expressions for more nuanced conversations. native-dialog model only
    )

    # Create a LiveRequestQueue for this session
    live_request_queue = LiveRequestQueue()

    # Start agent session
    live_events = runner.run_live(
        session=session,
        live_request_queue=live_request_queue,
        run_config=run_config,
    )
    return live_events, live_request_queue, runner, session


async def agent_to_client_messaging(websocket, live_events):
    """Agent to client communication"""
    while True:
        try:
            async for event in live_events:
                # If the turn complete or interrupted, send it
                if event.turn_complete or event.interrupted:
                    message = {
                        "turn_complete": event.turn_complete,
                        "interrupted": event.interrupted,
                    }
                    await websocket.send_text(json.dumps(message))
                    logger.info(f"[AGENT TO CLIENT]: {message}")
                    continue

                # Handle input transcription (User's voice)
                if hasattr(event, "input_transcription") and event.input_transcription:
                     transcription = event.input_transcription
                     if hasattr(transcription, "text"):
                         transcription_text = transcription.text
                     else:
                         transcription_text = str(transcription)
                     
                     message = {
                        "mime_type": "application/input_transcription",
                        "data": transcription_text,
                    }
                     await websocket.send_text(json.dumps(message))
                     logger.debug(f"[AGENT TO CLIENT]: input_transcription: {transcription_text}")
                     continue

                # Handle output transcription (Model's voice)
                if hasattr(event, "output_transcription") and event.output_transcription:
                     transcription = event.output_transcription
                     if hasattr(transcription, "text"):
                         transcription_text = transcription.text
                     else:
                         transcription_text = str(transcription)
                     
                     message = {
                        "mime_type": "text/plain",
                        "data": transcription_text,
                    }
                     await websocket.send_text(json.dumps(message))
                     logger.debug(f"[AGENT TO CLIENT]: output_transcription: {transcription_text}")
                     continue

                # Read the Content and its first Part
                part: Part = (
                    event.content and event.content.parts and event.content.parts[0]
                )
                if not part:
                    continue

                # If it's audio, send Base64 encoded audio data
                is_audio = part.inline_data and part.inline_data.mime_type.startswith(
                    "audio/pcm"
                )  # type: ignore
                if is_audio:
                    audio_data = part.inline_data and part.inline_data.data
                    if audio_data:
                        message = {
                            "mime_type": "audio/pcm",
                            "data": base64.b64encode(audio_data).decode("ascii"),
                        }
                        await websocket.send_text(json.dumps(message))
                        logger.debug(
                            f"[AGENT TO CLIENT]: audio/pcm: {len(audio_data)} bytes."
                        )
                        continue

                # If it's a function call, send it
                if part.function_call:
                    message = {
                        "mime_type": "application/tool_use",
                        "tool_name": part.function_call.name,
                    }
                    await websocket.send_text(json.dumps(message))
                    logger.info(f"[AGENT TO CLIENT]: tool_use: {part.function_call.name}")
                    continue

                # If it's text, send it (this handles output audio transcription too)
                if part.text:
                    message = {"mime_type": "text/plain", "data": part.text}
                    await websocket.send_text(json.dumps(message))
                    logger.debug(f"[AGENT TO CLIENT]: text/plain: {message}")
                    continue
        except WebSocketDisconnect:
            logger.info("Agent disconnected from client messaging.")
            break


async def client_to_agent_messaging(websocket, live_request_queue, runner, session):
    """Client to agent communication"""
    while True:
        try:
            # Decode JSON message
            message_json = await websocket.receive_text()
            message = json.loads(message_json)
            mime_type = message["mime_type"]
            data = message["data"]

            # Send the message to the agent
            if mime_type == "text/plain":
                # Send a text message
                content = Content(role="user", parts=[Part.from_text(text=data)])
                live_request_queue.send_content(content=content)
                logger.debug(f"[CLIENT TO AGENT]: {data}")
            elif mime_type == "audio/pcm" or mime_type == "image/jpeg":
                # Send an audio or image data
                decoded_data = base64.b64decode(data)
                live_request_queue.send_realtime(
                    Blob(data=decoded_data, mime_type=mime_type)
                )
                logger.debug(
                    f"[CLIENT TO AGENT]: {mime_type}: {len(decoded_data)} bytes"
                )
            elif mime_type == "application/json":
                message_data = json.loads(data)
                if message_data.get("event") == "screen_sharing":
                    status = message_data.get("status")
                    logger.info(f"Received screen sharing status: {status}")
                    state_delta = {"screen_sharing": status}
                    event = Event(
                        author="user", actions=EventActions(state_delta=state_delta)
                    )
                    await runner.session_service.append_event(
                        session=session, event=event
                    )
            else:
                raise ValueError(f"Mime type not supported: {mime_type}")
        except WebSocketDisconnect:
            logger.info("Client disconnected from agent messaging.")
            break


# @asynccontextmanager
# async def lifespan(app: FastAPI):
#     """Lifespan context manager for the application."""
#     # Startup
#     yield
#     # Shutdown
#     logger.info("Application is shutting down...")
#     tasks = [t for t in asyncio.all_tasks() if t is not asyncio.current_task()]

#     for task in tasks:
#         if not task.done():
#             task.cancel()

#     logger.info(f"Cancelling {len(tasks)} tasks")
#     try:
#         await asyncio.gather(*tasks, return_exceptions=True)
#     except asyncio.CancelledError:
#         logger.info("Shutdown tasks cancelled.")

app = FastAPI()

STATIC_DIR = Path("static")
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.get("/")
async def root():
    """Serves the index.html"""
    return FileResponse(os.path.join(STATIC_DIR, "index.html"))


@app.websocket("/ws/{user_id}")
async def websocket_endpoint(
    websocket: WebSocket, user_id: int, is_audio: str = "false"
):
    """Client websocket endpoint"""
    try:
        # Wait for client connection
        await websocket.accept()
        logger.info(f"Client #{user_id} connected, audio mode: {is_audio}")

        # Start agent session
        live_events, live_request_queue, runner, session = await start_agent_session(
            str(user_id), is_audio.lower() == "true"
        )
        # Start tasks
        agent_to_client_task = asyncio.create_task(
            agent_to_client_messaging(websocket, live_events)
        )
        client_to_agent_task = asyncio.create_task(
            client_to_agent_messaging(websocket, live_request_queue, runner, session)
        )

        # Wait until the websocket is disconnected or an error occurs
        tasks = [agent_to_client_task, client_to_agent_task]
        try:
            done, _ = await asyncio.wait(tasks, return_when=asyncio.FIRST_EXCEPTION)
            logger.info(f"Client await for #{user_id} finished")
            # Check for exceptions in the completed tasks and re-raise them.
            # This makes the error handling explicit.
            for task in done:
                if task.exception():
                    task.result()  # This will raise the exception from the task
            logger.info(
                f"Client await for #{user_id} finished without task exceptions."
            )
        except Exception as e:
            logger.exception(f"A websocket communication task failed: {e}")
        except asyncio.CancelledError as e:
            logger.info(f"background tasks cancelled {e}")
        finally:
            # Cancel all tasks
            for task in tasks:
                logger.info(f"cancelling task in web socket endpoint {task}")
                if not task.done():
                    task.cancel()
                    try:
                        await task
                    except asyncio.CancelledError:
                        logger.info("tasks are getting cancelled")
                        pass

            # Close LiveRequestQueue
            live_request_queue.close()

            # Close websocket connection
            try:
                # Check if the websocket is still in a state where it can be closed
                if websocket.client_state.value != 3:  # 3 is the CLOSED state
                    await websocket.close()
            except Exception as e:
                logger.error(f"Error closing websocket: {e}")

    except Exception as e:
        logger.error(f"Error in websocket endpoint: {e}")
        raise
    finally:
        logger.info(f"Client #{user_id} disconnected")
