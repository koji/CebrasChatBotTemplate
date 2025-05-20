import streamlit as st
import time
import os
import sys
from config import MODELS

# Attempt to import Cerebras SDK and specific error classes
# Set up variables to capture debugging information
import_error_details = ""
sdk_import_paths = []

try:
    # Try to explicitly check if the cerebras module is available
    import importlib.util
    spec = importlib.util.find_spec("cerebras")
    if spec is not None:
        sdk_import_paths.append(f"cerebras module found at: {spec.origin}")
    else:
        sdk_import_paths.append("cerebras module not found in sys.path")
    
    # Capture Python's module search paths
    sdk_import_paths.append("Python sys.path contains:")
    for path in sys.path:
        sdk_import_paths.append(f"  - {path}")
    
    # Now try the actual import
    from cerebras.cloud.sdk import Cerebras
    # Try to import error classes directly from the main SDK package
    # The error classes are likely defined within the main SDK package
    from cerebras.cloud.sdk import APIError, APIConnectionError, AuthenticationError
    CEREBRAS_SDK_AVAILABLE = True
    sdk_import_paths.append("✅ Cerebras SDK import successful")
except ImportError as e:
    CEREBRAS_SDK_AVAILABLE = False
    import_error_details = str(e)
    sdk_import_paths.append(f"❌ Import Error: {import_error_details}")
    
    # Define dummy classes if SDK is not available, so the rest of the code doesn't break
    class Cerebras: pass
    class APIError(Exception): pass
    class APIConnectionError(APIError): pass
    class AuthenticationError(APIError): pass

# --- Helper Functions (Actual API Interaction) ---
def get_cebras_response(api_key, model_id, current_prompt, chat_history_for_api):
    """
    Function to get a response from the Cerebras API.
    """
    if not CEREBRAS_SDK_AVAILABLE:
        return "Error: Cerebras SDK is not installed. Please run `pip install cerebras-cloud-sdk`."

    if not api_key:
        return "Error: Cerebras API Key not provided. Please enter it in the sidebar."

    model_details = MODELS.get(model_id)
    if not model_details:
        return f"Error: Model '{model_id}' not found in local configuration."

    try:
        client = Cerebras(api_key=api_key)

        # Construct the messages payload for the API
        # The API expects the full conversation history, including the latest prompt.
        messages_payload = chat_history_for_api + [{"role": "user", "content": current_prompt}]

        st.info(f"🚀 Sending request to Cerebras API with model: {model_id}...")
        # For non-streaming:
        # completion = client.chat.completions.create(
        #     model=model_id,
        #     messages=messages_payload,
        #     # You might want to add other parameters like temperature, max_tokens, etc.
        #     # max_tokens=model_details.get("tokens") # Example
        # )
        # return completion.choices[0].message.content

        # For streaming:
        full_response_content = ""
        stream = client.chat.completions.create(
            model=model_id,
            messages=messages_payload,
            stream=True,
            # max_tokens=model_details.get("tokens") # Optional: manage max output tokens
        )
        for chunk in stream:
            if chunk.choices and chunk.choices[0].delta and chunk.choices[0].delta.content:
                content_part = chunk.choices[0].delta.content
                yield content_part # Yield each part for streaming in Streamlit UI

    except AuthenticationError:
        return "Error: Authentication failed. Please check your Cerebras API Key."
    except APIConnectionError as e:
        return f"Error: Could not connect to Cerebras API. Details: {e}"
    except APIError as e:
        return f"Error: Cerebras API returned an error. Status: {e.status_code}, Message: {e.message}"
    except Exception as e:
        return f"An unexpected error occurred: {e}"

# --- Streamlit App ---
st.set_page_config(page_title="Cerebras Chatbot", page_icon="🤖")

st.write("Python Path:", sys.executable)
st.write("Python Version:", sys.version)

# Display detailed import debugging information
st.expander("🔍 SDK Import Debug Information").write("\n".join(sdk_import_paths))

st.title("🤖 Cerebras Powered Chatbot")

if not CEREBRAS_SDK_AVAILABLE:
    st.error(
        f"The Cerebras SDK is not installed. Please install it by running `pip install cerebras-cloud-sdk` in your terminal and restart the app.\n\nError details: {import_error_details}",
        icon="🚨"
    )
    
    # Add a command to check the pip installation
    st.code("python -m pip list | grep cerebras", language="bash")
    st.stop()

st.caption("A Streamlit application for interacting with Cerebras models via `cerebras.cloud.sdk`.")

# --- Sidebar for Configuration ---
with st.sidebar:
    st.header("⚙️ Configuration")

    # API Key Input
    # You can also set this as an environment variable CEREBRAS_API_KEY
    env_api_key = os.getenv("CEREBRAS_API_KEY")
    cebras_api_key = st.text_input(
        "🔑 Cerebras API Key",
        type="password",
        value=env_api_key if env_api_key else "",
        help="Enter your Cerebras API key. You can also set the CEREBRAS_API_KEY environment variable."
    )
    if not cebras_api_key and not env_api_key:
        st.warning("Please enter your Cerebras API Key to use the chatbot.")
    elif not cebras_api_key and env_api_key:
        cebras_api_key = env_api_key # Use env var if input is cleared but env var exists

    # Model Selection
    model_options = list(MODELS.keys())
    selected_model_id = st.selectbox(
        "🧠 Select Model",
        options=model_options,
        format_func=lambda model_id: MODELS[model_id]["name"],
        help="Choose the Cerebras model you want to interact with."
    )

    st.markdown("---")
    if selected_model_id:
        model_info = MODELS[selected_model_id]
        st.markdown(f"**Model Details:**")
        st.markdown(f"- **Name:** {model_info['name']}")
        st.markdown(f"- **Max Tokens (Context):** {model_info['tokens']}")
        st.markdown(f"- **Developer:** {model_info['developer']}")
    st.markdown("---")
    st.markdown("ℹ️ This application uses the `cerebras.cloud.sdk`.")


# --- Chat Interface ---

# Initialize chat history in session state
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display previous messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Chat input
if prompt := st.chat_input("What would you like to ask?"):
    if not cebras_api_key:
        st.error("🚨 Please enter your Cerebras API Key in the sidebar before sending a message.")
    elif not selected_model_id:
        st.error("🤔 Please select a model from the sidebar.")
    else:
        # Add user message to chat history and display it
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        # Get assistant response using the SDK
        with st.chat_message("assistant"):
            message_placeholder = st.empty()
            full_response_content = ""

            # Prepare chat history for the API call (current session_state.messages is suitable)
            # The API call itself will receive the prompt as part of the messages list
            try:
                response_stream = get_cebras_response(
                    cebras_api_key,
                    selected_model_id,
                    prompt, # Pass current prompt separately for clarity in function
                    st.session_state.messages[:-1] # Pass history *before* current prompt
                )

                if isinstance(response_stream, str): # Indicates an error string was returned
                    full_response_content = response_stream
                    message_placeholder.error(full_response_content)
                else: # It's a generator for streaming
                    for chunk_content in response_stream:
                        full_response_content += chunk_content
                        message_placeholder.markdown(full_response_content + "▌")
                    message_placeholder.markdown(full_response_content)

            except Exception as e: # Catch any other unexpected errors from the generator
                full_response_content = f"An unexpected error occurred during streaming: {str(e)}"
                message_placeholder.error(full_response_content)

        # Add assistant response (or error) to chat history
        st.session_state.messages.append({"role": "assistant", "content": full_response_content})

# Add a button to clear chat history
if st.sidebar.button("Clear Chat History"):
    st.session_state.messages = []
    st.rerun()

