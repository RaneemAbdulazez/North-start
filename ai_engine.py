import google.generativeai as genai
import os
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv("GOOGLE_API_KEY")

if api_key:
    try: genai.configure(api_key=api_key)
    except: pass

def analyze_performance(sessions_data):
    if not api_key: return "⚠️ AI Key Missing"
    
    model = genai.GenerativeModel('gemini-2.5-flash')
    prompt = f"""
    Analyze my work sessions today: {sessions_data}.
    Am I distracted? Lazy? Or productive?
    Give me 1 sentence feedback.
    """
    try:
        response = model.generate_content(prompt)
        return response.text
    except: return "AI Sleeping..."

def ask_coach(user_query, context):
    if not api_key: return "⚠️ AI Key Missing"
    
    model = genai.GenerativeModel('gemini-2.5-flash')
    prompt = f"""
    Context: {context}
    
    User: {user_query}
    
    Act as a world-class productivity coach (NorthStar OS). 
    Be concise, motivating, and data-driven.
    """
    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e: return f"AI Error: {e}"