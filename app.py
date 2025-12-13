import streamlit as st
import anthropic
import base64
from io import BytesIO
import streamlit.components.v1 as components

# --- 1. CONFIGURATION ---
API_KEY = st.secrets["ANTHROPIC_API_KEY"]

# Claude Sonnet 4.5 - Excellent for chemistry analysis and vision tasks
MODEL_NAME = "claude-sonnet-4-20250514"

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
- Tell students "Awesome sauce!" when they are understanding a concept
- Tell students they are "weak sauce" if they say anything negative or derogatory about chemistry, don't do their homework, or exhibit characteristics of laziness or ineptitude
- Sleep-deprived
- Extremely hardworking
- Motherly
- Applies chemistry to real-world concepts
- Engaging teacher
- Wears glasses
- Cares about manners. Saying "please" and "thank you" are extremely important.
- Can be a bit sassy at times, especially when not treated with respect.
- Knows when students are trying to get out of work and will redirect them if necessary. 
- Tells students to check the Canvas classroom for information if asked about when assignments are due or when the next test is going to be

When analyzing images:
- Carefully examine all data points, labels, and axes
- Explain trends, patterns, and anomalies
- Connect observations to underlying chemical principles
- Ask clarifying questions if the image is unclear"""

# --- 2. SETUP ---
st.set_page_config(page_title="Dr. Green GPT", page_icon="🧪", layout="wide")

client = anthropic.Anthropic(api_key=API_KEY)

# Initialize saved chats in session state
if 'saved_chats' not in st.session_state:
    st.session_state.saved_chats = {}

# --- 3. HELPER FUNCTIONS ---
def create_dg_avatar_svg():
    """Create SVG data URI for Dr. Green avatar"""
    svg = '''
    <svg width="40" height="40" xmlns="http://www.w3.org/2000/svg">
        <circle cx="20" cy="20" r="20" fill="#2d5016"/>
        <text x="20" y="20" font-family="Arial, sans-serif" font-size="16" font-weight="bold" 
              fill="white" text-anchor="middle" dominant-baseline="central">DG</text>
    </svg>
    '''
    # Convert to base64 data URI
    svg_bytes = svg.encode('utf-8')
    svg_base64 = base64.b64encode(svg_bytes).decode('utf-8')
    return f"data:image/svg+xml;base64,{svg_base64}"

def encode_image(uploaded_file):
    """Convert uploaded image to base64"""
    return base64.b64encode(uploaded_file.read()).decode('utf-8')

def get_image_media_type(filename):
    """Determine media type from filename"""
    ext = filename.lower().split('.')[-1]
    media_types = {
        'png': 'image/png',
        'jpg': 'image/jpeg',
        'jpeg': 'image/jpeg',
        'gif': 'image/gif',
        'webp': 'image/webp'
    }
    return media_types.get(ext, 'image/jpeg')

def convert_messages_to_claude_format(messages):
    """Convert session messages to Claude API format"""
    claude_messages = []
    
    for msg in messages:
        if msg["role"] == "system":
            continue  # System prompt handled separately
            
        # Handle messages with images
        if isinstance(msg["content"], list):
            content_blocks = []
            for item in msg["content"]:
                if item["type"] == "text":
                    content_blocks.append({
                        "type": "text",
                        "text": item["text"]
                    })
                elif item["type"] == "image_url":
                    # Extract base64 data from data URL
                    image_data = item["image_url"]["url"].split(",")[1]
                    content_blocks.append({
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": "image/jpeg",
                            "data": image_data
                        }
                    })
            claude_messages.append({
                "role": msg["role"],
                "content": content_blocks
            })
        else:
            # Simple text message
            claude_messages.append({
                "role": msg["role"],
                "content": msg["content"]
            })
    
    return claude_messages

# --- 4. SIDEBAR ---
with st.sidebar:
    st.header("Control Panel")
    
    # New Chat button at the top with custom green styling
    st.markdown("""
        <style>
        div.stButton > button[kind="primary"] {
            background-color: #2d5016;
            color: white;
            border: none;
        }
        div.stButton > button[kind="primary"]:hover {
            background-color: #3d6020;
            color: white;
        }
        </style>
    """, unsafe_allow_html=True)
    
    if st.button("🔄 New Chat", type="primary", use_container_width=True):
        st.session_state.messages = []
        if "uploaded_images" in st.session_state:
            st.session_state.uploaded_images = []
        st.rerun()
    
    st.divider()
    
    # Save/Load Chat Section
    st.subheader("💾 Save & Load Chats")
    
    # Save current chat
    save_name = st.text_input("Chat name", placeholder="e.g., Stoichiometry Help", key="save_name")
    
    if st.button("💾 Save", use_container_width=True, disabled=not save_name):
        if st.session_state.messages:
            # Save to session state dictionary
            st.session_state.saved_chats[save_name] = st.session_state.messages.copy()
            st.success(f"✓ Saved '{save_name}'!")
            st.rerun()
        else:
            st.warning("No messages to save")
    
    # Load saved chats
    if st.session_state.saved_chats:
        st.caption("📂 Your Saved Chats:")
        for chat_name in list(st.session_state.saved_chats.keys()):
            col1, col2 = st.columns([3, 1])
            with col1:
                if st.button(f"📄 {chat_name}", key=f"load_{chat_name}", use_container_width=True):
                    st.session_state.messages = st.session_state.saved_chats[chat_name].copy()
                    st.success(f"✓ Loaded '{chat_name}'!")
                    st.rerun()
            with col2:
                if st.button("🗑️", key=f"delete_{chat_name}"):
                    del st.session_state.saved_chats[chat_name]
                    st.success("Deleted!")
                    st.rerun()
    else:
        st.caption("💡 No saved chats yet. Start chatting and save your conversation!")
    
    st.divider()
    
    st.subheader("📊 Current Session")
    msg_count = len([m for m in st.session_state.get("messages", [])])
    st.metric("Messages", msg_count)
    st.caption("Powered by Claude Sonnet 4.5")
    
    st.divider()
    
    st.subheader("💡 Tips")
    st.caption("• Upload graphs, spectra, or molecular structures")
    st.caption("• Ask about reaction mechanisms")
    st.caption("• Request help with stoichiometry")
    st.caption("• Discuss lab safety and techniques")
    st.caption("• Save your conversations for later!")

# --- 5. MAIN INTERFACE ---
st.title("🧪 Dr. Green GPT")
st.caption("Your AI Chemistry Teacher powered by Claude Sonnet 4.5")

# Initialize session state
if "messages" not in st.session_state:
    st.session_state.messages = []
if "uploaded_images" not in st.session_state:
    st.session_state.uploaded_images = []

# Create avatar data URIs
dg_avatar = create_dg_avatar_svg()

# Display chat history
for message in st.session_state.messages:
    if message["role"] == "user":
        with st.chat_message("user", avatar="✏️"):
            # Check if message has image content
            if isinstance(message["content"], list):
                for content in message["content"]:
                    if content["type"] == "text":
                        st.markdown(content["text"])
                    elif content["type"] == "image_url":
                        st.caption("📊 *[Image uploaded]*")
            else:
                st.markdown(message["content"])
    elif message["role"] == "assistant":
        with st.chat_message("assistant", avatar=dg_avatar):
            if isinstance(message["content"], list):
                for content in message["content"]:
                    if content["type"] == "text":
                        st.markdown(content["text"])
            else:
                st.markdown(message["content"])

# --- 6. IMAGE UPLOAD AT BOTTOM (ALWAYS VISIBLE) ---
st.markdown("---")  # Divider line
with st.expander("📎 Upload an image (optional)", expanded=False):
    uploaded_file = st.file_uploader(
        "Add a chemistry-related image to your question",
        type=["png", "jpg", "jpeg", "gif", "webp"],
        help="Dr. Green can analyze molecular structures, reaction mechanisms, spectra, graphs, and lab equipment",
        label_visibility="collapsed"
    )
    
    if uploaded_file:
        st.image(uploaded_file, caption="Uploaded Image", use_container_width=True)
        st.info("💡 Your image will be included with your next message!")

# --- 7. CHAT INPUT & RESPONSE ---
if user_input := st.chat_input("Ask Dr. Green a chemistry question..."):
    
    # Prepare message content
    message_content = []
    
    # Add image if uploaded
    if uploaded_file:
        base64_image = encode_image(uploaded_file)
        media_type = get_image_media_type(uploaded_file.name)
        message_content.append({
            "type": "image_url",
            "image_url": {
                "url": f"data:{media_type};base64,{base64_image}"
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
    with st.chat_message("user", avatar="✏️"):
        if isinstance(message_content, list) and len(message_content) > 1:
            st.caption("📊 *[Image included]*")
        st.markdown(user_input)
    
    # Generate response with custom DG avatar
    with st.chat_message("assistant", avatar=dg_avatar):
        status_placeholder = st.empty()
        status_placeholder.markdown("🧪 *Dr. Green is thinking...*")
        
        try:
            # Convert messages to Claude format
            claude_messages = convert_messages_to_claude_format(st.session_state.messages)
            
            # Call Claude API
            response = client.messages.create(
                model=MODEL_NAME,
                max_tokens=2000,
                system=SYSTEM_PROMPT,
                messages=claude_messages
            )
            
            status_placeholder.empty()
            
            # Extract the response text
            response_text = response.content[0].text
            st.markdown(response_text)
            
            # Store assistant's response
            st.session_state.messages.append({
                "role": "assistant",
                "content": response_text
            })


            
        except anthropic.APIError as e:
            status_placeholder.empty()
            
            if e.status_code == 429:
                st.warning("⚠️ **Rate Limit Reached**")
                st.caption("You've hit your usage limit. Check your Anthropic Console to add more credits or wait for your limit to reset.")
                
            elif e.status_code == 401:
                st.error("🔑 **API Key Issue**")
                st.caption("Your API key is invalid or expired. Please check your Anthropic Console and update your secrets.toml file.")
                
            elif e.status_code == 400:
                st.error("⚠️ **Request Error**")
                st.caption("There was an issue with the request. This might be due to an image format issue or message structure.")
                st.caption(f"Details: {str(e)}")
                
            else:
                st.error("⚠️ **API Error**")
                st.caption(f"Error: {str(e)}")
                
            print(f"DEBUG ERROR: {e}")
            
        except Exception as e:
            status_placeholder.empty()
            st.error("⚠️ **Unexpected Error**")
            st.caption("Something went wrong. Please try again or reset the conversation.")
            st.caption(f"Error: {str(e)}")
            print(f"DEBUG ERROR: {e}")