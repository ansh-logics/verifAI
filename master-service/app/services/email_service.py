import os
import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from app.database.models import Student

logger = logging.getLogger(__name__)

class EmailService:
    def __init__(self):
        self.gmail_user = os.getenv("GMAIL_USER")
        self.gmail_password = os.getenv("GMAIL_APP_PASSWORD")
        self.smtp_server = "smtp.gmail.com"
        self.smtp_port = 587

    def send_single_email(self, student: Student, subject: str = None, body: str = None) -> bool:
        """Sends an email to student.email."""
        if not self.gmail_user or not self.gmail_password:
            logger.error("GMAIL credentials not configured in environment.")
            return False

        recipient_email = student.email

        if not recipient_email:
            logger.error("No email address found for student ID %s", student.id)
            return False

        if not subject:
            subject = f"Hello {student.name} from VerifAI"
        if not body:
            body = (
                f"Hi {student.name},\n\n"
                f"You have been shortlisted for the VIZ AI internship opportunity.\n\n"
                f"Please log in to VerifAI portal for next steps.\n\n"
                f"Regards,\n"
                f"VerifAI Team"
            )

        try:
            msg = MIMEMultipart()
            msg['From'] = self.gmail_user
            msg['To'] = recipient_email
            msg['Subject'] = subject
            msg.attach(MIMEText(body, 'plain'))

            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.gmail_user, self.gmail_password)
                server.send_message(msg)
            
            logger.info("Sent email to %s (%s)", student.name, recipient_email)
            return True
        except Exception as e:
            logger.exception("Failed to send email to %s", recipient_email)
            return False
