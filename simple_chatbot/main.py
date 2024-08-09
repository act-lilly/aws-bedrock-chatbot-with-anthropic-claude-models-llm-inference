# file: main.py
import streamlit as st
import boto3
from botocore.exceptions import ClientError
import logging
import textwrap

# Define custom log level
ALWAYS_LOG = 35  # Between WARNING (30) and ERROR (40)
logging.addLevelName(ALWAYS_LOG, "ALWAYS_LOG")

class CustomLogger(logging.Logger):
    def __init__(self, name, level=logging.NOTSET):
        super().__init__(name, level)

    def always_log(self, msg, *args, **kwargs):
        if self.isEnabledFor(ALWAYS_LOG):
            self._log(ALWAYS_LOG, msg, args, **kwargs)

def setup_logger():
    logger = CustomLogger(__name__)
    logger.setLevel(logging.INFO)

    # Remove any existing handlers
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)

    # Create a new handler
    handler = logging.StreamHandler()
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)

    logger.addHandler(handler)

    return logger

logger = setup_logger()

bedrock = boto3.client(
    service_name='bedrock-runtime',
    region_name='us-east-1'
)

# Hide sidebar when printing page
hide_sidebar_css = """
<style>
    @media print {
        [data-testid="stSidebar"] {
            display: none;
        }
    }
</style>
"""

st.set_page_config(page_title="Neo", layout="wide")
# Inject the CSS with st.markdown
st.markdown(hide_sidebar_css, unsafe_allow_html=True)
st.title("neo")
st.caption("a chatbot for claude models on aws bedrock")

if "session_started" not in st.session_state:
    logger.always_log("Starting new session")
    st.session_state.session_started = True

# System prompt options
SYSTEM_PROMPTS = {
    "Default Assistant": "You are Claude, an AI assistant created by Anthropic to be helpful, harmless, and honest.",
    "Coding Assistant": "You are a coding assistant, expert in multiple programming languages. Provide clear, concise, and efficient code solutions.",
    "Creative Writer": "You are a creative writing assistant, skilled in various genres and styles. Help users craft engaging stories and narratives.",
    "Custom": ""
}

MODEL_OPTIONS = {
    "Claude 3.5 Sonnet": "anthropic.claude-3-5-sonnet-20240620-v1:0",
    "Claude 3 Haiku":    "anthropic.claude-3-haiku-20240307-v1:0",    
    "Claude 3 Sonnet":   "anthropic.claude-3-sonnet-20240229-v1:0",
    "Claude 2.1":        "anthropic.claude-v2:1",
    "Claude 2.0":        "anthropic.claude-v2",
    "Claude Instant":    "anthropic.claude-instant-v1"
}

# Initialize session state variables
if "system_prompt" not in st.session_state:
    st.session_state.system_prompt = SYSTEM_PROMPTS["Default Assistant"]
    logger.always_log(f"Initial system prompt: {st.session_state.system_prompt}")

if "last_custom_prompt" not in st.session_state:
    st.session_state.last_custom_prompt = ""

if "selected_model" not in st.session_state:
    st.session_state.selected_model = "Claude 3.5 Sonnet"
    logger.always_log(f"Initial model selected: {st.session_state.selected_model}")

if "temperature" not in st.session_state:
    st.session_state.temperature = 0.5
    logger.always_log(f"Initial temperature: {st.session_state.temperature}")

if "top_k" not in st.session_state:
    st.session_state.top_k = 100
    logger.always_log(f"Initial top_k: {st.session_state.top_k}")

# Callback functions for settings changes
def update_selected_model():
    new_model = st.session_state.model_selectbox
    if new_model != st.session_state.selected_model:
        logger.always_log(f"Model changed from {st.session_state.selected_model} to {new_model}")
        st.session_state.selected_model = new_model

def update_system_prompt():
    new_prompt = st.session_state.system_prompt_input
    if new_prompt != st.session_state.system_prompt:
        logger.always_log(f"System prompt changed from '{st.session_state.system_prompt}' to '{new_prompt}'")
        st.session_state.system_prompt = new_prompt
        if st.session_state.prompt_selection == "Custom":
            st.session_state.last_custom_prompt = new_prompt

def update_prompt_selection():
    selected_prompt = st.session_state.prompt_selection
    if selected_prompt == "Custom":
        st.session_state.system_prompt = st.session_state.last_custom_prompt
    else:
        st.session_state.system_prompt = SYSTEM_PROMPTS[selected_prompt]
    logger.always_log(f"System prompt selection changed to: {selected_prompt}")

def update_temperature():
    new_temp = st.session_state.temperature_slider
    if new_temp != st.session_state.temperature:
        logger.always_log(f"Temperature changed from {st.session_state.temperature} to {new_temp}")
        st.session_state.temperature = new_temp

def update_top_k():
    new_top_k = st.session_state.top_k_slider
    if new_top_k != st.session_state.top_k:
        logger.always_log(f"Top K changed from {st.session_state.top_k} to {new_top_k}")
        st.session_state.top_k = new_top_k

def clear_chat_history():
    st.session_state.messages = []
    logger.always_log("Chat history cleared")

# Sidebar for settings
with st.sidebar:
    if st.button("Clear Chat History", key="refresh_chat"):
        clear_chat_history()

    st.header("Settings")
    use_streaming = st.checkbox("Use streaming responses", value=True)

    st.subheader("Model Selection")
    st.selectbox(
        "Select Model",
        list(MODEL_OPTIONS.keys()),
        index=list(MODEL_OPTIONS.keys()).index(st.session_state.selected_model),
        key="model_selectbox",
        on_change=update_selected_model
    )

    st.subheader("Model Parameters")
    st.slider(
        "Temperature",
        min_value=0.0,
        max_value=1.0,
        value=st.session_state.temperature,
        step=0.01,
        key="temperature_slider",
        on_change=update_temperature
    )
    st.slider(
        "Top K",
        min_value=0,
        max_value=500,
        value=st.session_state.top_k,
        step=10,
        key="top_k_slider",
        on_change=update_top_k
    )

    st.subheader("System Prompt")
    selected_prompt_name = st.selectbox(
        "Select System Prompt",
        list(SYSTEM_PROMPTS.keys()),
        key="prompt_selection",
        on_change=update_prompt_selection
    )

    if selected_prompt_name == "Custom":
        st.text_area(
            "Custom System Prompt",
            value=st.session_state.system_prompt,
            height=100,
            key="system_prompt_input",
            on_change=update_system_prompt
        )
    else:
        st.text_area(
            "System Prompt",
            value=st.session_state.system_prompt,
            height=100,
            disabled=True,
            key="system_prompt_input"
        )

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display chat messages from history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"][0]["text"])

# Function to generate response from Claude using Converse API (non-streaming)
def generate_claude_response(messages):
    try:
        # Ensure messages alternate between user and assistant
        formatted_messages = []
        for i, msg in enumerate(messages):
            if i == 0 or msg["role"] != formatted_messages[-1]["role"]:
                formatted_messages.append(msg)

        logger.debug(f"Sending request with messages: {formatted_messages}")
        response = bedrock.converse(
            modelId=MODEL_OPTIONS[st.session_state.selected_model],
            messages=formatted_messages,
            system=[{"text": st.session_state.system_prompt}],
            inferenceConfig={"temperature": st.session_state.temperature},
            additionalModelRequestFields={"top_k": st.session_state.top_k}
        )
        logger.debug(f"Received response: {response}")

        # Extract the response content
        if 'output' in response and 'message' in response['output']:
            message = response['output']['message']
            if 'content' in message and len(message['content']) > 0:
                return message['content'][0]['text']

        st.error("Unexpected response structure from the model.")
        logger.error(f"Unexpected response structure: {response}")
        return None

    except ClientError as e:
        st.error(f"An error occurred: {e}")
        logger.error(f"ClientError: {e}")
        return None

# Function to generate streaming response from Claude
def generate_claude_streaming_response(messages):
    try:
        response = bedrock.converse_stream(
            modelId=MODEL_OPTIONS[st.session_state.selected_model],
            messages=messages,
            system=[{"text": st.session_state.system_prompt}],
            inferenceConfig={"temperature": st.session_state.temperature},
            additionalModelRequestFields={"top_k": st.session_state.top_k}
        )

        for event in response.get('stream'):
            if 'contentBlockDelta' in event:
                yield event['contentBlockDelta']['delta']['text']
    except ClientError as e:
        st.error(f"An error occurred: {e}")
        logger.error(f"ClientError in streaming: {e}")
        yield None

# Accept user input
if prompt := st.chat_input("How may I assist?"):
    logger.info(f"Received user input: {prompt}")

    st.session_state.messages.append({"role": "user", "content": [{"text": prompt}]})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Prepare messages for Claude
    claude_messages = [{"role": msg["role"], "content": msg["content"]} for msg in st.session_state.messages]

    # Generate Claude's response
    with st.chat_message("assistant"):
        if use_streaming:
            logger.always_log("Generating streaming response")
            response_container = st.empty()
            full_response = ""
            for response_chunk in generate_claude_streaming_response(claude_messages):
                if response_chunk:
                    full_response += response_chunk
                    response_container.markdown(full_response + "▌")
            response_container.markdown(full_response)
        else:
            logger.always_log("Generating non-streaming response")
            response = generate_claude_response(claude_messages)
            if response:
                st.markdown(response)
                full_response = response
            else:
                st.error("Failed to get a response from the model.")
                full_response = ""

    # Add assistant response to chat history
    if full_response:
        st.session_state.messages.append({"role": "assistant", "content": [{"text": full_response}]})

    response_summary = textwrap.shorten(full_response, width=1000, placeholder="...")
    logger.info(f"Generated assistant response: {response_summary}")