import os.path
import base64
from email.message import EmailMessage
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

# If modifying these scopes, delete the file token.json.
SCOPES = ['https://www.googleapis.com/auth/gmail.modify']

def get_gmail_service():
    creds = None
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=8080)
        # Save the credentials for the next run
        with open('token.json', 'w') as token:
            token.write(creds.to_json())

    service = build('gmail', 'v1', credentials=creds)
    return service

def fetch_recent_emails(limit=5):
    """
    Fetches the last N unread emails and returns them as a list of dictionaries.
    """
    service = get_gmail_service()

    # Get last 5 messages
    results = service.users().messages().list(userId='me', maxResults=limit, q='is:unread').execute()
    messages = results.get('messages', [])

    if not messages:
        print('No new messages found.')
        return []
    
    email_list = []
    
    for message in messages:
        msg = service.users().messages().get(userId='me', id=message['id']).execute()
        headers = msg['payload']['headers']
        subject = next((h['value'] for h in headers if h['name'] == 'Subject'), "No Subject")
        sender = next((h['value'] for h in headers if h['name'] == 'From'), "Unknown")
        snippet = msg.get('snippet', '')
        
        email_list.append({
            "id": message['id'],
            "sender": sender,
            "subject": subject,
            "body": snippet
        })
    return email_list

def create_draft(to_email, original_subject, body_text):
    """
    Creates a dradt email in the user's Gmail account.
    """
    try:
        service = get_gmail_service()
        message = EmailMessage()
        message.set_content(body_text)
        message['To'] - to_email

        if not original_subject.lower().starswith('re:'):
            message['Subject'] = f"Re: {original_subject}"
        else:
            message['Subject'] = original_subject

        encoded_message = base64.urlsafe_b64decode(message.as_bytes()).decode()
        create_message = {'message': {'raw': encoded_message}}

        #create the draft
        draft = service.users().drafts().create(userId='me', body=create_message).execute()
        print(f"Draft created, Draft ID: {draft['id']}")
        return draft
    
    except Exception as e:
        print("Error creating draft: {e}")
        return None

if __name__ == '__main__':
    fetch_recent_emails()