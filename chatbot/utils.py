import os
from groq import Groq
from dotenv import load_dotenv
import google.genai as genai

# Load environment variables
load_dotenv()

# Initialize Groq client
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
client = Groq(api_key=GROQ_API_KEY)

# Initialize Gemini (Google AI)
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
if GOOGLE_API_KEY:
    genai_client = genai.Client(api_key=GOOGLE_API_KEY)  # ✅ New way
    gemini_model = "gemini-1.5-flash"  # ✅ New model name
else:
    genai_client = None
    gemini_model = None
    print("⚠️ GOOGLE_API_KEY not found. Gemini features disabled.")

# System prompts for different modes
SYSTEM_PROMPTS = {
    "legal": """You are a Legal Information Assistant.
    - ONLY answer questions about legal topics (contracts, IP, courts, laws, etc.)
    - If the user asks about health, wellness, or non-legal topics, politely say:
      "I'm currently in Legal Mode. Please switch to Wellness Mode for health-related questions."
    - Provide clear, accurate, and concise answers about legal topics
    - Always add: "For professional legal advice, please consult a licensed attorney"
    - Keep responses under 200 words
    - Use simple language""",
    
    "wellness": """You are a Wellness Information Assistant.
    - ONLY answer questions about wellness, mental health, stress, anxiety, sleep, etc.
    - If the user asks about legal topics, politely say:
      "I'm currently in Wellness Mode. Please switch to Legal Mode for legal questions."
    - Provide supportive, practical, and accurate wellness advice
    - Always add: "For professional health advice, please consult a qualified healthcare provider"
    - Keep responses under 200 words
    - Be empathetic and encouraging
    - Offer specific techniques (breathing exercises, mindfulness tips, etc.)"""
}

# Keywords for domain detection
LEGAL_KEYWORDS = [
    'contract', 'law', 'legal', 'attorney', 'lawsuit', 'court', 'judge',
    'patent', 'copyright', 'trademark', 'ip', 'intellectual property',
    'nda', 'non-disclosure', 'force majeure', 'tort', 'negligence',
    'appeal', 'verdict', 'tenant', 'lease', 'property', 'employment',
    'discrimination', 'termination', 'breach', 'consideration', 'civil',
    'criminal', 'liable', 'defendant', 'plaintiff', 'sue', 'suing'
]

WELLNESS_KEYWORDS = [
    'anxiety', 'stress', 'depression', 'sleep', 'insomnia', 'breathing',
    'meditation', 'mindfulness', 'therapy', 'mental health', 'wellness',
    'motivation', 'anger', 'sadness', 'panic', 'relax', 'exercise',
    'nutrition', 'hydration', 'self-care', 'boundaries', 'wellness',
    'mental', 'health', 'feel', 'emotion','headache'
]

def detect_domain(text):
    """Detect if question is legal, wellness, or unknown"""
    text_lower = text.lower()
    
    legal_score = sum(1 for kw in LEGAL_KEYWORDS if kw in text_lower)
    wellness_score = sum(1 for kw in WELLNESS_KEYWORDS if kw in text_lower)
    
    if legal_score > wellness_score and legal_score > 0:
        return "legal"
    elif wellness_score > 0:
        return "wellness"
    else:
        return "unknown"

def generate_response(user_input, mode="legal", chat_history=None):
    """
    Generate response using Groq API with domain enforcement
    """
    # Detect the domain of the user's question
    detected_domain = detect_domain(user_input)
    
    # If user asks about legal in wellness mode OR wellness in legal mode
    if mode == "legal" and detected_domain == "wellness":
        return "🌿 I notice you're asking about wellness. I'm currently in **Legal Mode**. Please click the **Wellness Mode** button above for health-related questions!"
    
    if mode == "wellness" and detected_domain == "legal":
        return "⚖️ I notice you're asking about legal topics. I'm currently in **Wellness Mode**. Please click the **Legal Mode** button above for legal questions!"
    
    # If domain is unknown, politely ask for clarification
    if detected_domain == "unknown":
        return "🤔 I'm not sure if that's a legal or wellness question. Could you please clarify? Or switch to the appropriate mode using the buttons above."
    
    # Get the system prompt for the selected mode
    system_prompt = SYSTEM_PROMPTS.get(mode, SYSTEM_PROMPTS["legal"])
    
    # Build the messages list
    messages = [
        {"role": "system", "content": system_prompt}
    ]
    
    # Add chat history for context (if available)
    if chat_history:
        for msg in chat_history[-5:]:  # Last 5 exchanges
            messages.append({"role": "user", "content": msg["user"]})
            messages.append({"role": "assistant", "content": msg["bot"]})
    
    # Add the current user message
    messages.append({"role": "user", "content": user_input})
    
    try:
        # Call Groq API
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=messages,
            temperature=0.3,
            max_tokens=300,
        )
        
        return response.choices[0].message.content
        
    except Exception as e:
        return f"⚠️ Error: {str(e)}. Please try again."

# ===== GEMINI (GOOGLE AI) SENTIMENT ANALYSIS =====
def get_sentiment_with_gemini(text):
    """
    Analyze sentiment using Google Gemini AI
    Returns: (sentiment_label, confidence_score)
    """
    if not gemini_model:
        return "NEUTRAL", 0.5
    
    try:
        # Prompt for Gemini
        prompt = f"""
        Analyze the sentiment of this message and return ONLY a JSON response.
        Message: "{text}"
        
        Return format:
        {{
            "sentiment": "POSITIVE" or "NEGATIVE" or "NEUTRAL",
            "confidence": 0.0 to 1.0
        }}
        """
        
        response = gemini_model.generate_content(prompt)
        
        # Parse the response
        import json
        import re
        
        # Extract JSON from response
        json_match = re.search(r'\{.*\}', response.text, re.DOTALL)
        if json_match:
            data = json.loads(json_match.group())
            sentiment = data.get("sentiment", "NEUTRAL")
            confidence = data.get("confidence", 0.5)
            return sentiment, confidence
        
        return "NEUTRAL", 0.5
        
    except Exception as e:
        print(f"Gemini sentiment error: {e}")
        return "NEUTRAL", 0.5

# ===== UPDATED get_sentiment FUNCTION =====
def get_sentiment(text):
    """
    Get sentiment using Gemini AI (fallback to neutral if unavailable)
    """
    if gemini_model:
        return get_sentiment_with_gemini(text)
    return "NEUTRAL", 0.5