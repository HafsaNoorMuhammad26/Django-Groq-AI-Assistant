import streamlit as st
from groq import Groq
import os
from dotenv import load_dotenv
import io
from datetime import datetime
import json
import re
import PyPDF2
from io import BytesIO

# ===== LOAD ENVIRONMENT =====
load_dotenv()

# ===== INITIALIZE GROQ CLIENT =====
try:
    GROQ_API_KEY = st.secrets["GROQ_API_KEY"]
except:
    GROQ_API_KEY = os.getenv("GROQ_API_KEY")

if not GROQ_API_KEY:
    st.error("❌ GROQ_API_KEY not found! Please add it to .env or secrets.toml")
    st.stop()

# ✅ THIS IS THE FIX - Initialize the client
client = Groq(api_key=GROQ_API_KEY)

# ===== PAGE CONFIG =====
st.set_page_config(
    page_title="Legal & Wellness AI",
    page_icon="⚖️",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# ===== DARK MODE =====
if "theme" not in st.session_state:
    st.session_state.theme = "light"

def toggle_theme():
    st.session_state.theme = "dark" if st.session_state.theme == "light" else "light"

# ===== REMOVE EMOJIS =====
def remove_emojis(text):
    emoji_pattern = re.compile(
        "["
        u"\U0001F600-\U0001F64F"
        u"\U0001F300-\U0001F5FF"
        u"\U0001F680-\U0001F6FF"
        u"\U0001F1E0-\U0001F1FF"
        u"\U00002702-\U000027B0"
        u"\U000024C2-\U0001F251"
        u"\U0001F900-\U0001F9FF"
        u"\U0001FA70-\U0001FAFF"
        "]+",
        flags=re.UNICODE
    )
    return emoji_pattern.sub(r'', text).strip()

# ===== EXPORT FUNCTIONS =====
def get_chat_text():
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

def export_chat_text():
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
    try:
        from reportlab.lib.pagesizes import letter
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import inch
        from reportlab.lib.enums import TA_CENTER, TA_LEFT
        from reportlab.lib import colors
        
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=letter,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=72,
        )
        
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle('CustomTitle', parent=styles['Heading1'], fontSize=18, alignment=TA_CENTER, spaceAfter=20)
        header_style = ParagraphStyle('CustomHeader', parent=styles['Heading2'], fontSize=13, alignment=TA_LEFT, spaceAfter=6, textColor=colors.HexColor('#1a2a6c'))
        body_style = ParagraphStyle('CustomBody', parent=styles['Normal'], fontSize=11, alignment=TA_LEFT, spaceAfter=10, leftIndent=10)
        date_style = ParagraphStyle('CustomDate', parent=styles['Normal'], fontSize=10, alignment=TA_CENTER, textColor=colors.HexColor('#666666'), spaceAfter=20)
        footer_style = ParagraphStyle('CustomFooter', parent=styles['Normal'], fontSize=9, alignment=TA_CENTER, textColor=colors.HexColor('#999999'), spaceAfter=6)
        
        content = []
        content.append(Paragraph("Legal & Wellness AI - Chat Export", title_style))
        content.append(Spacer(1, 0.1 * inch))
        
        date_str = datetime.now().strftime('%Y-%m-%d %I:%M %p')
        content.append(Paragraph(f"Exported on: {date_str}", date_style))
        content.append(Spacer(1, 0.2 * inch))
        
        for msg in st.session_state.messages:
            role = "User" if msg["role"] == "user" else "Assistant"
            icon = "User" if msg["role"] == "user" else "Assistant"
            content.append(Paragraph(f"{icon}:", header_style))
            clean_content = remove_emojis(msg['content'])
            content.append(Paragraph(clean_content, body_style))
            content.append(Spacer(1, 0.1 * inch))
        
        content.append(Spacer(1, 0.3 * inch))
        content.append(Paragraph("=" * 60, footer_style))
        content.append(Paragraph("For professional advice, consult a licensed professional.", footer_style))
        content.append(Paragraph(f"Total messages: {len(st.session_state.messages)}", footer_style))
        
        doc.build(content)
        
        pdf_data = buffer.getvalue()
        buffer.close()
        
        filename = f"chat_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        st.download_button(
            label="Download PDF",
            data=pdf_data,
            file_name=filename,
            mime="application/pdf",
            use_container_width=True,
            key="download_pdf"
        )
    except Exception as e:
        st.error(f"PDF export error: {e}")

def export_chat_json():
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
    st.markdown("## ⚙️ Settings")
    if st.button("🌙" if st.session_state.theme == "light" else "☀️", help="Toggle Dark Mode"):
        toggle_theme()
        st.rerun()
    
    st.markdown("---")
    st.markdown("## 📥 Export Chat")
    
    if "messages" in st.session_state and len(st.session_state.messages) > 1:
        if st.button("📄 Download as Text", use_container_width=True):
            export_chat_text()
        if st.button("📕 Download as PDF", use_container_width=True):
            export_chat_pdf()
        if st.button("📊 Download as JSON", use_container_width=True):
            export_chat_json()
    else:
        st.info("💬 Start a conversation to enable export")
    
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

# ===== PDF UPLOAD SECTION =====
st.markdown("---")
st.markdown("## 📄 Upload PDF for Legal Analysis")

uploaded_file = st.file_uploader(
    "Upload a legal document (PDF)",
    type=['pdf'],
    help="Upload contracts, agreements, or legal documents for AI analysis"
)

if uploaded_file is not None:
    try:
        pdf_reader = PyPDF2.PdfReader(BytesIO(uploaded_file.read()))
        text = ""
        for page in pdf_reader.pages:
            text += page.extract_text() + "\n"
        
        if not text:
            st.error("Could not extract text from PDF. Please ensure it contains readable text.")
        else:
            with st.expander("📄 Document Preview"):
                st.text(text[:1000] + ("..." if len(text) > 1000 else ""))
            
            if st.button("🔍 Analyze Document", use_container_width=True):
                with st.spinner("Analyzing document... This may take a moment."):
                    analysis_prompt = f"""
                    You are a Legal Document Analyst. Analyze the following legal document and provide:
                    
                    1. **Document Summary** (2-3 sentences)
                    2. **Key Clauses** (list the most important clauses)
                    3. **Potential Issues** (any concerning clauses or ambiguities)
                    4. **Plain English Explanation** (explain the document in simple terms)
                    
                    Document:
                    {text[:8000]}
                    """
                    
                    # ✅ client is now defined!
                    response = client.chat.completions.create(
                        model="llama-3.3-70b-versatile",
                        messages=[
                            {"role": "system", "content": "You are a Legal Document Analyst. Provide structured analysis."},
                            {"role": "user", "content": analysis_prompt}
                        ],
                        temperature=0.3,
                        max_tokens=800,
                    )
                    
                    analysis = response.choices[0].message.content
                    
                    st.markdown("### 📋 Analysis Result")
                    st.markdown(analysis)
                    
                    st.download_button(
                        label="📥 Download Analysis",
                        data=analysis,
                        file_name=f"analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                        mime="text/plain",
                        use_container_width=True
                    )
                    
    except Exception as e:
        st.error(f"Error reading PDF: {e}")

# ===== CHAT INPUT =====
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