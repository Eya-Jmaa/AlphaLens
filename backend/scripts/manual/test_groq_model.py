"""Test Groq Model"""
import os

from dotenv import load_dotenv
from langchain_groq import ChatGroq

load_dotenv()

api_key = os.getenv("GROQ_API_KEY")
model = os.getenv("GROQ_MODEL", "openai/gpt-oss-120b")

print(f"Testing model: {model}")
print(f"API Key: {api_key[:10]}...")

try:
    llm = ChatGroq(
        groq_api_key=api_key,
        model_name=model,
        temperature=0.3,
        max_tokens=100,
        timeout=30,
    )
    response = llm.invoke("Say 'Hello, World!' in 3 words")
    print(f"✅ Model working! Response: {response.content}")
except Exception as e:
    print(f"❌ Model failed: {e}")