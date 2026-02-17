from fastapi import FastAPI
from src.tools.gmail_client import fetch_recent_emails
from src.core.brain import analyze_email 
import traceback

app = FastAPI()

@app.get("/")
def home():
    return {"status": "Inbox Sentinel Agent is Active"}

@app.get("/scan")
def scan_inbox():
    print("Starting Inbox Scan...") 
    
    try:
        # 1. Get raw emails
        raw_emails = fetch_recent_emails(limit=5)
        
        if not raw_emails:
            return {"message": "No new emails found."}

        final_results = [] 
        
        
        for email in raw_emails:
            print(f"Analyzing: {email['subject']}...") 
            
            # <--- THIS IS THE FUNCTION CALL (Singular)
            analysis = analyze_email(email['sender'], email['subject'], email['body'])
            
            if analysis:
                full_data = {
                    "id": email['id'],
                    "sender": email['sender'],
                    "subject": email['subject'],
                    "ai_analysis": analysis
                }
                final_results.append(full_data) 
            else:
                print("Skipping email due to analysis failure.")

        return {"analyzed_count": len(final_results), "emails": final_results}

    except Exception as e:
        print("CRITICAL ERROR:")
        traceback.print_exc()
        return {"error": str(e)}