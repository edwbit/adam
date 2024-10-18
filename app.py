import re
import streamlit as st
from typing import Generator
from groq import Groq

# Set up the page configuration
st.set_page_config(page_icon="🕎", layout="centered", page_title="Groq Adam")

st.sidebar.title("Groq Adam")  # App name
st.sidebar.caption("App created by AI")
api_key = st.sidebar.text_input("Enter your API key and press Enter", type="password")

if st.sidebar.button("New Chat"):
    st.session_state.messages = []  # Clear the chat history

# Initialize the Groq client with the provided API key
client = Groq(api_key=api_key)

st.subheader("Groq Adam", divider="rainbow", anchor="false")

# Initialize chat history and selected model
if "messages" not in st.session_state:
    st.session_state.messages = []

if "selected_model" not in st.session_state:
    st.session_state.selected_model = None

models = {
    "llama-3.2-90b-text-preview": {"name": "llama-3.2-90b-text-preview", "tokens": 8192},
    "mixtral-8x7b-32768": {"name": "Mixtral-8x7b-Instruct-v0.1", "tokens": 32768},
}

# Layout for model selection and max token slider
model_option = st.selectbox(
    "Choose a model:",
    options=list(models.keys()),
    format_func=lambda x: models[x]["name"],
    index=0
)

# Detect model change and clear chat history if the model has changed
if st.session_state.selected_model != model_option:
    st.session_state.messages = []
    st.session_state.selected_model = model_option

max_tokens_range = models[model_option]["tokens"]

max_tokens = st.slider(
    "Max Tokens:",
    min_value=1024,
    max_value=max_tokens_range,
    value=min(32768, max_tokens_range),
    step=1024,
    help=f"Adjust the maximum number of tokens (words) for the model's response. Max for selected model: {max_tokens_range}"
)

# Custom CSS for the scrollable chat history
st.markdown("""
    <style>
        .chat-container {
            max-height: 400px;
            overflow-y: auto;
            border: 1px solid #ccc;
            padding: 10px;
            margin-bottom: 10px;
        }
    </style>
    """, unsafe_allow_html=True)

# Display chat messages from history in a scrollable container if there are messages
if st.session_state.messages:
    st.markdown('<div class="chat-container">', unsafe_allow_html=True)
    for message in st.session_state.messages:
        avatar = '✨' if message["role"] == "assistant" else '🤠'
        with st.chat_message(message["role"], avatar=avatar):
            st.markdown(message["content"])
    st.markdown('</div>', unsafe_allow_html=True)
else:
    st.write("No chat history yet. Start a conversation by typing a message.")

# Function to generate chat responses
def generate_chat_responses(chat_completion) -> Generator[str, None, None]:
    full_response = ""
    for chunk in chat_completion:
        try:
            # Check if there is content in the response chunk
            if chunk.choices[0].delta.content:
                chunk_content = chunk.choices[0].delta.content
                st.write(f"Chunk received: {chunk_content}")  # Debugging log for each chunk
                yield chunk_content  # Yield the chunk content
                full_response += chunk_content  # Collect full response
        except Exception as e:
            st.error(f"Error processing response chunk: {e}")

    return full_response  # Return the full response after streaming

# Handle new chat input
if prompt := st.chat_input("What do you want to ask?"):
    # Generate specific task based on user input
    task_description = generate_response_based_on_input(prompt)
    st.session_state.messages.append({"role": "user", "content": f"{prompt} \n{task_description}\nProvide links to source if you can"})

    with st.chat_message("user", avatar='🤠'):
        st.markdown(prompt)

    full_response = ""  # Initialize full_response as an empty string

    try:
        chat_completion = client.chat.completions.create(
            model=model_option,
            messages=[
                {"role": m["role"], "content": m["content"]}
                for m in st.session_state.messages
            ],
            max_tokens=max_tokens,
            stream=True
        )

        with st.chat_message("assistant", avatar="✨"):
            # Collect responses from the generator and display them immediately
            chat_responses_generator = generate_chat_responses(chat_completion)
            for chunk in chat_responses_generator:
                st.markdown(chunk)  # Immediately display each chunk

    except Exception as e:
        st.error(e, icon="🚨")

    # Ensure full_response is appended after AI interaction
    if full_response:
        st.session_state.messages.append({"role": "assistant", "content": full_response})
    else:
        st.session_state.messages.append({"role": "assistant", "content": "Sorry, I couldn't process your request."})

