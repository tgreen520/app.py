import streamlit as st
from openai import OpenAI

# --- Configuration ---
API_KEY = st.secrets["OPENROUTER_API_KEY"]
BASE_URL = "https://openrouter.ai/api/v1"

# Define the personality once so we can reuse it
SYSTEM_PROMPT = "You are an experienced, intelligent chemistry teacher with a PhD in biochemistry. You have a playful, caring, yet firm-when-needed personality. You love coffee, say 'Huzzah', and tell students they are 'waffling' when off-task."

st.set_page_config(page_title="Dr. Green GPT", page_icon="🧪")

# --- Sidebar (The New Part) ---
with st.sidebar:
    st.header("Control Panel")
    # The 'type="primary"' makes the button red/prominent
    if st.button("Reset Conversation", type="primary"):
        # 1. Reset history to just the system prompt
        st.session_state.messages = [{"role": "system", "content": SYSTEM_PROMPT}]
        # 2. Rerun the app to update the screen immediately
        st.rerun()

st.title("🧪 Dr. Green GPT")

# --- Initialize Client ---
st.session_state.client = OpenAI(
    base_url=BASE_URL,
    api_key=API_KEY,
    default_headers={"HTTP-Referer": "http://localhost", "X-Title": "Dr. Green GPT"}
)

# --- Initialize History ---
if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "system", "content": SYSTEM_PROMPT}]

# --- Display Chat History ---
for message in st.session_state.messages:
    if message["role"] != "system":
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

# --- Chat Logic ---
if user_input := st.chat_input("Ask Dr. Green a chemistry question..."):
    with st.chat_message("user"):
        st.markdown(user_input)
    
    st.session_state.messages.append({"role": "user", "content": user_input})

    with st.chat_message("assistant"):
        stream = st.session_state.client.chat.completions.create(
            model="mistralai/mistral-7b-instruct",
            messages=st.session_state.messages,
            stream=True,
        )
        response = st.write_stream(stream)
    
    st.session_state.messages.append({"role": "assistant", "content": response})