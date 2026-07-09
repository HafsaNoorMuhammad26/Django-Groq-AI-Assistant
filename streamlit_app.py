import streamlit as st
from groq import Groq

# Load API key from Streamlit secrets
client = Groq(api_key=st.secrets["GROQ_API_KEY"])

st.set_page_config(page_title="Legal & Wellness AI", page_icon="⚖️")
st.title("⚖️ Legal & 🌿 Wellness AI Assistant")

# Mode selection
mode = st.radio("Select Mode", ["⚖️ Legal", "🌿 Wellness"])

# Chat history
if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "assistant", "content": "Hello! I'm your AI companion. Ask me about legal terms or wellness tips."}]

# Display chat
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])

# User input
if prompt := st.chat_input("Type your message..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.write(prompt)
    
    system_prompt = "You are a Legal Assistant." if mode == "⚖️ Legal" else "You are a Wellness Assistant."
    
    with st.chat_message("assistant"):
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "system", "content": system_prompt}] + st.session_state.messages
        )
        reply = response.choices[0].message.content
        st.write(reply)
        st.session_state.messages.append({"role": "assistant", "content": reply})