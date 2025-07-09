# ADK documentation

TITLE: Navigating to Agent Project Parent Directory (Java)
DESCRIPTION: This console output illustrates the recommended directory structure for a Java-based ADK agent project, indicating the parent directory to navigate into (e.g., `project_folder/`) before running the agent. It shows a typical Maven/Gradle project layout.
SOURCE: https://github.com/google/adk-docs/blob/main/docs/get-started/quickstart.md#_snippet_17

LANGUAGE: console
CODE:
```
project_folder/                <-- navigate to this directory
├── pom.xml (or build.gradle)
├── src/
├── └── main/
│       └── java/
│           └── agents/
│               └── multitool/
│                   └── MultiToolAgent.java
└── test/
```

----------------------------------------

TITLE: Launching ADK Dev UI (Python)
DESCRIPTION: This shell command launches the ADK Dev UI, a web-based interface for interacting with and inspecting your agent. For Windows users encountering `_make_subprocess_transport NotImplementedError`, the `--no-reload` option is suggested as a workaround.
SOURCE: https://github.com/google/adk-docs/blob/main/docs/get-started/quickstart.md#_snippet_13

LANGUAGE: shell
CODE:
```
adk web
```

----------------------------------------

TITLE: Install Agent Development Kit
DESCRIPTION: Instructions for installing the Google Agent Development Kit (ADK) using various package managers for different programming languages.
SOURCE: https://github.com/google/adk-docs/blob/main/docs/index.md#_snippet_0

LANGUAGE: Python
CODE:
```
pip install google-adk
```

LANGUAGE: XML
CODE:
```
<dependency>
    <groupId>com.google.adk</groupId>
    <artifactId>google-adk</artifactId>
    <version>0.1.0</version>
</dependency>
```

LANGUAGE: Gradle
CODE:
```
dependencies {
    implementation 'com.google.adk:google-adk:0.1.0'
}
```

----------------------------------------

TITLE: Create Live Audio Run Tool in Java
DESCRIPTION: This Java code defines the `LiveAudioRun` class, which demonstrates how to conduct a live voice conversation with an agent using the Google ADK. It sets up audio input from a microphone and output to speakers, configures the agent runner for bidirectional streaming with audio responses, and manages concurrent tasks for capturing audio input and playing back the agent's audio output. It utilizes `javax.sound.sampled` for audio processing and `io.reactivex.rxjava3` for event stream handling.
SOURCE: https://github.com/google/adk-docs/blob/main/docs/get-started/streaming/quickstart-streaming-java.md#_snippet_6

LANGUAGE: java
CODE:
```
package samples.liveaudio;

import com.google.adk.agents.LiveRequestQueue;
import com.google.adk.agents.RunConfig;
import com.google.adk.events.Event;
import com.google.adk.runner.Runner;
import com.google.adk.sessions.InMemorySessionService;
import com.google.common.collect.ImmutableList;
import com.google.genai.types.Blob;
import com.google.genai.types.Modality;
import com.google.genai.types.PrebuiltVoiceConfig;
import com.google.genai.types.Content;
import com.google.genai.types.Part;
import com.google.genai.types.SpeechConfig;
import com.google.genai.types.VoiceConfig;
import io.reactivex.rxjava3.core.Flowable;
import java.io.ByteArrayOutputStream;
import java.io.InputStream;
import java.net.URL;
import javax.sound.sampled.AudioFormat;
import javax.sound.sampled.AudioInputStream;
import javax.sound.sampled.AudioSystem;
import javax.sound.sampled.DataLine;
import javax.sound.sampled.LineUnavailableException;
import javax.sound.sampled.Mixer;
import javax.sound.sampled.SourceDataLine;
import javax.sound.sampled.TargetDataLine;
import java.util.UUID;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.ConcurrentHashMap;
import java.util.concurrent.ConcurrentMap;
import java.util.concurrent.Executors;
import java.util.concurrent.Future;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.atomic.AtomicBoolean;
import agents.ScienceTeacherAgent;

/** Main class to demonstrate running the {@link LiveAudioAgent} for a voice conversation. */
public final class LiveAudioRun {
  private final String userId;
  private final String sessionId;
  private final Runner runner;

  private static final javax.sound.sampled.AudioFormat MIC_AUDIO_FORMAT =
      new javax.sound.sampled.AudioFormat(16000.0f, 16, 1, true, false);

  private static final javax.sound.sampled.AudioFormat SPEAKER_AUDIO_FORMAT =
      new javax.sound.sampled.AudioFormat(24000.0f, 16, 1, true, false);

  private static final int BUFFER_SIZE = 4096;

  public LiveAudioRun() {
    this.userId = "test_user";
    String appName = "LiveAudioApp";
    this.sessionId = UUID.randomUUID().toString();

    InMemorySessionService sessionService = new InMemorySessionService();
    this.runner = new Runner(ScienceTeacherAgent.ROOT_AGENT, appName, null, sessionService);

    ConcurrentMap<String, Object> initialState = new ConcurrentHashMap<>();
    var unused =
        sessionService.createSession(appName, userId, initialState, sessionId).blockingGet();
  }

  private void runConversation() throws Exception {
    System.out.println("Initializing microphone input and speaker output...");

    RunConfig runConfig =
        RunConfig.builder()
            .setStreamingMode(RunConfig.StreamingMode.BIDI)
            .setResponseModalities(ImmutableList.of(new Modality("AUDIO")))
            .setSpeechConfig(
                SpeechConfig.builder()
                    .voiceConfig(
                        VoiceConfig.builder()
                            .prebuiltVoiceConfig(
                                PrebuiltVoiceConfig.builder().voiceName("Aoede").build())
                            .build())
                    .languageCode("en-US")
                    .build())
            .build();

    LiveRequestQueue liveRequestQueue = new LiveRequestQueue();

    Flowable<Event> eventStream =
        this.runner.runLive(
            runner.sessionService().createSession(userId, sessionId).blockingGet(),
            liveRequestQueue,
            runConfig);

    AtomicBoolean isRunning = new AtomicBoolean(true);
    AtomicBoolean conversationEnded = new AtomicBoolean(false);
    ExecutorService executorService = Executors.newFixedThreadPool(2);

    // Task for capturing microphone input
    Future<?> microphoneTask =
        executorService.submit(() -> captureAndSendMicrophoneAudio(liveRequestQueue, isRunning));

    // Task for processing agent responses and playing audio
    Future<?> outputTask =
        executorService.submit(
            () -> {
              try {
                processAudioOutput(eventStream, isRunning, conversationEnded);
              } catch (Exception e) {
                System.err.println("Error processing audio output: " + e.getMessage());
                e.printStackTrace();
                isRunning.set(false);
              }
            });

    // Wait for user to press Enter to stop the conversation
    System.out.println("Conversation started. Press Enter to stop...");
    System.in.read();

    System.out.println("Ending conversation...");
    isRunning.set(false);

    try {
      // Give some time for ongoing processing to complete
      microphoneTask.get(2, TimeUnit.SECONDS);
      outputTask.get(2, TimeUnit.SECONDS);
    } catch (Exception e) {

```

----------------------------------------

TITLE: Initializing LlmAgent with Claude 3 Sonnet on Vertex AI in Java
DESCRIPTION: This snippet demonstrates how to configure and instantiate an LlmAgent in Java, integrating it with Claude 3 Sonnet hosted on Google Cloud's Vertex AI. It involves setting up the AnthropicOkHttpClient with a VertexBackend, specifying the region and GCP project ID, and using GoogleCredentials. The `createAgent` method returns a configured LlmAgent instance, and the `main` method shows how to call it and handle potential IO exceptions.
SOURCE: https://github.com/google/adk-docs/blob/main/docs/agents/models.md#_snippet_34

LANGUAGE: Java
CODE:
```
            // Model name for Claude 3 Sonnet on Vertex AI (or other versions)
            String claudeModelVertexAi = "claude-3-7-sonnet"; // Or any other Claude model

            // Configure the AnthropicOkHttpClient with the VertexBackend
            AnthropicClient anthropicClient = AnthropicOkHttpClient.builder()
                .backend(
                    VertexBackend.builder()
                        .region("us-east5") // Specify your Vertex AI region
                        .project("your-gcp-project-id") // Specify your GCP Project ID
                        .googleCredentials(GoogleCredentials.getApplicationDefault())
                        .build())
                .build();

            // Instantiate LlmAgent with the ADK Claude wrapper
            LlmAgent agentClaudeVertexAi = LlmAgent.builder()
                .model(new Claude(claudeModelVertexAi, anthropicClient)) // Pass the Claude instance
                .name("claude_vertexai_agent")
                .instruction("You are an assistant powered by Claude 3 Sonnet on Vertex AI.")
                // .generateContentConfig(...) // Optional: Add generation config if needed
                // ... other agent parameters
                .build();
            
            return agentClaudeVertexAi;
        }

        public static void main(String[] args) {
            try {
                LlmAgent agent = createAgent();
                System.out.println("Successfully created agent: " + agent.name());
                // Here you would typically set up a Runner and Session to interact with the agent
            } catch (IOException e) {
                System.err.println("Failed to create agent: " + e.getMessage());
                e.printStackTrace();
            }
        }
    }
```

----------------------------------------

TITLE: Implement Loop Agent with Conditional Termination in ADK
DESCRIPTION: This example demonstrates how to use a `LoopAgent` in Google ADK to execute sub-agents repeatedly. It includes a custom `CheckCondition` agent that escalates an event to terminate the loop when a specific state condition is met, or after a maximum number of iterations.
SOURCE: https://github.com/google/adk-docs/blob/main/docs/agents/multi-agents.md#_snippet_3

LANGUAGE: Python
CODE:
```
# Conceptual Example: Loop with Condition
from google.adk.agents import LoopAgent, LlmAgent, BaseAgent
from google.adk.events import Event, EventActions
from google.adk.agents.invocation_context import InvocationContext
from typing import AsyncGenerator

class CheckCondition(BaseAgent): # Custom agent to check state
    async def _run_async_impl(self, ctx: InvocationContext) -> AsyncGenerator[Event, None]:
        status = ctx.session.state.get("status", "pending")
        is_done = (status == "completed")
        yield Event(author=self.name, actions=EventActions(escalate=is_done)) # Escalate if done

process_step = LlmAgent(name="ProcessingStep") # Agent that might update state['status']

poller = LoopAgent(
    name="StatusPoller",
    max_iterations=10,
    sub_agents=[process_step, CheckCondition(name="Checker")]
)
# When poller runs, it executes process_step then Checker repeatedly
# until Checker escalates (state['status'] == 'completed') or 10 iterations pass.
```

----------------------------------------

TITLE: ADK RunConfig Runtime Parameters API Reference
DESCRIPTION: This API documentation details the various configurable parameters available within the `RunConfig` class. It provides comprehensive information on each parameter's purpose, its corresponding data types in both Python and Java, default values, and specific usage notes, including experimental features and current limitations.
SOURCE: https://github.com/google/adk-docs/blob/main/docs/runtime/runconfig.md#_snippet_1

LANGUAGE: APIDOC
CODE:
```
RunConfig Parameters:
- speech_config:
  Python Type: Optional[types.SpeechConfig]
  Java Type: SpeechConfig (nullable via @Nullable)
  Default (Py / Java): None / null
  Description: Configures speech synthesis (voice, language) using the SpeechConfig type.
- response_modalities:
  Python Type: Optional[list[str]]
  Java Type: ImmutableList<Modality>
  Default (Py / Java): None / Empty ImmutableList
  Description: List of desired output modalities (e.g., Python: ["TEXT", "AUDIO"]; Java: uses structured Modality objects).
- save_input_blobs_as_artifacts:
  Python Type: bool
  Java Type: boolean
  Default (Py / Java): False / false
  Description: If true, saves input blobs (e.g., uploaded files) as run artifacts for debugging/auditing.
- streaming_mode:
  Python Type: StreamingMode
  Java Type: *Currently not supported*
  Default (Py / Java): StreamingMode.NONE / N/A
  Description: Sets the streaming behavior: NONE (default), SSE (server-sent events), or BIDI (bidirectional).
- output_audio_transcription:
  Python Type: Optional[types.AudioTranscriptionConfig]
  Java Type: AudioTranscriptionConfig (nullable via @Nullable)
  Default (Py / Java): None / null
  Description: Configures transcription of generated audio output using the AudioTranscriptionConfig type.
- max_llm_calls:
  Python Type: int
  Java Type: int
  Default (Py / Java): 500 / 500
  Description: Limits total LLM calls per run. 0 or negative means unlimited (warned); sys.maxsize raises ValueError.
- support_cfc:
  Python Type: bool
  Java Type: *Currently not supported*
  Default (Py / Java): False / N/A
  Description: **Python:** Enables Compositional Function Calling. Requires streaming_mode=SSE and uses the LIVE API. **Experimental.**
```

----------------------------------------

TITLE: Define ADK LlmAgent with MCPToolset for Filesystem Operations
DESCRIPTION: This Python code defines an `LlmAgent` using the `google.adk` library, integrating `MCPToolset` to enable filesystem operations. It configures the agent to use the `gemini-2.0-flash` model and connects to a local filesystem server via `npx @modelcontextprotocol/server-filesystem`. The snippet highlights the importance of providing an absolute path for the target folder that the MCP server can access.
SOURCE: https://github.com/google/adk-docs/blob/main/docs/tools/mcp-tools.md#_snippet_2

LANGUAGE: python
CODE:
```
# ./adk_agent_samples/mcp_agent/agent.py
import os # Required for path operations
from google.adk.agents import LlmAgent
from google.adk.tools.mcp_tool.mcp_toolset import MCPToolset, StdioServerParameters

# It's good practice to define paths dynamically if possible,
# or ensure the user understands the need for an ABSOLUTE path.
# For this example, we'll construct a path relative to this file,
# assuming '/path/to/your/folder' is in the same directory as agent.py.
# REPLACE THIS with an actual absolute path if needed for your setup.
TARGET_FOLDER_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "/path/to/your/folder")
# Ensure TARGET_FOLDER_PATH is an absolute path for the MCP server.
# If you created ./adk_agent_samples/mcp_agent/your_folder,

root_agent = LlmAgent(
    model='gemini-2.0-flash',
    name='filesystem_assistant_agent',
    instruction='Help the user manage their files. You can list files, read files, etc.',
    tools=[
        MCPToolset(
            connection_params=StdioServerParameters(
                command='npx',
                args=[
                    "-y",  # Argument for npx to auto-confirm install
                    "@modelcontextprotocol/server-filesystem",
                    # IMPORTANT: This MUST be an ABSOLUTE path to a folder the
                    # npx process can access.
                    # Replace with a valid absolute path on your system.
                    # For example: "/Users/youruser/accessible_mcp_files"
                    # or use a dynamically constructed absolute path:
                    os.path.abspath(TARGET_FOLDER_PATH),
                ],
            ),
            # Optional: Filter which tools from the MCP server are exposed
            # tool_filter=['list_directory', 'read_file']
        )
    ],
)
```

----------------------------------------

TITLE: Define find_shopping_items ADK Tool
DESCRIPTION: Defines a Python function `find_shopping_items` that acts as an ADK Tool. It queries an e-commerce API using `call_vector_search` to find items based on a list of user queries. The function returns a dictionary containing status and found items, adhering to explicit typing and verbose docstring requirements for ADK Tools.
SOURCE: https://github.com/google/adk-docs/blob/main/examples/python/notebooks/shop_agent.ipynb#_snippet_6

LANGUAGE: python
CODE:
```
from typing import Dict

def find_shopping_items(queries: list[str]) -> Dict[str, str]:
    """
    Find shopping items from the e-commerce site with the specified list of
    queries.

    Args:
        queries: the list of queries to run.
    Returns:
        A dict with the following one property:
            - "status": returns the following status:
                - "success": successful execution
            - "items": items found in the e-commerce site.
    """
    url = "https://www.ac0.cloudadvocacyorg.joonix.net/api/query"

    items = []
    for query in queries:
        result = call_vector_search(
            url=url,
            query=query,
            rows=3,
        )
        items.extend(result["items"])

    print("-----")
    print(f"User queries: {queries}")
    print(f"Found: {len(items)} items")
    print("-----")

    return items
```

----------------------------------------

TITLE: Creating LlmAgent with Claude Model (Java)
DESCRIPTION: This Java snippet provides the initial imports and class structure for creating an LlmAgent that utilizes the ADK's Claude wrapper. It demonstrates the necessary dependencies for integrating Anthropic's client, Vertex AI backend, and Google authentication, setting up the foundation for an agent that interacts with Claude on Vertex AI.
SOURCE: https://github.com/google/adk-docs/blob/main/docs/agents/models.md#_snippet_33

LANGUAGE: java
CODE:
```
import com.anthropic.client.AnthropicClient;
import com.anthropic.client.okhttp.AnthropicOkHttpClient;
import com.anthropic.vertex.backends.VertexBackend;
import com.google.adk.agents.LlmAgent;
import com.google.adk.models.Claude; // ADK's wrapper for Claude
import com.google.auth.oauth2.GoogleCredentials;
import java.io.IOException;

// ... other imports

public class ClaudeVertexAiAgent {

    public static LlmAgent createAgent() throws IOException {
```

----------------------------------------

TITLE: Get Session API Method (Java)
DESCRIPTION: Retrieves a specific session based on application name, user ID, and session ID. It supports an optional configuration to filter included events and returns a ReactiveX Single containing the session data.
SOURCE: https://github.com/google/adk-docs/blob/main/docs/api-reference/java/com/google/adk/sessions/InMemorySessionService.html#_snippet_2

LANGUAGE: APIDOC
CODE:
```
getSession(String appName, String userId, String sessionId, Optional<GetSessionConfig> configOpt)
  Description: Retrieves a specific session, optionally filtering the events included.
  Returns: io.reactivex.rxjava3.core.Single<ListEventsResponse>
```

----------------------------------------

TITLE: Initiating OAuth Authentication Request (Python)
DESCRIPTION: When no valid credentials or authentication responses are found, this snippet initiates the OAuth flow by calling `tool_context.request_credential()`. This action pauses the tool's execution and prompts the end-user to log in, returning a pending status to the client.
SOURCE: https://github.com/google/adk-docs/blob/main/docs/tools/authentication.md#_snippet_14

LANGUAGE: Python
CODE:
```
# Use auth_scheme and auth_credential configured in the tool.

  tool_context.request_credential(AuthConfig(
    auth_scheme=auth_scheme,
    raw_auth_credential=auth_credential,
  ))
  return {'pending': true, 'message': 'Awaiting user authentication.'}

# By setting request_credential, ADK detects a pending authentication event. It pauses execution and ask end user to login.
```

----------------------------------------

TITLE: Agent Project Directory Structure
DESCRIPTION: Illustrates the expected directory structure for an agent project, showing the parent folder and the agent's main file (Python or Java).
SOURCE: https://github.com/google/adk-docs/blob/main/docs/get-started/testing.md#_snippet_1

LANGUAGE: console
CODE:
```
parent_folder/
└── my_sample_agent/
    └── agent.py (or Agent.java)
```

----------------------------------------

TITLE: Create ScienceTeacherAgent Java Class
DESCRIPTION: Provides the Java code for the ScienceTeacherAgent class, which extends BaseAgent and uses LlmAgent.builder to define a science teacher agent with a specific model and instruction. It highlights the ROOT_AGENT field and initAgent method required for Dev UI dynamic loading.
SOURCE: https://github.com/google/adk-docs/blob/main/docs/get-started/streaming/quickstart-streaming-java.md#_snippet_2

LANGUAGE: java
CODE:
```
package samples.liveaudio;

import com.google.adk.agents.BaseAgent;
import com.google.adk.agents.LlmAgent;

/** Science teacher agent. */
public class ScienceTeacherAgent {

  // Field expected by the Dev UI to load the agent dynamically
  // (the agent must be initialized at declaration time)
  public static BaseAgent ROOT_AGENT = initAgent();

  public static BaseAgent initAgent() {
    return LlmAgent.builder()
        .name("science-app")
        .description("Science teacher agent")
        .model("gemini-2.0-flash-exp")
        .instruction("""
            You are a helpful science teacher that explains
            science concepts to kids and teenagers.
            """)
        .build();
  }
}
```

----------------------------------------

TITLE: Configure synchronous pre-model callback for LlmAgent.Builder
DESCRIPTION: Sets a synchronous callback to be executed before the LLM model is invoked. This allows for last-minute modifications or logging prior to content generation.
SOURCE: https://github.com/google/adk-docs/blob/main/docs/api-reference/java/com/google/adk/agents/class-use/LlmAgent.Builder.html#_snippet_1

LANGUAGE: APIDOC
CODE:
```
LlmAgent.Builder.beforeModelCallbackSync(com.google.adk.agents.Callbacks.BeforeModelCallbackSync beforeModelCallbackSync): LlmAgent.Builder
  Parameters:
    beforeModelCallbackSync (com.google.adk.agents.Callbacks.BeforeModelCallbackSync): The callback to be invoked synchronously before the model is called.
  Returns:
    LlmAgent.Builder: The current builder instance for chaining calls.
```

----------------------------------------

TITLE: ADK Runner Package: Methods Accepting Session as Parameter
DESCRIPTION: Outlines methods in the `com.google.adk.runner` package that accept a `Session` object as a parameter. The `runAsync` method, for instance, uses a provided `Session` to execute an agent in standard mode.
SOURCE: https://github.com/google/adk-docs/blob/main/docs/api-reference/java/com/google/adk/sessions/class-use/Session.html#_snippet_2

LANGUAGE: APIDOC
CODE:
```
com.google.adk.runner.Runner:
  runAsync(
    session: com.google.adk.sessions.Session,
    newMessage: com.google.genai.types.Content,
    runConfig: com.google.adk.agents.RunConfig
  ): io.reactivex.rxjava3.core.Flowable<com.google.adk.events.Event>
  Description: Runs the agent in the standard mode using a provided Session object.
```

----------------------------------------

TITLE: Manage associated agent (Java API)
DESCRIPTION: Allows setting or retrieving the `BaseAgent` associated with this `InvocationContext`.
SOURCE: https://github.com/google/adk-docs/blob/main/docs/api-reference/java/com/google/adk/agents/InvocationContext.html#_snippet_8

LANGUAGE: APIDOC
CODE:
```
public BaseAgent agent()
```

LANGUAGE: APIDOC
CODE:
```
public void agent(BaseAgent agent)
```

----------------------------------------

TITLE: Set Output Schema for LlmAgent.Builder
DESCRIPTION: Defines the expected output schema for the `LlmAgent`. This schema specifies the structure and types of data the agent will produce as output.
SOURCE: https://github.com/google/adk-docs/blob/main/docs/api-reference/java/com/google/adk/agents/LlmAgent.Builder.html#_snippet_23

LANGUAGE: APIDOC
CODE:
```
@CanIgnoreReturnValue public LlmAgent.Builder outputSchema(com.google.genai.types.Schema outputSchema)
```

----------------------------------------

TITLE: BaseFlow: Run Live with InvocationContext
DESCRIPTION: Executes a live flow, taking an `InvocationContext` to manage the execution environment and state.
SOURCE: https://github.com/google/adk-docs/blob/main/docs/api-reference/java/com/google/adk/agents/class-use/InvocationContext.html#_snippet_10

LANGUAGE: APIDOC
CODE:
```
BaseFlow.runLive(com.google.adk.agents.InvocationContext invocationContext)
```

----------------------------------------

TITLE: Get Before Model Callback (Java ADK API)
DESCRIPTION: Retrieves an optional callback that is executed before a model interaction. This allows for custom logic to be injected prior to model execution.
SOURCE: https://github.com/google/adk-docs/blob/main/docs/api-reference/java/com/google/adk/agents/LlmAgent.html#_snippet_17

LANGUAGE: APIDOC
CODE:
```
public Optional<Callbacks.BeforeModelCallback> beforeModelCallback()
```

----------------------------------------

TITLE: Configure Content Inclusion for LlmAgent
DESCRIPTION: Specifies how the LlmAgent should include content in its interactions, based on predefined inclusion settings.
SOURCE: https://github.com/google/adk-docs/blob/main/docs/api-reference/java/com/google/adk/agents/LlmAgent.Builder.html#_snippet_9

LANGUAGE: APIDOC
CODE:
```
LlmAgent.Builder includeContents(LlmAgent.IncludeContents includeContents)
  includeContents: LlmAgent.IncludeContents - The content inclusion setting for the LlmAgent.
```

----------------------------------------

TITLE: Java: LlmAgent.Builder.beforeAgentCallbackSync Method API Documentation
DESCRIPTION: API documentation for the `beforeAgentCallbackSync` method in the `LlmAgent.Builder` class. This method accepts an instance of `Callbacks.BeforeAgentCallbackSync` to configure agent behavior before execution, typically used for setting up callbacks.
SOURCE: https://github.com/google/adk-docs/blob/main/docs/api-reference/java/com/google/adk/agents/class-use/Callbacks.BeforeAgentCallbackSync.html#_snippet_0

LANGUAGE: APIDOC
CODE:
```
Class: com.google.adk.agents.LlmAgent.Builder
  Method: beforeAgentCallbackSync
    Signature: beforeAgentCallbackSync(com.google.adk.agents.Callbacks.BeforeAgentCallbackSync beforeAgentCallbackSync)
    Parameters:
      beforeAgentCallbackSync: An instance of the `com.google.adk.agents.Callbacks.BeforeAgentCallbackSync` interface.
    Returns: LlmAgent.Builder (for method chaining)
```

----------------------------------------

TITLE: Agent-related Constructors with InvocationContext
DESCRIPTION: Constructors for CallbackContext and ReadonlyContext classes, demonstrating how to initialize context-related objects using an InvocationContext.
SOURCE: https://github.com/google/adk-docs/blob/main/docs/api-reference/java/com/google/adk/agents/class-use/InvocationContext.html#_snippet_8

LANGUAGE: APIDOC
CODE:
```
CallbackContext(com.google.adk.agents.InvocationContext invocationContext, com.google.adk.events.EventActions eventActions)
```

LANGUAGE: APIDOC
CODE:
```
ReadonlyContext(com.google.adk.agents.InvocationContext invocationContext)
```

----------------------------------------

TITLE: Creating Python `agent.py` File
DESCRIPTION: This command creates an empty `agent.py` file within the `multi_tool_agent` directory. This file will contain the core logic and implementation of the multi-tool agent.
SOURCE: https://github.com/google/adk-docs/blob/main/docs/get-started/quickstart.md#_snippet_5

LANGUAGE: shell
CODE:
```
touch multi_tool_agent/agent.py
```

----------------------------------------

TITLE: Launching ADK API Server (Python)
DESCRIPTION: This shell command starts a local FastAPI server for the ADK agent, facilitating testing with cURL requests before deployment. Further details on using `adk api_server` for testing are available in the ADK documentation.
SOURCE: https://github.com/google/adk-docs/blob/main/docs/get-started/quickstart.md#_snippet_16

LANGUAGE: shell
CODE:
```
adk api_server
```

----------------------------------------

TITLE: Prepare Agent Team Interaction Environment
DESCRIPTION: This Python snippet sets up the necessary environment for interacting with the previously defined agent team. It ensures 'asyncio' is imported and includes a crucial check for the existence of the root agent variable ('root_agent' or 'weather_agent_team') before proceeding with the conversation setup. This preparation is essential for defining the 'run_team_conversation' function and testing the delegation flow.
SOURCE: https://github.com/google/adk-docs/blob/main/docs/tutorials/agent-team.md#_snippet_20

LANGUAGE: python
CODE:
```
# @title Interact with the Agent Team
import asyncio # Ensure asyncio is imported

# Ensure the root agent (e.g., 'weather_agent_team' or 'root_agent' from the previous cell) is defined.
# Ensure the call_agent_async function is defined.

# Check if the root agent variable exists before defining the conversation function
root_agent_var_name = 'root_agent' # Default name from Step 3 guide
if 'weather_agent_team' in globals(): # Check if user used this name instead
    root_agent_var_name = 'weather_agent_team'
elif 'root_agent' not in globals():
    print("⚠️ Root agent ('root_agent' or 'weather_agent_team') not found. Cannot define run_team_conversation.")
    # Assign a dummy value to prevent NameError later if the code block runs anyway
    root_agent = None # Or set a flag to prevent execution

```

----------------------------------------

TITLE: Methods Inherited from java.lang.Object
DESCRIPTION: Lists methods inherited by LlmResponse.Builder from the java.lang.Object class, providing fundamental functionalities like object comparison, hashing, and thread synchronization.
SOURCE: https://github.com/google/adk-docs/blob/main/docs/api-reference/java/com/google/adk/models/LlmResponse.Builder.html#_snippet_8

LANGUAGE: APIDOC
CODE:
```
clone()
equals(java.lang.Object obj)
finalize()
getClass()
hashCode()
notify()
notifyAll()
toString()
wait()
wait(long timeout)
wait(long timeout, int nanos)
```

----------------------------------------

TITLE: LLM Content Generation API (BaseLlm, Claude, Gemini)
DESCRIPTION: Documents the `generateContent` method across `BaseLlm`, `Claude`, and `Gemini` classes. This method is used for generating content from LLM requests and supports an optional streaming mode, returning a Flowable for asynchronous content delivery.
SOURCE: https://github.com/google/adk-docs/blob/main/docs/api-reference/java/com/google/adk/models/class-use/LlmRequest.html#_snippet_9

LANGUAGE: APIDOC
CODE:
```
Class: BaseLlm
  Method: generateContent(LlmRequest llmRequest, boolean stream)
    Description: Generates one content from the given LLM request and tools.
    Parameters:
      llmRequest: LlmRequest - The LLM request object.
      stream: boolean - Whether to stream the content generation.
    Returns: io.reactivex.rxjava3.core.Flowable<LlmResponse>
```

LANGUAGE: APIDOC
CODE:
```
Class: Claude
  Method: generateContent(LlmRequest llmRequest, boolean stream)
    Parameters:
      llmRequest: LlmRequest - The LLM request object.
      stream: boolean - Whether to stream the content generation.
    Returns: io.reactivex.rxjava3.core.Flowable<LlmResponse>
```

LANGUAGE: APIDOC
CODE:
```
Class: Gemini
  Method: generateContent(LlmRequest llmRequest, boolean stream)
    Parameters:
      llmRequest: LlmRequest - The LLM request object.
      stream: boolean - Whether to stream the content generation.
    Returns: io.reactivex.rxjava3.core.Flowable<LlmResponse>
```

----------------------------------------

TITLE: Extract LiveRequest Connection Close Boolean
DESCRIPTION: Extracts the boolean value from the `close` field. If the `close` field is unset, this method returns `false`.
SOURCE: https://github.com/google/adk-docs/blob/main/docs/api-reference/java/com/google/adk/agents/LiveRequest.html#_snippet_4

LANGUAGE: APIDOC
CODE:
```
Method: shouldClose
Signature: public boolean shouldClose()
Returns: boolean - True if the connection should be closed, false otherwise.
```

----------------------------------------

TITLE: Classes from com.google.adk.events Used by com.google.adk
DESCRIPTION: Details which classes from `com.google.adk.events` are utilized by the `com.google.adk` package.
SOURCE: https://github.com/google/adk-docs/blob/main/docs/api-reference/java/com/google/adk/events/package-use.html#_snippet_1

LANGUAGE: APIDOC
CODE:
```
Classes in com.google.adk.events used by com.google.adk:
- Class: Event
  Description: Represents an event in a session.
```

----------------------------------------

TITLE: LlmAgent.builder() Method
DESCRIPTION: Returns a static builder instance for constructing LlmAgent objects. This method provides a convenient way to create new LlmAgent instances using a fluent API.
SOURCE: https://github.com/google/adk-docs/blob/main/docs/api-reference/java/com/google/adk/agents/LlmAgent.html#_snippet_4

LANGUAGE: APIDOC
CODE:
```
public static LlmAgent.Builder builder()
Returns a LlmAgent.Builder for LlmAgent.
```

----------------------------------------

TITLE: Set Close Flag for LiveRequest.Builder
DESCRIPTION: Sets the close flag for the `LiveRequest.Builder`. This method is overloaded to accept either a nullable `java.lang.Boolean` or an `Optional` `java.lang.Boolean`. Both return the builder instance for chaining.
SOURCE: https://github.com/google/adk-docs/blob/main/docs/api-reference/java/com/google/adk/agents/LiveRequest.Builder.html#_snippet_4

LANGUAGE: APIDOC
CODE:
```
public abstract LiveRequest.Builder close(@Nullable Boolean close)
```

LANGUAGE: APIDOC
CODE:
```
public abstract LiveRequest.Builder close(Optional<Boolean> close)
```

----------------------------------------

TITLE: ReadonlyContext Inherited Methods
DESCRIPTION: Methods inherited from the `com.google.adk.agents.ReadonlyContext` class, providing read-only access to agent-specific information.
SOURCE: https://github.com/google/adk-docs/blob/main/docs/api-reference/java/com/google/adk/tools/ToolContext.html#_snippet_2

LANGUAGE: APIDOC
CODE:
```
ReadonlyContext:
  agentName()
  invocationId()
```

----------------------------------------

TITLE: LlmAgent.Builder Class Methods
DESCRIPTION: Defines the various methods available on the `LlmAgent.Builder` class for configuring an `LlmAgent` instance. These methods allow setting properties such as example providers, executors, content generation configurations, instructions, models, schemas, and sub-agents.
SOURCE: https://github.com/google/adk-docs/blob/main/docs/api-reference/java/com/google/adk/agents/LlmAgent.Builder.html#_snippet_2

LANGUAGE: APIDOC
CODE:
```
class LlmAgent.Builder {
  exampleProvider(com.google.adk.examples.BaseExampleProvider exampleProvider);
  exampleProvider(com.google.adk.examples.Example... examples);
  exampleProvider(java.util.List<com.google.adk.examples.Example> examples);
  executor(java.util.concurrent.Executor executor);
  generateContentConfig(com.google.genai.types.GenerateContentConfig generateContentConfig);
  globalInstruction(java.lang.String globalInstruction);
  includeContents(com.google.adk.agents.LlmAgent.IncludeContents includeContents);
  inputSchema(com.google.genai.types.Schema inputSchema);
  instruction(java.lang.String instruction);
  model(com.google.adk.models.BaseLlm model);
  model(java.lang.String model);
  name(java.lang.String name);
  outputKey(java.lang.String outputKey);
  outputSchema(com.google.genai.types.Schema outputSchema);
  planning(boolean planning);
  subAgents(com.google.adk.agents.BaseAgent... subAgents);
  subAgents(java.util.List<? extends com.google.adk.agents.BaseAgent> subAgents);
  tools(com.google.adk.tools.BaseTool... tools);
}
```

----------------------------------------

TITLE: Build Docker Image for Python ADK Agent
DESCRIPTION: This Dockerfile provides instructions to build a container image for a Python-based Google ADK agent. It sets up the Python environment, installs dependencies, creates a non-root user, copies application code, and defines the entrypoint for `uvicorn`.
SOURCE: https://github.com/google/adk-docs/blob/main/docs/deploy/cloud-run.md#_snippet_9

LANGUAGE: dockerfile
CODE:
```
FROM python:3.13-slim
WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

RUN adduser --disabled-password --gecos "" myuser && \
    chown -R myuser:myuser /app

COPY . .

USER myuser

ENV PATH="/home/myuser/.local/bin:$PATH"

CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port $PORT"]
```

----------------------------------------

TITLE: APIDOC: LlmAgent.Builder Class
DESCRIPTION: Builder for LlmAgent.
SOURCE: https://github.com/google/adk-docs/blob/main/docs/api-reference/java/allclasses-index.html#_snippet_18

LANGUAGE: APIDOC
CODE:
```
class com.google.adk.agents.LlmAgent.Builder
```

----------------------------------------

TITLE: APIDOC: LoopAgent
DESCRIPTION: An agent implementation that executes its sub-agents sequentially in a continuous loop, useful for iterative processes or recurring tasks.
SOURCE: https://github.com/google/adk-docs/blob/main/docs/api-reference/java/allclasses-index.html#_snippet_29

LANGUAGE: APIDOC
CODE:
```
LoopAgent (class)
  Description: An agent that runs its sub-agents sequentially in a loop.
```

----------------------------------------

TITLE: Run Agent Asynchronously with Full Configuration
DESCRIPTION: Runs the agent in standard mode for a given user and session, processing a new message with explicit run configuration.
SOURCE: https://github.com/google/adk-docs/blob/main/docs/api-reference/java/com/google/adk/runner/Runner.html#_snippet_13

LANGUAGE: APIDOC
CODE:
```
public io.reactivex.rxjava3.core.Flowable<Event> runAsync(String userId, String sessionId, com.google.genai.types.Content newMessage, RunConfig runConfig)
Parameters:
  userId: The ID of the user for the session.
  sessionId: The ID of the session to run the agent in.
  newMessage: The new message from the user to process.
  runConfig: Configuration for the agent run.
Returns:
  A Flowable stream of Event objects generated by the agent during execution.
```

----------------------------------------

TITLE: Installing Project Dependencies - Shell
DESCRIPTION: This command uses `pip` to install all Python packages listed in the `requirements.txt` file. This ensures that all necessary project dependencies are installed within the activated virtual environment.
SOURCE: https://github.com/google/adk-docs/blob/main/CONTRIBUTING.md#_snippet_2

LANGUAGE: shell
CODE:
```
pip install -r requirements.txt
```

----------------------------------------

TITLE: Capture and Send Microphone Audio in Java
DESCRIPTION: This method captures audio from the microphone, checks for line support, initializes the microphone, and continuously reads audio data. The captured audio chunks are then converted into Blob objects and sent to a LiveRequestQueue for processing, typically for real-time streaming to a service. It includes error handling for microphone access.
SOURCE: https://github.com/google/adk-docs/blob/main/docs/get-started/streaming/quickstart-streaming-java.md#_snippet_8

LANGUAGE: Java
CODE:
```
  private void captureAndSendMicrophoneAudio(
      LiveRequestQueue liveRequestQueue, AtomicBoolean isRunning) {
    TargetDataLine micLine = null;
    try {
      DataLine.Info info = new DataLine.Info(TargetDataLine.class, MIC_AUDIO_FORMAT);
      if (!AudioSystem.isLineSupported(info)) {
        System.err.println("Microphone line not supported!");
        return;
      }

      micLine = (TargetDataLine) AudioSystem.getLine(info);
      micLine.open(MIC_AUDIO_FORMAT);
      micLine.start();

      System.out.println("Microphone initialized. Start speaking...");

      byte[] buffer = new byte[BUFFER_SIZE];
      int bytesRead;

      while (isRunning.get()) {
        bytesRead = micLine.read(buffer, 0, buffer.length);

        if (bytesRead > 0) {
          byte[] audioChunk = new byte[bytesRead];
          System.arraycopy(buffer, 0, audioChunk, 0, bytesRead);

          Blob audioBlob = Blob.builder().data(audioChunk).mimeType("audio/pcm").build();

          liveRequestQueue.realtime(audioBlob);
        }
      }
    } catch (LineUnavailableException e) {
      System.err.println("Error accessing microphone: " + e.getMessage());
      e.printStackTrace();
    } finally {
      if (micLine != null) {
        micLine.stop();
        micLine.close();
      }
    }
  }
```

----------------------------------------

TITLE: Create FunctionTool Instance
DESCRIPTION: Static factory methods to create `FunctionTool` instances. These overloaded methods allow creating a tool either directly from a `java.lang.reflect.Method` object or by providing a `java.lang.Class` and the method name as a `java.lang.String`.
SOURCE: https://github.com/google/adk-docs/blob/main/docs/api-reference/java/com/google/adk/tools/FunctionTool.html#_snippet_2

LANGUAGE: APIDOC
CODE:
```
public static com.google.adk.tools.FunctionTool create(java.lang.reflect.Method func)
```

LANGUAGE: APIDOC
CODE:
```
public static com.google.adk.tools.FunctionTool create(java.lang.Class<?> cls, java.lang.String methodName)
```

----------------------------------------

TITLE: Session.Builder Constructor
DESCRIPTION: Details the constructor for the `Session.Builder` class, which is used to initialize a new builder instance with a specified session ID.
SOURCE: https://github.com/google/adk-docs/blob/main/docs/api-reference/java/com/google/adk/sessions/Session.Builder.html#_snippet_2

LANGUAGE: APIDOC
CODE:
```
Class: com.google.adk.sessions.Session.Builder
  Constructor:
    public Builder(String id)
```

----------------------------------------

TITLE: Java Map Return for Service Responses
DESCRIPTION: Illustrates returning a `Map` in Java, typically used for service responses, including handling `IllegalArgumentException` to return an error map. This snippet demonstrates a common pattern for structured responses.
SOURCE: https://github.com/google/adk-docs/blob/main/docs/context/index.md#_snippet_18

LANGUAGE: Java
CODE:
```
                return Map.of("availableDocs", "artifactKeys");
            } catch(IllegalArgumentException e){
                return Map.of("error", "Artifact service error: " + e);
            }
        }
```

----------------------------------------

TITLE: Set Generate Content Response for LlmResponse Builder
DESCRIPTION: Sets the main content response generated by the LLM for the LlmResponse.Builder. This method is crucial for populating the core LLM output into the builder.
SOURCE: https://github.com/google/adk-docs/blob/main/docs/api-reference/java/com/google/adk/models/LlmResponse.Builder.html#_snippet_15

LANGUAGE: APIDOC
CODE:
```
@CanIgnoreReturnValue public final LlmResponse.Builder response(com.google.genai.types.GenerateContentResponse response)
```

----------------------------------------

TITLE: Run ADK Web UI to Interact with Agent
DESCRIPTION: This shell command navigates to the agent's parent directory and launches the ADK Web UI. This allows users to interact with the defined `LlmAgent` through a web interface. A note for Windows users suggests using `adk web --no-reload` to avoid a `_make_subprocess_transport NotImplementedError`.
SOURCE: https://github.com/google/adk-docs/blob/main/docs/tools/mcp-tools.md#_snippet_4

LANGUAGE: shell
CODE:
```
cd ./adk_agent_samples # Or your equivalent parent directory
adk web
```

----------------------------------------

TITLE: Configure asynchronous pre-tool callback for LlmAgent.Builder
DESCRIPTION: Sets an asynchronous callback to be executed before a tool is invoked by the LLM. This allows for custom logic or validation before tool execution.
SOURCE: https://github.com/google/adk-docs/blob/main/docs/api-reference/java/com/google/adk/agents/class-use/LlmAgent.Builder.html#_snippet_2

LANGUAGE: APIDOC
CODE:
```
LlmAgent.Builder.beforeToolCallback(com.google.adk.agents.Callbacks.BeforeToolCallback beforeToolCallback): LlmAgent.Builder
  Parameters:
    beforeToolCallback (com.google.adk.agents.Callbacks.BeforeToolCallback): The callback to be invoked asynchronously before a tool is called.
  Returns:
    LlmAgent.Builder: The current builder instance for chaining calls.
```

----------------------------------------

TITLE: Java Map Interface: containsKey
DESCRIPTION: Documents the `containsKey` method of the Java `Map` interface, detailing its signature and inheritance. This method checks if the map contains a mapping for the specified key.
SOURCE: https://github.com/google/adk-docs/blob/main/docs/api-reference/java/com/google/adk/sessions/State.html#_snippet_9

LANGUAGE: APIDOC
CODE:
```
boolean containsKey(Object key)
Specified by:
  containsKey in interface Map<String,Object>
```

----------------------------------------

TITLE: Java Object Inherited Methods API Reference
DESCRIPTION: Lists common methods inherited from `java.lang.Object` in Java, providing a quick reference to their names and basic signatures as part of the ADK API context.
SOURCE: https://github.com/google/adk-docs/blob/main/docs/api-reference/java/com/google/adk/agents/Callbacks.html#_snippet_1

LANGUAGE: APIDOC
CODE:
```
java.lang.Object Inherited Methods:
- clone()
- equals(java.lang.Object)
- finalize()
- getClass()
- hashCode()
- notify()
- notifyAll()
- toString()
- wait()
- wait(long)
- wait(long, int)
```

----------------------------------------

TITLE: Setting PYTHONUTF8 Environment Variable (PowerShell)
DESCRIPTION: Sets the `PYTHONUTF8` environment variable to `1` in PowerShell to prevent `UnicodeDecodeError` when using LiteLLM on Windows. This forces Python to use UTF-8 globally for file operations, including cached model pricing information.
SOURCE: https://github.com/google/adk-docs/blob/main/docs/agents/models.md#_snippet_11

LANGUAGE: powershell
CODE:
```
# Set for current session
$env:PYTHONUTF8 = "1"
# Set persistently for the user
[System.Environment]::SetEnvironmentVariable('PYTHONUTF8', '1', [System.EnvironmentVariableTarget]::User)
```

----------------------------------------

TITLE: EventActions.Builder Class and Constructor API Documentation
DESCRIPTION: Documents the EventActions.Builder class, which is part of com.google.adk.events, and its default public constructor.
SOURCE: https://github.com/google/adk-docs/blob/main/docs/api-reference/java/com/google/adk/events/EventActions.Builder.html#_snippet_1

LANGUAGE: APIDOC
CODE:
```
class com.google.adk.events.EventActions.Builder
  Constructor:
    public Builder()
```

----------------------------------------

TITLE: EventActions.Builder.transferToAgent Method
DESCRIPTION: Documents the `transferToAgent` method within the `EventActions.Builder` class. This method is used to transfer an event action to a specific agent, identified by their ID.
SOURCE: https://github.com/google/adk-docs/blob/main/docs/api-reference/java/com/google/adk/events/class-use/EventActions.Builder.html#_snippet_1

LANGUAGE: APIDOC
CODE:
```
EventActions.Builder.transferToAgent(java.lang.String agentId)
  Parameters:
    agentId: java.lang.String - The ID of the agent to transfer the event action to.
```

----------------------------------------

TITLE: Function Tools Overview in ADK
DESCRIPTION: Describes custom tools tailored to specific application needs within ADK, including regular Python/Java functions and long-running operations. It also covers the concept of using other agents as tools.
SOURCE: https://github.com/google/adk-docs/blob/main/llms.txt#_snippet_2

LANGUAGE: APIDOC
CODE:
```
Function Tools:
  Function Tool:
    Description: Regular Python functions or Java methods for specific actions.
    Parameters: JSON-serializable types, avoid default values.
    Return Type: Dictionary (Python), Map (Java) for LLM context.
    LLM Description: Docstrings or source code comments.
  Long Running Function Tool:
    Description: Subclass of FunctionTool for time-consuming tasks without blocking agent.
    Behavior: Initiates operation, optionally returns initial result, allows agent pause, client queries progress.
  Agent-as-a-Tool:
    Class: AgentTool
    Description: Leverages other agents by calling them as tools.
    Behavior: Returns answer to calling agent, which summarizes and responds, retaining control.
```

----------------------------------------

TITLE: Configure disallow transfer to parent for LlmAgent.Builder
DESCRIPTION: Configures whether the `LlmAgent` is allowed to transfer control to its parent agent. Setting this to `true` prevents such transfers.
SOURCE: https://github.com/google/adk-docs/blob/main/docs/api-reference/java/com/google/adk/agents/class-use/LlmAgent.Builder.html#_snippet_6

LANGUAGE: APIDOC
CODE:
```
LlmAgent.Builder.disallowTransferToParent(boolean disallowTransferToParent): LlmAgent.Builder
  Parameters:
    disallowTransferToParent (boolean): If true, prevents the agent from transferring control to its parent.
  Returns:
    LlmAgent.Builder: The current builder instance for chaining calls.
```

----------------------------------------

TITLE: Constructors Using McpToolset in com.google.adk.tools.mcp
DESCRIPTION: Documents constructors within the `com.google.adk.tools.mcp` package that accept `McpToolset` as a parameter.
SOURCE: https://github.com/google/adk-docs/blob/main/docs/api-reference/java/com/google/adk/tools/mcp/class-use/McpToolset.html#_snippet_1

LANGUAGE: APIDOC
CODE:
```
Package: com.google.adk.tools.mcp

Constructors with McpToolset parameter:
- McpToolsAndToolsetResult(List<McpTool> tools, McpToolset toolset)
```

----------------------------------------

TITLE: Define Project Structure for ADK Agent
DESCRIPTION: This snippet illustrates the recommended file and folder structure for an ADK agent project. It includes a root folder, an environment file (.env), and a dedicated agent directory containing Python initialization, agent logic, and tools files, ensuring proper organization for development and deployment.
SOURCE: https://github.com/google/adk-docs/blob/main/docs/tools/google-cloud-tools.md#_snippet_7

LANGUAGE: console
CODE:
```
project_root_folder
|-- .env
`-- my_agent
    |-- __init__.py
    |-- agent.py
    `__ tools.py
```

----------------------------------------

TITLE: com.google.adk Package API Overview
DESCRIPTION: Comprehensive API documentation for the `com.google.adk` package, detailing its related sub-packages and core classes with their descriptions.
SOURCE: https://github.com/google/adk-docs/blob/main/docs/api-reference/java/com/google/adk/package-summary.html#_snippet_1

LANGUAGE: APIDOC
CODE:
```
Package: com.google.adk

Related Packages:
  com.google.adk.agents
  com.google.adk.artifacts
  com.google.adk.events
  com.google.adk.examples
  com.google.adk.exceptions
  com.google.adk.flows
  com.google.adk.models
  com.google.adk.network
  com.google.adk.runner
  com.google.adk.sessions
  com.google.adk.tools
  com.google.adk.utils

Classes:
  CollectionUtils:
    Description: Frequently used code snippets for collections.
  JsonBaseModel:
    Description: The base class for the types that needs JSON serialization/deserialization capability.
  SchemaUtils:
    Description: Utility class for validating schemas.
  Telemetry:
    Description: Utility class for capturing and reporting telemetry data within the ADK.
  Version:
    Description: Holding class for the version of the Java ADK.
```

----------------------------------------

TITLE: LoopAgent.Builder Configuration Methods
DESCRIPTION: Documents the methods available in the `LoopAgent.Builder` class for configuring various properties of a `LoopAgent`, including its name, description, sub-agents, maximum iterations, and callback functions, culminating in the `build` method to create the `LoopAgent` instance.
SOURCE: https://github.com/google/adk-docs/blob/main/docs/api-reference/java/com/google/adk/agents/LoopAgent.Builder.html#_snippet_3

LANGUAGE: APIDOC
CODE:
```
LoopAgent.Builder:
  name(String name): LoopAgent.Builder
    @CanIgnoreReturnValue
  description(String description): LoopAgent.Builder
    @CanIgnoreReturnValue
  subAgents(List<? extends BaseAgent> subAgents): LoopAgent.Builder
    @CanIgnoreReturnValue
  subAgents(BaseAgent... subAgents): LoopAgent.Builder
    @CanIgnoreReturnValue
  maxIterations(int maxIterations): LoopAgent.Builder
    @CanIgnoreReturnValue
  maxIterations(Optional<Integer> maxIterations): LoopAgent.Builder
    @CanIgnoreReturnValue
  beforeAgentCallback(Callbacks.BeforeAgentCallback beforeAgentCallback): LoopAgent.Builder
    @CanIgnoreReturnValue
  afterAgentCallback(Callbacks.AfterAgentCallback afterAgentCallback): LoopAgent.Builder
    @CanIgnoreReturnValue
  build(): LoopAgent
```

----------------------------------------

TITLE: Build LlmRequest Object
DESCRIPTION: Details the `build` method of `LlmRequest.Builder`, which is used to construct an immutable `LlmRequest` instance. This method is part of the builder design pattern for creating complex objects.
SOURCE: https://github.com/google/adk-docs/blob/main/docs/api-reference/java/com/google/adk/models/class-use/LlmRequest.html#_snippet_6

LANGUAGE: APIDOC
CODE:
```
Method: LlmRequest.Builder.build()
  Return Type: abstract com.google.adk.models.LlmRequest
```

----------------------------------------

TITLE: Example of Agent Trajectory Step Comparison
DESCRIPTION: This Python snippet illustrates the concept of comparing an agent's actual sequence of actions (trajectory) against a predefined set of expected steps. This comparison is fundamental for evaluating the agent's decision-making process and adherence to an ideal path, revealing potential errors or inefficiencies.
SOURCE: https://github.com/google/adk-docs/blob/main/docs/evaluate/index.md#_snippet_0

LANGUAGE: Python
CODE:
```
# Trajectory evaluation will compare
expected_steps = ["determine_intent", "use_tool", "review_results", "report_generation"]
actual_steps = ["determine_intent", "use_tool", "review_results", "report_generation"]
```

----------------------------------------

TITLE: Retrieve Google Cloud Project Number (Alternative)
DESCRIPTION: An alternative method to get your Google Cloud project number if `jq` is not installed. You will need to manually copy the project number from the command output.
SOURCE: https://github.com/google/adk-docs/blob/main/docs/deploy/gke.md#_snippet_1

LANGUAGE: bash
CODE:
```
gcloud projects describe $GOOGLE_CLOUD_PROJECT
```

----------------------------------------

TITLE: Reference to Full CrewAI Serper Search Example
DESCRIPTION: This entry points to a complete Python code example file that demonstrates the end-to-end integration and usage of the CrewAI Serper API search tool within an ADK agent.
SOURCE: https://github.com/google/adk-docs/blob/main/docs/tools/third-party-tools.md#_snippet_11

LANGUAGE: python
CODE:
```
--8<-- "examples/python/snippets/tools/third-party/crewai_serper_search.py"
```

----------------------------------------

TITLE: Session Class API Documentation
DESCRIPTION: Detailed API specification for the `com.google.adk.sessions.Session` class, including its inheritance, nested classes, and a summary of all public methods with their signatures and return types.
SOURCE: https://github.com/google/adk-docs/blob/main/docs/api-reference/java/com/google/adk/sessions/Session.html#_snippet_0

LANGUAGE: APIDOC
CODE:
```
Class: com.google.adk.sessions.Session
Extends: com.google.adk.JsonBaseModel
Description: A Session object that encapsulates the State and Events of a session.

Nested Classes:
  static final class Session.Builder
    Description: Builder for Session.

Method Summary:
  String appName()
  static Session.Builder builder(String id)
  List<Event> events()
  static Session fromJson(String json)
  double getLastUpdateTimeAsDouble()
  String id()
  Instant lastUpdateTime()
  void lastUpdateTime(Instant lastUpdateTime)
  ConcurrentMap<String, Object> state()
  String userId()

Methods inherited from class com.google.adk.JsonBaseModel:
  (Details not provided in source text)
```