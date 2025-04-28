import os
from dotenv import load_dotenv
from helpers.email_helper import send_email

# Load environment variables
load_dotenv()

# Test email
send_email(
    recipient=os.getenv("RECIPIENT_EMAIL"),
    subject="Test Email from Agent Garden 🌱",
    body="Hello Ryan,\n\nThis is a test email from Aurora's communication system.\n\n- The Garden"
)
