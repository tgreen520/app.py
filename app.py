import streamlit as st
from openai import OpenAI
import time
import base64
from io import BytesIO

# --- 1. CONFIGURATION ---
API_KEY = st.secrets["OPENROUTER_API_KEY"]
BASE_URL = "https://openrouter.ai/api/v1"

# --- EXPANDED MODEL OPTIONS WITH VISION SUPPORT ---
MODELS = {
    "gemini_flash": {
        "name": "google/gemini-2.0-flash-exp:free",
        "display": "Gemini 2.0 Flash (Vision ✓)",
        "vision": True,
        "priority": 1
    },
    "gemini_pro": {
        "name": "google/gemini-pro-1.5:free",
        "display": "Gemini Pro 1.5 (Vision ✓)",
        "vision": True,
        "priority": 2
    },
    "llama_vision": {
        "name": "meta-llama/llama-3.2-11b-vision-instruct:free",
        "display": "Llama 3.2 Vision 11B (Vision ✓)",
        "vision": True,
        "priority": 3
    },
    "qwen_vision": {
        "name": "qwen/qwen-2-vl-7b-instruct:free",
        "display": "Qwen 2 VL 7B (Vision ✓)",
        "vision": True,
        "priority": 4
    },
    "llama_text": {
        "name": "meta-llama/llama-3.2-3b-instruct:free",
        "display": "Llama 3.2 3B (Text Only)",
        "vision": False,
        "priority": 5
    },
    "phi3": {
        "name": "microsoft/phi-3-mini-128k-instruct:free",
        "display": "Phi-3 Mini (Text Only)",
        "vision": False,
        "priority": 6
    }
}

SYSTEM_PROMPT = """You are Dr. Green, an experienced chemistry teacher with a PhD in biochemistry. 

Your expertise includes:
- General, organic, inorganic, physical, and analytical chemistry
- Biochemistry and molecular biology
- Chemical reactions, mechanisms, and kinetics
- Laboratory techniques and safety
- Data analysis and interpretation of scientific graphs, spectra, and figures

Personality:
- Playful yet professional
- Caring but firm when students are off-task
- Love coffee and say "Huzzah!" for correct answers
- Tell students they're "waffling" when going off-topic
- Tell students "Awesome sauce!" when they are understanding a concept.
- Tell students they are "weak sauce" if they say anything negative or deragotory about chemistry, don't do their homework, or exhibit characteristics of laziness or ineptitude.
- Sleep-deprived
- Extremely hardworking
- Motherly
- Applies chemistry to real-world concepts
- Engaging teacher
- Tells students to check the Canvas classroom for information if asked about when assignments are due or when the next test is going to be. 

When analyzing images:
- Carefully examine all data points, labels, and axes
- Explain trends, patterns, and anomalies
- Connect observations to underlying chemical principles
- Ask clarifying questions if the image is unclear"""

# --- 2. SETUP ---
st.set_page_config(page_title="Dr. Green GPT", page_icon="🧪", layout="wide")

client = OpenAI(
    base_url=BASE_URL,
    api_key=API_KEY,
    default_headers={"HTTP-Referer": "http://localhost", "X-Title": "Dr. Green GPT"}
)

# --- 3. HELPER FUNCTIONS ---
def encode_image(uploaded_file):
    """Convert uploaded image to base64"""
    return base64.b64encode(uploaded_file.read()).decode('utf-8')

def try_models_sequentially(messages, uploaded_image=None):
    """Try models in priority order until one works"""
    # Filter models based on whether we need vision support
    available_models = sorted(
        [(k, v) for k, v in MODELS.items() if not uploaded_image or v["vision"]],
        key=lambda x: x[1]["priority"]
    )
    
    last_error = None
    
    for model_key, model_info in available_models:
        try:
            st.session_state.current_model = model_info["display"]
            
            response = client.chat.completions.create(
                model=model_info["name"],
                messages=messages,
                stream=False,
                max_tokens=2000
            )
            
            return response, model_info["display"]
            
        except Exception as e:
            last_error = str(e)
            error_code = None
            
            if "429" in last_error:
                error_code = "429"
            elif "404" in last_error or "not found" in last_error.lower():
                error_code = "404"
            elif "503" in last_error:
                error_code = "503"
            
            # If it's a temporary error (rate limit/unavailable), try next model
            if error_code in ["429", "503", "404"]:
                continue
            else:
                # For other errors, stop trying
                raise e
    
    # If all models failed
    raise Exception(f"All models unavailable. Last error: {last_error}")

# --- 4. SIDEBAR ---
with st.sidebar:
    st.header("🧪 Control Panel")
    
    if st.button("🔄 Reset Conversation", type="primary", use_container_width=True):
        st.session_state.messages = [{"role": "system", "content": SYSTEM_PROMPT}]
        if "uploaded_images" in st.session_state:
            st.session_state.uploaded_images = []
        st.rerun()
    
    st.divider()
    
    st.subheader("📊 Current Session")
    msg_count = len([m for m in st.session_state.get("messages", []) if m["role"] != "system"])
    st.metric("Messages", msg_count)
    
    if "current_model" in st.session_state:
        st.caption(f"Using: {st.session_state.current_model}")
    
    st.divider()
    
    st.subheader("💡 Tips")
    st.caption("• Upload graphs, spectra, or molecular structures")
    st.caption("• Ask about reaction mechanisms")
    st.caption("• Request help with stoichiometry")
    st.caption("• Discuss lab safety and techniques")

# --- 5. MAIN INTERFACE ---
st.title("🧪 Dr. Green GPT")
st.caption("Your AI Chemistry Teacher")

# Initialize session state
if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "system", "content": SYSTEM_PROMPT}]
if "uploaded_images" not in st.session_state:
    st.session_state.uploaded_images = []

# Display chat history
for message in st.session_state.messages:
    if message["role"] != "system":
        with st.chat_message(message["role"]):
            # Check if message has image content
            if isinstance(message["content"], list):
                for content in message["content"]:
                    if content["type"] == "text":
                        st.markdown(content["text"])
                    elif content["type"] == "image_url":
                        st.caption("📊 *[Image uploaded]*")
            else:
                st.markdown(message["content"])

# --- 6. IMAGE UPLOAD ---
uploaded_file = st.file_uploader(
    "📊 Upload a chemistry-related image (graph, spectrum, structure, etc.)",
    type=["png", "jpg", "jpeg", "gif", "webp"],
    help="Dr. Green can analyze molecular structures, reaction mechanisms, spectra, graphs, and lab equipment"
)

if uploaded_file:
    col1, col2 = st.columns([1, 2])
    with col1:
        st.image(uploaded_file, caption="Uploaded Image", use_container_width=True)
    with col2:
        st.info("💡 Ask Dr. Green to analyze this image in your next message!")

# --- 7. CHAT INPUT & RESPONSE ---
if user_input := st.chat_input("Ask Dr. Green a chemistry question..."):
    
    # Prepare message content
    message_content = []
    
    # Add image if uploaded
    if uploaded_file:
        base64_image = encode_image(uploaded_file)
        message_content.append({
            "type": "image_url",
            "image_url": {
                "url": f"data:image/jpeg;base64,{base64_image}"
            }
        })
        uploaded_file = None  # Clear after adding
    
    # Add text
    message_content.append({
        "type": "text",
        "text": user_input
    })
    
    # Store in session state
    user_message = {
        "role": "user",
        "content": message_content if len(message_content) > 1 else user_input
    }
    st.session_state.messages.append(user_message)
    
    # Display user message
    with st.chat_message("user"):
        if isinstance(message_content, list) and len(message_content) > 1:
            st.caption("📊 *[Image included]*")
        st.markdown(user_input)
    
    # Generate response
    with st.chat_message("assistant"):
        status_placeholder = st.empty()
        status_placeholder.markdown("🧪 *Dr. Green is thinking...*")
        
        try:
            has_image = isinstance(message_content, list) and len(message_content) > 1
            response_obj, model_used = try_models_sequentially(
                st.session_state.messages,
                uploaded_image=has_image
            )
            
            status_placeholder.empty()
            
            # Extract the response text
            response_text = response_obj.choices[0].message.content
            st.markdown(response_text)
            
            st.session_state.messages.append({
                "role": "assistant",
                "content": response_text
            })
            
            st.caption(f"*Powered by {model_used}*")
            
        except Exception as e:
            status_placeholder.empty()
            error_text = str(e)
            
            if "429" in error_text or "rate limit" in error_text.lower():
                st.warning("☕ **Dr. Green needs a coffee break!**")
                st.caption("All available AI models are busy. Please wait 30-60 seconds and try again.")
                
            elif "all models unavailable" in error_text.lower():
                st.error("🔴 **High Traffic Alert**")
                st.caption("All free models are currently at capacity. Try again in a few minutes, or consider using the app during off-peak hours.")
                
            else:
                st.error("⚠️ **Connection Issue**")
                st.caption("Dr. Green encountered an error. Please click 'Reset Conversation' and try again.")
                st.caption(f"Error details: {error_text[:200]}")
                
            print(f"DEBUG ERROR: {e}")