from fastapi import FastAPI
from src.tools.gmail_client import fetch_recent_emails, create_draft, send_email_to_self, archive_message, trash_message
from src.core.brain import analyze_email, generate_digest 
from src.core.memory import init_db, is_email_processed, log_email, schedule_for_trash, get_emails_ready_to_trash, remove_from_scheduled_trash
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
        #1. check id there are emails that are expired
        ready_to_trash = get_emails_ready_to_trash()
        if ready_to_trash:
            print(f"Found {len(ready_to_trash)} expired mails. Trashing now...")
            for t_id in ready_to_trash:
                trash_message(t_id)
                remove_from_scheduled_trash(t_id)
        #2. fetch new emails
        raw_emails = fetch_recent_emails(limit=5)
        
        if not raw_emails:
            return {"message": "No new emails found."}

        final_results = [] 
        digest_collection = []
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
                category = analysis.get("category", "")
                suggested_action = analysis.get("suggested_action", "")
                draft_content = analysis.get("draft_reply")
                summary = analysis.get("summary", "")

                if suggested_action == "Reply" and draft_content:
                    print(f"Auto-drafting reply to {email['sender']}...")
                    create_draft(email['sender'], email['subject'], draft_content)
                    action_taken = "Draft Created"
                elif suggested_action == "Digest" or category in ["Newsletter", "Informational", "Finance"]:
                    print(f"Adding to Daily Digest: {email['subject']}")
                    digest_collection.append({
                        "sender": email['sender'],
                        "subject": email['subject'],
                        "summary": summary
                    })
                    action_taken = "Added to Digest"
                elif suggested_action == "Archive":
                    print(f"Archiving clutter: {email['subject']}")
                    archive_message(email['id'])
                    action_taken="Archived"
                elif suggested_action == "Trash":
                    if category == "OTP":
                        print(f"OTP detected: Scheduling '{email['subject']}' to be trashed later")
                        schedule_for_trash(email['id'], delay_minute=1)
                        action_taken = "Schedule for Trash"
                    else:
                        print(f"Trashing useless email: {email['subject']}")
                        trash_message(email['id'])
                        action_taken = "Trashed"


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

        if digest_collection:
            print(f"Generating Daily Digest from {len(digest_collection)} emails...")
            digest_body = generate_digest(digest_collection)

            if digest_body:
                send_email_to_self("Your Daily Digest is here", digest_body)

        return {"analyzed_count": len(final_results), "skipper_count": skipped_count, "emails": final_results}

    except Exception as e:
        print("CRITICAL ERROR:")
        traceback.print_exc()
        return {"error": str(e)}