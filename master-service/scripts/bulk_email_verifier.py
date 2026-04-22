import os
import time
import uuid
import smtplib
import requests
from typing import List, Dict, Any
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Configuration from environment variables
API_KEY = os.getenv("TESTMAIL_API_KEY", "73dd84d5-f200-4704-a3cd-c4744ab4daba")
NAMESPACE = os.getenv("TESTMAIL_NAMESPACE")
SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", 587))
SMTP_EMAIL = os.getenv("SMTP_EMAIL")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")

# Test settings
EMAIL_COUNT = 100
SUBJECT_PREFIX = "Bulk Verification Test"
WAIT_TIME_SECONDS = 15  # Time to wait for delivery before checking API

def generate_test_addresses(namespace: str, count: int) -> List[str]:
    """
    Generates a list of unique Testmail addresses.
    Format: {namespace}.user{i}@inbox.testmail.app
    Note: Testmail standard format is namespace.tag@inbox.testmail.app
    """
    if not namespace:
        raise ValueError("TESTMAIL_NAMESPACE is not set in environment variables.")
    
    # We use 'inbox.testmail.app' as it's the default for most namespaces
    return [f"{namespace}.user{i}@inbox.testmail.app" for i in range(1, count + 1)]

def send_emails(emails: List[str], batch_id: str):
    """
    Sends 100 emails using SMTP.
    """
    if not SMTP_EMAIL or not SMTP_PASSWORD:
        print("Error: SMTP credentials not provided in .env")
        return

    print(f"[*] Starting to send {len(emails)} emails (Batch ID: {batch_id})...")
    
    try:
        # Connect to SMTP server
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(SMTP_EMAIL, SMTP_PASSWORD)
        
        for i, recipient in enumerate(emails, 1):
            user_id = recipient.split('.')[1].split('@')[0] # extracts 'userX'
            subject = f"{SUBJECT_PREFIX} | {batch_id} | {user_id}"
            body = f"This is a test email for bulk delivery verification.\nBatch: {batch_id}\nUser: {user_id}"
            
            msg = MIMEMultipart()
            msg['From'] = SMTP_EMAIL
            msg['To'] = recipient
            msg['Subject'] = subject
            msg.attach(MIMEText(body, 'plain'))
            
            server.send_message(msg)
            if i % 10 == 0:
                print(f"    - Sent {i}/{len(emails)}...")
        
        server.quit()
        print("[+] All emails sent successfully via SMTP.")
        
    except smtplib.SMTPAuthenticationError:
        print("[-] Authentication failed. Please check your SMTP_EMAIL and SMTP_PASSWORD.")
    except Exception as e:
        print(f"[-] Error sending emails: {e}")

def check_testmail(namespace: str, api_key: str, batch_id: str) -> List[Dict[Any, Any]]:
    """
    Fetches received emails from Testmail API.
    """
    print(f"[*] Waiting {WAIT_TIME_SECONDS} seconds for delivery...")
    time.sleep(WAIT_TIME_SECONDS)
    
    url = f"https://api.testmail.app/api/json?apikey={api_key}&namespace={namespace}&live=true"
    
    try:
        print(f"[*] Fetching emails from Testmail API for namespace: {namespace}...")
        response = requests.get(url, timeout=30)
        
        if response.status_code == 401:
            print("[-] API Failure: Invalid API Key.")
            return []
        
        response.raise_for_status()
        data = response.json()
        
        if data.get('result') == 'fail':
            print(f"[-] API Error: {data.get('message')}")
            return []
            
        emails = data.get('emails', [])
        
        # Filter emails belonging to this batch
        batch_emails = [e for e in emails if batch_id in e.get('subject', '')]
        return batch_emails

    except requests.exceptions.RequestException as e:
        print(f"[-] Network issue or API failure: {e}")
        return []
    except Exception as e:
        print(f"[-] Unexpected error fetching emails: {e}")
        return []

def generate_report(sent_count: int, sent_emails: List[str], received_emails: List[Dict[Any, Any]], batch_id: str):
    """
    Analyzes delivery and prints a summary report.
    """
    received_tags = set()
    duplicates = []
    
    for email in received_emails:
        tag = email.get('tag')
        if tag in received_tags:
            duplicates.append(tag)
        received_tags.add(tag)
    
    # Identify missing tags
    sent_tags = {f"user{i}" for i in range(1, sent_count + 1)}
    missing_tags = sorted(list(sent_tags - received_tags))
    
    total_received = len(received_emails)
    unique_received = len(received_tags)
    
    status = "Success" if unique_received == sent_count else "Partial Success"
    if unique_received == 0:
        status = "Failed"
        
    print("\n" + "="*40)
    print("      DELIVERY SUMMARY REPORT")
    print("="*40)
    print(f"Batch ID:       {batch_id}")
    print(f"Total Sent:     {sent_count}")
    print(f"Total Received: {total_received}")
    print(f"Unique Recv:    {unique_received}")
    print(f"Missing:        {', '.join(missing_tags) if missing_tags else 'None'}")
    print(f"Duplicates:     {', '.join(duplicates) if duplicates else 'None'}")
    print(f"Status:         {status}")
    print("="*40)

def main():
    """
    Main execution flow.
    """
    # 1. Setup
    batch_id = str(uuid.uuid4())[:8] # Short unique ID for this run
    
    try:
        # 2. Generate addresses
        target_emails = generate_test_addresses(NAMESPACE, EMAIL_COUNT)
        
        # 3. Send emails
        send_emails(target_emails, batch_id)
        
        # 4. Verify via API
        received = check_testmail(NAMESPACE, API_KEY, batch_id)
        
        # 5. Report
        generate_report(EMAIL_COUNT, target_emails, received, batch_id)
        
    except ValueError as ve:
        print(f"[-] Configuration Error: {ve}")
    except KeyboardInterrupt:
        print("\n[!] Process interrupted by user.")

if __name__ == "__main__":
    main()
