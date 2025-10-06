# core/cold_mailer.py

import os
import base64
from email.mime.text import MIMEText
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# --- Configuration ---
# If modifying these SCOPES, delete the file token.json.
SCOPES = ["https://www.googleapis.com/auth/gmail.send"]

def get_gmail_service():
    """
    Authenticates with the Gmail API and returns a service object.
    Handles the OAuth 2.0 flow.
    """
    creds = None
    # The file token.json stores the user's access and refresh tokens.
    # It's created automatically when the authorization flow completes for the first time.
    if os.path.exists("token.json"):
        creds = Credentials.from_authorized_user_file("token.json", SCOPES)

    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            # IMPORTANT: Your credentials.json file must be in the root directory
            flow = InstalledAppFlow.from_client_secrets_file("credentials.json", SCOPES)
            creds = flow.run_local_server(port=0)
        
        # Save the credentials for the next run
        with open("token.json", "w") as token:
            token.write(creds.to_json())

    return build("gmail", "v1", credentials=creds)

def create_message(sender, to, subject, message_text):
    """Create a message for an email."""
    message = MIMEText(message_text)
    message["to"] = to
    message["from"] = sender
    message["subject"] = subject
    # Encode the message in base64url format
    return {"raw": base64.urlsafe_b64encode(message.as_bytes()).decode()}

def send_email_api(recipient_email, subject, body):
    """
    Uses the Gmail API to send an email.
    """
    try:
        service = get_gmail_service()
        message = create_message("me", recipient_email, subject, body)
        print(message)
        # Call the Gmail API to send the email
        sent_message = service.users().messages().send(userId="me", body=message).execute()
        print(f"Email sent successfully! Message ID: {sent_message['id']}")
        return True
    except HttpError as error:
        print(f"An error occurred: {error}")
        return False
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return False

if __name__ == "__main__":
    # --- Example Usage ---
    # The first time you run this, a browser window will open for you to log in
    # and grant permission. A `token.json` file will be created to remember your login.
    
    test_recipient = "manu.martin.developer@gmail.com"
    test_subject = "Testing the Gmail API"
    test_body = "This is a test email sent from the AI Job Butler using the official Gmail API."
    
    send_email_api(test_recipient, test_subject, test_body)