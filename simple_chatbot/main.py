# file: main.py
import streamlit as st
import boto3
from botocore.exceptions import ClientError
import logging
import textwrap

def setup_logger():
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.DEBUG)

    # Remove any existing handlers
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)

    # Create a new handler
    handler = logging.StreamHandler()
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)

    logger.addHandler(handler)

    return logger

# Setup the logger
logger = setup_logger()

# Initialize the AWS Bedrock client
bedrock = boto3.client(
    service_name='bedrock-runtime',
    region_name='us-east-1'
)

# Streamlit title for app and page and subtitle
st.set_page_config(page_title="Neo", layout="wide")
st.title("neo")
st.caption("a chatbot for claude models on aws bedrock")

# Log the start of the session
logger.info("Starting new session")

# System prompt options
SYSTEM_PROMPTS = {
    "Default Assistant": "You are Claude, an AI assistant created by Anthropic to be helpful, harmless, and honest.",
    "Coding Assistant": "You are a coding assistant, expert in multiple programming languages. Provide clear, concise, and efficient code solutions.",
    "Creative Writer": "You are a creative writing assistant, skilled in various genres and styles. Help users craft engaging stories and narratives.",
    "Custom": ""  # Empty string for custom input
}

# Model options
MODEL_OPTIONS = {
    "Claude 3.5 Sonnet": "anthropic.claude-3-5-sonnet-20240620-v1:0",
    "Claude 3 Haiku":    "anthropic.claude-3-haiku-20240307-v1:0",    
    "Claude 3 Sonnet":   "anthropic.claude-3-sonnet-20240229-v1:0",
    "Claude 2.1":        "anthropic.claude-v2:1",
    "Claude 2.0":        "anthropic.claude-v2",
    "Claude Instant":    "anthropic.claude-instant-v1"
}

# Initialize system_prompt in session state if it doesn't exist
if "system_prompt" not in st.session_state:
    st.session_state.system_prompt = SYSTEM_PROMPTS["Default Assistant"]
    logger.info(f"Initial system prompt: {st.session_state.system_prompt}")

# Function to clear chat history
def clear_chat_history():
    st.session_state.messages = []
    logger.info("Chat history cleared")

# Sidebar for settings
with st.sidebar:
    # Add a "Clear Chat History" button
    if st.button("Clear Chat History", key="refresh_chat"):
        clear_chat_history()

    st.header("Settings")
    use_streaming = st.checkbox("Use streaming responses", value=True)

    st.subheader("Model Selection")
    selected_model_name = st.selectbox("Select Model", list(MODEL_OPTIONS.keys()))
    selected_model_id = MODEL_OPTIONS[selected_model_name]

    st.subheader("Model Parameters")
    temperature = st.slider("Temperature", min_value=0.0, max_value=1.0, value=0.5, step=0.01)
    top_k = st.slider("Top K", min_value=0, max_value=500, value=100, step=10)

    st.subheader("System Prompt")
    selected_prompt_name = st.selectbox("Select System Prompt", list(SYSTEM_PROMPTS.keys()))

    if selected_prompt_name == "Custom":
        system_prompt = st.text_area("Custom System Prompt", value="", height=100)
    else:
        system_prompt = st.text_area("System Prompt", value=SYSTEM_PROMPTS[selected_prompt_name], height=100, disabled=True)

    # Check if system prompt has changed
    if system_prompt != st.session_state.system_prompt:
        st.session_state.system_prompt = system_prompt
        logger.info(f"System prompt changed to: {system_prompt}")

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
            modelId=selected_model_id,
            messages=formatted_messages,
            system=[{"text": st.session_state.system_prompt}],
            inferenceConfig={"temperature": temperature},
            additionalModelRequestFields={"top_k": top_k}
        )
        logger.debug(f"Received response: {response}")

        # Extract the response content
        if 'output' in response and 'message' in response['output']:
            message = response['output']['message']
            if 'content' in message and len(message['content']) > 0:
                return message['content'][0]['text']

        # If the expected structure is not found, return an error message
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
            modelId=selected_model_id,
            messages=messages,
            system=[{"text": st.session_state.system_prompt}],
            inferenceConfig={"temperature": temperature},
            additionalModelRequestFields={"top_k": top_k}
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
    # Log the user input
    logger.info(f"Received user input: {prompt}")

    # Add user message to chat history
    st.session_state.messages.append({"role": "user", "content": [{"text": prompt}]})
    # Display user message in chat message container
    with st.chat_message("user"):
        st.markdown(prompt)

    # Prepare messages for Claude
    claude_messages = [{"role": msg["role"], "content": msg["content"]} for msg in st.session_state.messages]

    # Generate Claude's response
    with st.chat_message("assistant"):
        if use_streaming:
            # Streaming response
            logger.info("Generating streaming response")
            response_container = st.empty()
            full_response = ""
            for response_chunk in generate_claude_streaming_response(claude_messages):
                if response_chunk:
                    full_response += response_chunk
                    response_container.markdown(full_response + "▌")
            response_container.markdown(full_response)
        else:
            # Non-streaming response
            logger.info("Generating non-streaming response")
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

    # Log the assistant's response
    response_summary = textwrap.shorten(full_response, width=1000, placeholder="...")
    logger.info(f"Generated assistant response: {response_summary}")
