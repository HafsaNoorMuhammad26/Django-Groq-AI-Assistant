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

st.set_page_config(page_title="Legal & Wellness AI", page_icon="⚖️")

# Custom CSS for better UI
st.markdown("""
    <style>
    .stApp {
        max-width: 800px;
        margin: 0 auto;
    }
    .stRadio > div {
        gap: 20px;
    }
    </style>
""", unsafe_allow_html=True)

st.title("⚖️ Legal & 🌿 Wellness AI Assistant")

# Mode selection
mode = st.radio(
    "Select Mode",
    ["⚖️ Legal", "🌿 Wellness"],
    horizontal=True,
)

# Initialize session state
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