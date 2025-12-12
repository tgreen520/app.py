import streamlit as st
from openai import OpenAI

# --- Configuration ---
API_KEY = st.secrets["OPENROUTER_API_KEY"]
BASE_URL = "https://openrouter.ai/api/v1"

# --- MODEL SAFETY SWITCH ---
# If one fails, just change the variable below to use a backup!
# Option 1: Llama 3.2 3B (Fastest, most reliable free model right now)
MODEL_OPTION_1 = "meta-llama/llama-3.2-3b-instruct:free"

# Option 2: Google Gemini 2.0 Flash (Smartest, but sometimes busy/429 errors)
MODEL_OPTION_2 = "google/gemini-2.0-flash-exp:free"

# Option 3: Zephyr 7B (Old reliable backup)
MODEL_OPTION_3 = "huggingfaceh4/zephyr-7b-beta:free"

# CURRENT SELECTION:
MODEL_NAME = MODEL_OPTION_1 

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
        status_placeholder = st.empty()
        status_placeholder.markdown("Dr. Green is thinking...")
        
        try:
            stream = client.chat.completions.create(
                model=MODEL_NAME, # Uses the selection from the top
                messages=st.session_state.messages,
                stream=True,
            )
            
            status_placeholder.empty()
            response = st.write_stream(stream)
            
            st.session_state.messages.append({"role": "assistant", "content": response})
            
        except Exception as e:
            # If the model fails, show a helpful error
            status_placeholder.error(f"**Model Error:** {e}")
            st.error(f"The model '{MODEL_NAME}' is currently unavailable. Please try changing the MODEL_NAME at the top of app.py to MODEL_OPTION_2 or MODEL_OPTION_3.")