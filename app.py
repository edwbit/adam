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
    "deepseek-r1-distill-llama-70b": {"name": "deepseek-r1-distill-llama-70b", "tokens": 32768},
    "deepseek-r1-distill-qwen-32b": {"name": "deepseek-r1-distill-qwen-32b", "tokens": 16384},   
    "deepseek-r1-distill-llama-70b-specdec": {"name":"deepseek-r1-distill-llama-70b-specdec", "tokens":16384},
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
    min_value=8192,
    max_value=max_tokens_range,
    value=min(16384, max_tokens_range),
    step=8192
    help=f"Adjust the maximum number of tokens (words) for the model's response. Max for selected model: {max_tokens_range}"
)

#doctrine option
doctrine = ["Roman Catholic and other Sunday Keepers","Seventh-day Adventist"]
selected_doctrine = st.selectbox(
    'Select doctrine', doctrine, index=0,format_func=lambda x: x.upper()
)

# Display chat messages from history in a scrollable container if there are messages
if st.session_state.messages:
    # st.markdown('<div class="chat-container">', unsafe_allow_html=True)
    for message in st.session_state.messages:
        avatar = '📖' if message["role"] == "assistant" else '😊'
        with st.chat_message(message["role"], avatar=avatar):
            st.markdown(message["content"])
    # st.markdown('</div>', unsafe_allow_html=True)
else:
    st.write("No chat history yet. Start a conversation by typing a message.")

# Function to generate chat responses
def generate_chat_responses(chat_completion) -> Generator[str, None, None]:
    for chunk in chat_completion:
        if chunk.choices[0].delta.content:
            yield chunk.choices[0].delta.content

# Function to detect if input is a Bible verse reference
def is_bible_verse(input_text):
    # Basic regex to check for common Bible reference formats, e.g., "john 1:1"
    pattern = r'^([1-3] )?(?:1st|2nd|3rd|[1-3])? ?[a-zA-Z]+(?: [a-zA-Z]+)?(?: [a-zA-Z]+)?,? \d+:\d+$'
    return bool(re.match(pattern, input_text, re.IGNORECASE))
    # return bool(re.match(r'^[1-3]?[a-zA-Z]+\s\d+:\d+', input_text))

# Function to check if the input is a name (for genealogy or notable works)
def is_name(input_text):
    # You can improve this with more sophisticated checks
    # For now, this is a simple assumption: if it's a single word, treat it as a name
    return len(input_text.split()) == 1
# define Bible version
bible = "New King James Version"

#guidelines
guidelines = f"""Use clear, specific words based on {selected_doctrine} doctrine. Use bulleted list for formatting and readability. Avoid unnecessary instructions or bland statements.
        Provide response in proper order and do not add anything else. Provide high quality and real-life illustration if required."""

#structure
opening_hook = f"""Grab attention and connect with the audience.
Start with a relatable biblical story, a striking question, or a vivid image. Refrain from using corny stories or cliche"""

core_principle = f"""Introduce a short Bible verse, quote, or principle tied to your theme.
Briefly provide three in-depth explanations of the context or meaning in simple terms. Support these with biblical verses"""

problem =f""" Highlight a relatable struggle or tension.
Describe a common human challenge tied to your theme (e.g., doubt, fear, exhaustion).
Use biblical accounts.
"""

turn= f"""Offer hope and a solution through the core principle.
Connect the struggle to the scripture/principle.
Share how it transforms the problem—practical or spiritual insight
Use biblical accounts.
"""

application = f"""Make it actionable for the audience.
Give 1-2 clear, practical steps for life application.
Use biblical accounts.
"""

closing = f"""Inspire and send them out with purpose.
End with a powerful statement, prayer, or call to action.
"""

# Function to generate appropriate response based on the input type
def generate_response_based_on_input(prompt):
    if is_bible_verse(prompt):
        return f"""Using {bible}, {guidelines} :
        Provide Sermon Title:
        A. {opening_hook}
        B> {core_principle}
        C. {problem}
        D. {turn}
        E. {application}
        F. {closing}        
        These must be based on the Bible verse {prompt}. 
       """
    elif is_name(prompt):
        return f"Using {bible}, Provide biblical genealogy, historical biography, spouse name or concubines if any for the name {prompt}. {guidelines}"
    else:
        return f"Using {bible}, Provide a biblical description for the keyword '{prompt}'. Provide signigicant events and controversies. Provide historical events that support it.{guidelines}"

# Handle new chat input
if prompt := st.chat_input("Type a biblical character or bible verse"):
    # Generate specific task based on user input
    task_description = generate_response_based_on_input(prompt)
    # st.session_state.messages.append({"role": "user", "content": f"{prompt} \n{task_description}\nProvide links to source if you can"})
    st.session_state.messages.append({"role": "user", "content": f" Provide comprehensive: {prompt} \n{task_description} \nProvide cross-references in the Bible if any"})

    with st.chat_message("user", avatar='😊'):
        st.markdown(prompt)

    try:
        chat_completion = client.chat.completions.create(
            model=model_option,
            messages=[
                {"role": m["role"], "content": m["content"]}
                for m in st.session_state.messages
            ],
            temperature=0.6,
            max_tokens=max_tokens,
            reasoning_format="hidden"
            stream=True
        )
        with st.chat_message("assistant", avatar="📖"):
            chat_responses_generator = generate_chat_responses(chat_completion)
            full_response = st.write_stream(chat_responses_generator)
    except Exception as e:
        st.error(e, icon="🚨")
    
    if isinstance(full_response, str):
        st.session_state.messages.append({"role": "assistant", "content": full_response})
    else:
        combined_response = "\n".join(str(item) for item in full_response)
        st.session_state.messages.append({"role": "assistant", "content": combined_response})
