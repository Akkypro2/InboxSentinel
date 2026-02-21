from fastapi import FastAPI
from src.tools.gmail_client import fetch_recent_emails, create_draft
from src.core.brain import analyze_email 
from src.core.memory import init_db, is_email_processed, log_email
import traceback
import time

app = FastAPI()
init_db()

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
        skipped_count = 0
        
        
        for email in raw_emails:
            if is_email_processed(email['id']):
                print(f"Skipping (Already Processed): {email['subject']}")
                skipped_count += 1
                continue

            print(f"Analyzing new email: {email['subject']}...") 
            
            analysis = analyze_email(email['sender'], email['subject'], email['body'])
            
            if analysis:
                action_taken = "None"
                suggested_action = analysis.get("suggested_action", "")
                draft_content = analysis.get("draft_reply")

                if suggested_action == "Reply" and draft_content:
                    print(f"Auto-drafting reply to {email['sender']}...")
                    create_draft(email['sender'], email['subject'], draft_content)
                    action_taken = "Draft Created"

                full_data = {
                    "id": email['id'],
                    "sender": email['sender'],
                    "subject": email['subject'],
                    "ai_analysis": analysis,
                    "action_taken": action_taken
                }
                final_results.append(full_data)

                log_email(email['id'], email['sender'], email['subject'])
                print(f"Saved to memory: {email['subject']}")
            else:
                print("Skipping email due to analysis failure.")

            time.sleep(3)

        return {"analyzed_count": len(final_results), "skipper_count": skipped_count, "emails": final_results}

    except Exception as e:
        print("CRITICAL ERROR:")
        traceback.print_exc()
        return {"error": str(e)}