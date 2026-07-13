import streamlit as st
from groq import Groq
import os
from dotenv import load_dotenv
import io
from datetime import datetime
import re  # Add this for emoji removal

# ===== PDF EXPORT LIBRARY =====
try:
    from fpdf import FPDF
    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False

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
if "theme" not in st.session_state:
    st.session_state.theme = "light"

def toggle_theme():
    st.session_state.theme = "dark" if st.session_state.theme == "light" else "light"

# ===== EXPORT FUNCTIONS =====
def get_chat_text():
    """Get formatted chat text"""
    lines = []
    lines.append("=" * 50)
    lines.append("Legal & Wellness AI - Chat Export")
    lines.append(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append("=" * 50)
    lines.append("")
    
    for msg in st.session_state.messages:
        role = "User" if msg["role"] == "user" else "Assistant"
        lines.append(f"{role}: {msg['content']}")
        lines.append("-" * 40)
    
    lines.append("")
    lines.append("=" * 50)
    lines.append("End of conversation")
    lines.append("For professional advice, consult a licensed professional.")
    
    return "\n".join(lines)

def remove_emojis(text):
    """Remove emojis and special characters for PDF export"""
    emoji_pattern = re.compile(
        "["
        u"\U0001F600-\U0001F64F"  # emoticons
        u"\U0001F300-\U0001F5FF"  # symbols & pictographs
        u"\U0001F680-\U0001F6FF"  # transport & map symbols
        u"\U0001F1E0-\U0001F1FF"  # flags
        u"\U00002702-\U000027B0"
        u"\U000024C2-\U0001F251"
        u"\U0001F900-\U0001F9FF"  # supplemental symbols
        u"\U0001FA70-\U0001FAFF"  # symbols extended-a
        "]+",
        flags=re.UNICODE
    )
    return emoji_pattern.sub(r'', text).strip()

def export_chat_text():
    """Export chat as text file"""
    content = get_chat_text()
    filename = f"chat_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    
    st.download_button(
        label="Download Text File",
        data=content,
        file_name=filename,
        mime="text/plain",
        use_container_width=True,
        key="download_text"
    )

def export_chat_pdf():
    """Export chat as PDF with emoji support"""
    if not PDF_AVAILABLE:
        st.error("PDF export requires fpdf. Install: pip install fpdf")
        return
    
    try:
        pdf = FPDF()
        pdf.add_page()
        
        # Title
        pdf.set_font("Arial", "B", 16)
        pdf.cell(0, 10, "Legal & Wellness AI - Chat Export", ln=True, align="C")
        
        pdf.set_font("Arial", "I", 10)
        pdf.cell(0, 10, f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", ln=True, align="C")
        pdf.ln(10)
        
        # Add messages (cleaned of emojis)
        for msg in st.session_state.messages:
            role = "User" if msg["role"] == "user" else "Assistant"
            clean_content = remove_emojis(msg["content"])
            
            pdf.set_font("Arial", "B", 11)
            pdf.cell(0, 8, f"{role}:", ln=True)
            pdf.set_font("Arial", "", 10)
            
            # Split long messages
            if len(clean_content) > 80:
                pdf.multi_cell(0, 6, clean_content)
            else:
                pdf.cell(0, 6, clean_content, ln=True)
            pdf.ln(4)
        
        # Footer
        pdf.set_y(-20)
        pdf.set_font("Arial", "I", 8)
        pdf.cell(0, 10, "For professional advice, consult a licensed professional.", ln=True, align="C")
        
        # Generate PDF bytes
        pdf_output = pdf.output(dest='S')
        
        # Encode properly for download
        if isinstance(pdf_output, str):
            pdf_output = pdf_output.encode('latin-1', errors='ignore')
        
        filename = f"chat_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        
        st.download_button(
            label="Download PDF",
            data=pdf_output,
            file_name=filename,
            mime="application/pdf",
            use_container_width=True,
            key="download_pdf"
        )
        
    except Exception as e:
        st.error(f"Error generating PDF: {e}")

def export_chat_json():
    """Export chat as JSON"""
    import json
    
    data = {
        "export_date": datetime.now().isoformat(),
        "messages": st.session_state.messages
    }
    
    json_str = json.dumps(data, indent=2, ensure_ascii=False)
    filename = f"chat_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    
    st.download_button(
        label="Download JSON",
        data=json_str,
        file_name=filename,
        mime="application/json",
        use_container_width=True,
        key="download_json"
    )

# ===== SIDEBAR =====
with st.sidebar:
    st.markdown("## Settings")
    if st.button("🌙" if st.session_state.theme == "light" else "☀️", help="Toggle Dark Mode"):
        toggle_theme()
        st.rerun()
    
    st.markdown("---")
    
    st.markdown("## Export Chat")
    
    if "messages" in st.session_state and len(st.session_state.messages) > 1:
        if st.button("Download as Text", use_container_width=True):
            export_chat_text()
        
        if st.button("Download as PDF", use_container_width=True):
            export_chat_pdf()
        
        if st.button("Download as JSON", use_container_width=True):
            export_chat_json()
    else:
        st.info("Start a conversation to enable export")
    
    st.markdown("---")
    st.markdown("### About")
    st.markdown("Legal & Wellness AI Assistant powered by Groq API")

# ===== CUSTOM CSS =====
if st.session_state.theme == "dark":
    st.markdown("""
        <style>
        .stApp { background-color: #1a1a2e; }
        .stApp header { background-color: #16213e; }
        .stChatMessage { background-color: #2a2a4a !important; }
        .stChatMessage div[data-testid="stChatMessage"] { background-color: #2a2a4a !important; color: #e0e0e0 !important; }
        .stChatMessage .stMarkdown { color: #e0e0e0 !important; }
        .stTextInput > div > div > input { background-color: #2a2a4a !important; color: #e0e0e0 !important; border-color: #4a4a6a !important; }
        .stButton > button { background-color: #4a6fa5 !important; color: white !important; }
        .stButton > button:hover { background-color: #5a7fb5 !important; }
        .stRadio > div { background-color: #2a2a4a !important; color: #e0e0e0 !important; border-radius: 10px; padding: 10px; }
        .stRadio label { color: #e0e0e0 !important; }
        .stMarkdown h1, .stMarkdown h2, .stMarkdown h3 { color: #e0e0e0 !important; }
        .stMarkdown p { color: #d0d0d0 !important; }
        .element-container { color: #e0e0e0 !important; }
        ::-webkit-scrollbar { width: 8px; }
        ::-webkit-scrollbar-track { background: #1a1a2e; }
        ::-webkit-scrollbar-thumb { background: #4a4a6a; border-radius: 4px; }
        ::-webkit-scrollbar-thumb:hover { background: #5a5a7a; }
        </style>
    """, unsafe_allow_html=True)
else:
    st.markdown("""
        <style>
        .stApp { background-color: #f0f4f8; }
        .stChatMessage { background-color: #ffffff !important; }
        .stTextInput > div > div > input { background-color: #ffffff !important; }
        .stButton > button { background-color: #1a2a6c !important; color: white !important; }
        .stButton > button:hover { background-color: #2a3a8c !important; }
        .stRadio > div { background-color: #f8f9fa !important; border-radius: 10px; padding: 10px; }
        </style>
    """, unsafe_allow_html=True)

# ===== MAIN APP =====
st.title("⚖️ Legal & 🌿 Wellness AI Assistant")
st.caption("Your emotionally intelligent assistant" + (" 🌙" if st.session_state.theme == "dark" else " ☀️"))

mode = st.radio(
    "Select Mode",
    ["⚖️ Legal", "🌿 Wellness"],
    horizontal=True,
)

if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "Hello! I'm your AI companion. Ask me about legal terms or wellness tips. 🌟"}
    ]

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])

col1, col2 = st.columns([5, 1])
with col2:
    if st.button("🗑️ Clear Chat"):
        st.session_state.messages = [
            {"role": "assistant", "content": "Chat cleared! Start a new conversation. 🌟"}
        ]
        st.rerun()

if prompt := st.chat_input("Type your message..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.write(prompt)
    
    if mode == "⚖️ Legal":
        system_prompt = """You are a Legal Information Assistant. 
Only answer questions about legal topics.
Always add: For professional legal advice, consult an attorney."""
    else:
        system_prompt = """You are a Wellness Information Assistant.
Only answer questions about wellness.
Always add: For professional health advice, consult a doctor."""
    
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

st.markdown("---")
st.caption("Powered by Groq API & Llama 3.3 | Built with Streamlit")