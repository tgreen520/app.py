import streamlit as st
from openai import OpenAI

# --- 1. CONFIGURATION & SAFETY SWITCH ---
# ==========================================
API_KEY = st.secrets["OPENROUTER_API_KEY"]
BASE_URL = "https://openrouter.ai/api/v1"

# --- MODEL BACKUP LIST (The Safety Switch) ---
# If a model crashes (404/429), just change 'SELECTED_MODEL' to use a different option.

# OPTION 1: Google Gemini 2.0 Flash (Fastest, Smartest, but sometimes busy)
MODEL_OPTION_1 = "google/gemini-2.0-flash-exp:free"

# OPTION 2: Llama 3.2 3B (Very fast, reliable, great for chat)
MODEL_OPTION_2 = "meta-llama/llama-3.2-3b-instruct:free"

# OPTION 3: Microsoft Phi-3 Mini (The "Secret Weapon" - highly available)
MODEL_OPTION_3 = "microsoft/phi-3-mini-128k-instruct:free"

# OPTION 4: Mistral 7B (The classic reliable backup)
MODEL_OPTION_4 = "mistralai/mistral-7b-instruct:free"

# ------------------------------------------
# >>>> CHANGE THIS LINE TO SWITCH MODELS <<<<
MODEL_NAME = MODEL_OPTION_2
# ------------------------------------------

SYSTEM_PROMPT = "You are an experienced, intelligent chemistry teacher with a PhD in biochemistry. You have a playful, caring, yet firm-when-needed personality. You love coffee, say 'Huzzah', and tell students they are 'waffling' when off-task."

# --- 2. SETUP APP ---
# ==========================================
st.set_page_config(page_title="Dr. Green GPT", page_icon="🧪")

client = OpenAI(
    base_url=BASE_URL,
    api_key=API_KEY,
    default_headers={"HTTP-Referer": "http://localhost", "X-Title": "Dr. Green GPT"}
)

# --- 3. SIDEBAR CONTROLS ---
# ==========================================
with st.sidebar:
    st.header("Control Panel")
    if st.button("Reset Conversation", type="primary"):
        st.session_state.messages = [{"role": "system", "content": SYSTEM_PROMPT}]
        st.rerun()
    
    # Helpful debug info so you know which brain is running
    st.caption(f"🧠 Brain: {MODEL_NAME}")

st.title("🧪 Dr. Green GPT")

# --- 4. HISTORY MANAGEMENT ---
# ==========================================
if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "system", "content": SYSTEM_PROMPT}]

# Display existing history
for message in st.session_state.messages:
    if message["role"] != "system":
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

# --- 5. CHAT LOGIC ---
# ==========================================
if user_input := st.chat_input("Ask Dr. Green a chemistry question..."):
    
    # A. Display User Message
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)

    # B. Generate Response
    with st.chat_message("assistant"):
        status_placeholder = st.empty()
        status_placeholder.markdown("Dr. Green is thinking...")
        
        try:
            stream = client.chat.completions.create(
                model=MODEL_NAME,
                messages=st.session_state.messages,
                stream=True,
            )
            
            # Wipe the status text once the real answer starts
            status_placeholder.empty()
            response = st.write_stream(stream)
            
            st.session_state.messages.append({"role": "assistant", "content": response})
            
        except Exception as e:
            status_placeholder.error(f"**Connection Error:** {e}")
            st.error(f"⚠️ The model '{MODEL_NAME}' is currently down or busy. Please open `app.py` and switch to a different MODEL_OPTION at the top of the file.")