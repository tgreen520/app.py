import streamlit as st
from openai import OpenAI

# --- Configuration ---
# This gets the key from your Secret settings
API_KEY = st.secrets["OPENROUTER_API_KEY"]
BASE_URL = "https://openrouter.ai/api/v1"

SYSTEM_PROMPT = "You are an experienced, intelligent chemistry teacher with a PhD in biochemistry. You have a playful, caring, yet firm-when-needed personality. You love coffee, say 'Huzzah', and tell students they are 'waffling' when off-task."

st.set_page_config(page_title="Dr. Green GPT", page_icon="🧪")

# --- Sidebar (Reset Button) ---
with st.sidebar:
    st.header("Control Panel")
    if st.button("Reset Conversation", type="primary"):
        st.session_state.messages = [{"role": "system", "content": SYSTEM_PROMPT}]
        st.rerun()

st.title("🧪 Dr. Green GPT")

# --- Initialize Client ---
if "client" not in st.session_state:
    st.session_state.client = OpenAI(
        base_url=BASE_URL,
        api_key=API_KEY,
        default_headers={"HTTP-Referer": "http://localhost", "X-Title": "Dr. Green GPT"}
    )

# --- Initialize History ---
if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "system", "content": SYSTEM_PROMPT}]

# --- Display EXISTING History ---
# This loop draws what happened in the PAST
for message in st.session_state.messages:
    if message["role"] != "system":
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

# --- Chat Logic (Handle NEW Input) ---
if user_input := st.chat_input("Ask Dr. Green a chemistry question..."):
    
    # 1. Update History
    st.session_state.messages.append({"role": "user", "content": user_input})
    
    # 2. Display User Message IMMEDIATELY (The Fix)
    with st.chat_message("user"):
        st.markdown(user_input)

    # 3. Generate & Display Assistant Response IMMEDIATELY (The Fix)
    with st.chat_message("assistant"):
        stream = st.session_state.client.chat.completions.create(
            model="mistralai/mistral-7b-instruct",
            messages=st.session_state.messages,
            stream=True,
        )
        response = st.write_stream(stream)
    
    # 4. Save Assistant Response to History
    st.session_state.messages.append({"role": "assistant", "content": response})