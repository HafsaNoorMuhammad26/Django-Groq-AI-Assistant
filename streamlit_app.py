import streamlit as st
from groq import Groq
import os
from dotenv import load_dotenv

# Load .env file (for local development)
load_dotenv()

# Try to get API key from multiple sources
try:
    GROQ_API_KEY = st.secrets["GROQ_API_KEY"]
except:
    GROQ_API_KEY = os.getenv("GROQ_API_KEY")

if not GROQ_API_KEY:
    st.error("❌ GROQ_API_KEY not found! Please add it to .env or secrets.toml")
    st.stop()

# Initialize Groq client
client = Groq(api_key=GROQ_API_KEY)

# ===== PAGE CONFIG =====
st.set_page_config(
    page_title="Legal & Wellness AI",
    page_icon="⚖️",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# ===== DARK MODE TOGGLE =====
# Initialize theme in session state
if "theme" not in st.session_state:
    st.session_state.theme = "light"

def toggle_theme():
    st.session_state.theme = "dark" if st.session_state.theme == "light" else "light"

# Theme toggle button in sidebar
with st.sidebar:
    st.markdown("## ⚙️ Settings")
    if st.button("🌙" if st.session_state.theme == "light" else "☀️", help="Toggle Dark Mode"):
        toggle_theme()
        st.rerun()
    st.markdown("---")
    st.markdown("### About")
    st.markdown("Legal & Wellness AI Assistant powered by Groq API")

# ===== CUSTOM CSS FOR DARK MODE =====
if st.session_state.theme == "dark":
    st.markdown("""
        <style>
        /* Dark mode styles */
        .stApp {
            background-color: #1a1a2e;
        }
        .stApp header {
            background-color: #16213e;
        }
        .stChatMessage {
            background-color: #2a2a4a !important;
            color: #e0e0e0 !important;
        }
        .stChatMessage div[data-testid="stChatMessage"] {
            background-color: #2a2a4a !important;
            color: #e0e0e0 !important;
        }
        .stChatMessage .stMarkdown {
            color: #e0e0e0 !important;
        }
        .stTextInput > div > div > input {
            background-color: #2a2a4a !important;
            color: #e0e0e0 !important;
            border-color: #4a4a6a !important;
        }
        .stButton > button {
            background-color: #4a6fa5 !important;
            color: white !important;
        }
        .stButton > button:hover {
            background-color: #5a7fb5 !important;
        }
        .stRadio > div {
            background-color: #2a2a4a !important;
            color: #e0e0e0 !important;
            border-radius: 10px;
            padding: 10px;
        }
        .stRadio label {
            color: #e0e0e0 !important;
        }
        .stMarkdown h1, .stMarkdown h2, .stMarkdown h3 {
            color: #e0e0e0 !important;
        }
        .stMarkdown p {
            color: #d0d0d0 !important;
        }
        .element-container {
            color: #e0e0e0 !important;
        }
        /* Scrollbar */
        ::-webkit-scrollbar {
            width: 8px;
        }
        ::-webkit-scrollbar-track {
            background: #1a1a2e;
        }
        ::-webkit-scrollbar-thumb {
            background: #4a4a6a;
            border-radius: 4px;
        }
        ::-webkit-scrollbar-thumb:hover {
            background: #5a5a7a;
        }
        </style>
    """, unsafe_allow_html=True)
else:
    st.markdown("""
        <style>
        /* Light mode styles */
        .stApp {
            background-color: #f0f4f8;
        }
        .stChatMessage {
            background-color: #ffffff !important;
        }
        .stTextInput > div > div > input {
            background-color: #ffffff !important;
        }
        .stButton > button {
            background-color: #1a2a6c !important;
            color: white !important;
        }
        .stButton > button:hover {
            background-color: #2a3a8c !important;
        }
        .stRadio > div {
            background-color: #f8f9fa !important;
            border-radius: 10px;
            padding: 10px;
        }
        </style>
    """, unsafe_allow_html=True)

# ===== MAIN APP =====
st.title("⚖️ Legal & 🌿 Wellness AI Assistant")
st.caption("Your emotionally intelligent assistant" + (" 🌙" if st.session_state.theme == "dark" else " ☀️"))

# Mode selection
mode = st.radio(
    "Select Mode",
    ["⚖️ Legal", "🌿 Wellness"],
    horizontal=True,
)

# Initialize session state for messages
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "Hello! I'm your AI companion. Ask me about legal terms or wellness tips. 🌟"}
    ]

# Display chat history
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])

# User input
if prompt := st.chat_input("Type your message..."):
    # Add user message
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.write(prompt)
    
    # System prompt based on mode
    if mode == "⚖️ Legal":
        system_prompt = """You are a Legal Information Assistant. 
Only answer questions about legal topics (contracts, IP, courts, laws, etc.).
If the user asks about health or wellness, say: I'm in Legal Mode. Please switch to Wellness Mode.
Always add: For professional legal advice, consult an attorney."""
    else:
        system_prompt = """You are a Wellness Information Assistant.
Only answer questions about wellness, mental health, stress, anxiety, sleep, etc.
If the user asks about legal topics, say: I'm in Wellness Mode. Please switch to Legal Mode.
Always add: For professional health advice, consult a doctor."""
    
    # Get response
    with st.chat_message("assistant"):
        try:
            response = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[
                    {"role": "system", "content": system_prompt},
                ] + st.session_state.messages,
                temperature=0.3,
                max_tokens=300,
            )
            reply = response.choices[0].message.content
            st.write(reply)
            st.session_state.messages.append({"role": "assistant", "content": reply})
        except Exception as e:
            st.error(f"Error: {e}")

# ===== FOOTER =====
st.markdown("---")
st.caption("Powered by Groq API & Llama 3.3 | Built with Streamlit")