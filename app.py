import streamlit as st
from openai import OpenAI

# --- Configuration ---
API_KEY = st.secrets["OPENROUTER_API_KEY"]
BASE_URL = "https://openrouter.ai/api/v1"

SYSTEM_PROMPT = "You are an experienced, intelligent chemistry teacher with a PhD in biochemistry. You have a playful, caring, yet firm-when-needed personality. You love coffee, say 'Huzzah', and tell students they are 'waffling' when off-task."

st.set_page_config(page_title="Dr. Green GPT", page_icon="🧪")

# --- Initialize Client ---
client = OpenAI(
    base_url=BASE_URL,
    api_key=API_KEY,
    default_headers={"HTTP-Referer": "http://localhost", "X-Title": "Dr. Green GPT"}
)

# --- Sidebar ---
with st.sidebar:
    st.header("Control Panel")
    if st.button("Reset Conversation", type="primary"):
        st.session_state.messages = [{"role": "system", "content": SYSTEM_PROMPT}]
        st.rerun()

st.title("🧪 Dr. Green GPT")

# --- Initialize History ---
if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "system", "content": SYSTEM_PROMPT}]

# --- Display History ---
for message in st.session_state.messages:
    if message["role"] != "system":
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

# --- Chat Logic ---
if user_input := st.chat_input("Ask Dr. Green a chemistry question..."):
    
    # 1. Show User Message
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)

    # 2. Generate Response
    with st.chat_message("assistant"):
        # Create a placeholder for the "Thinking..." text
        status_placeholder = st.empty()
        status_placeholder.markdown("Dr. Green is thinking...")
        
        try:
            # SWITCHED MODEL TO: Google Gemini 2.0 Flash (Free & Fast)
            stream = client.chat.completions.create(
                model="google/gemini-2.0-flash-exp:free",
                messages=st.session_state.messages,
                stream=True,
            )
            
            # Clear the "thinking" text immediately
            status_placeholder.empty()
            
            # Stream the real answer
            response = st.write_stream(stream)
            
            # 3. Save Response
            st.session_state.messages.append({"role": "assistant", "content": response})
            
        except Exception as e:
            status_placeholder.markdown(f"**Error:** {e}")