import streamlit as st
from openai import OpenAI
import time

# --- 1. CONFIGURATION & SAFETY SWITCH ---
# ==========================================
API_KEY = st.secrets["OPENROUTER_API_KEY"]
BASE_URL = "https://openrouter.ai/api/v1"

# --- MODEL BACKUP LIST ---
# Option 1: Google Gemini 2.0 Flash (Fastest, Smartest)
MODEL_OPTION_1 = "google/gemini-2.0-flash-exp:free"

# Option 2: Llama 3.2 3B (Fast, reliable)
MODEL_OPTION_2 = "meta-llama/llama-3.2-3b-instruct:free"

# Option 3: Microsoft Phi-3 Mini (High availability backup)
MODEL_OPTION_3 = "microsoft/phi-3-mini-128k-instruct:free"

# Option 4: Mistral 7B (Classic backup)
MODEL_OPTION_4 = "mistralai/mistral-7b-instruct:free"

# >>>> CURRENT MODEL <<<<
# I switched this to OPTION 3 (Phi-3) as it is often less busy than Llama right now.
MODEL_NAME = MODEL_OPTION_1 

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
            # C. ERROR HANDLING (The Fix)
            status_placeholder.empty() # Remove the "Thinking" text
            
            error_text = str(e)
            
            # Check if it's the specific "Rate Limit" (429) error
            if "429" in error_text:
                st.warning("☕ **Dr. Green needs a coffee break!**")
                st.caption("Too many students are asking questions at once (Server Traffic). Please wait 30 seconds and try again.")
            
            # Check if it's a "Not Found" (404) error
            elif "404" in error_text:
                st.error("⚠️ **System Update:** This version of Dr. Green is currently offline.")
                st.caption("Please tell your teacher to switch the 'MODEL_OPTION' in the code.")
                
            # Generic catch-all for other errors
            else:
                st.error("⚠️ **Connection Hiccup**")
                st.caption("Dr. Green lost the connection. Please click 'Reset Conversation' or try again.")
                # We print the real error to the backend console for YOU to see, but hide it from students
                print(f"DEBUG ERROR: {e}")