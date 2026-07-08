from groq import Groq

client = Groq(api_key="GROQ_API_KEY")  # Keep your key

response = client.chat.completions.create(
    model="llama-3.3-70b-versatile",  # ✅ Current model
    messages=[
        {"role": "system", "content": "You are a legal assistant."},
        {"role": "user", "content": "What is a contract?"}
    ],
    temperature=0.3
)

print(response.choices[0].message.content)