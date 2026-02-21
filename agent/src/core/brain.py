import os
import json
import google.generativeai as genai
from dotenv import load_dotenv
from groq import Groq

# Load the API key from the .env file
load_dotenv()
api_key = os.getenv("GROQ_API_KEY")

if not api_key:
    raise ValueError("No GROQ_API_KEY found in .env file!")

client = Groq(api_key=api_key)

def analyze_email(sender, subject, body):
    """
    Sends the email content to Deepseek to determine urgency and next steps.
    """
    
    prompt = f"""
    You are an executive assistant named 'Inbox Sentinel'. 
    Analyze the following incoming email and return a strictly valid JSON object.
    
    Sender: {sender}
    Subject: {subject}
    Body: {body}
    
    Output JSON format:
    {{
        "category": "Work" | "Personal" | "Spam" | "Newsletter" | "Finance",
        "urgency_score": (integer 1-10, where 10 is immediate crisis),
        "is_actionable": (boolean),
        "summary": (string, max 15 words),
        "suggested_action": "Archive" | "Reply" | "Mark as Read" | "Flag",
        "draft_reply": (string, null if no reply needed. Be professional and concise.)
    }}
    
    Return ONLY the JSON. No markdown formatting.
    """
    
    try:
        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": "You are a helpful executive assistant designed to output strict JSON."},
                {"role": "user", "content": prompt}
            ]
        )
        json_content = response.choices[0].message.content
        return json.loads(json_content)
    except Exception as e:
        print(f"Error analyzing email: {e}")
        return None

# --- TEST AREA ---
if __name__ == "__main__":
    # Let's fake an email to test the brain
    fake_sender = "boss@company.com"
    fake_subject = "URGENT: Server Down"
    fake_body = "The production server is on fire. Fix it now or you're fired."
    
    print("Thinking...")
    analysis = analyze_email(fake_sender, fake_subject, fake_body)
    
    import pprint
    pprint.pprint(analysis)