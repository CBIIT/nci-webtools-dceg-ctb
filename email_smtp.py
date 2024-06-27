import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import os
from dotenv import load_dotenv

load_dotenv()
EMAIL_SERVICE_USERNAME = os.getenv('EMAIL_SERVICE_USERNAME', '')
EMAIL_SERVICE_PASSWORD = os.getenv('EMAIL_SERVICE_PASSWORD', '')
# Replace with your own credentials
SMTP_SERVER = "email-smtp.us-east-1.amazonaws.com"  # Your SMTP server (region-specific)
SMTP_PORT = 587 # TLS port
SMTP_USERNAME = EMAIL_SERVICE_USERNAME
SMTP_PASSWORD = EMAIL_SERVICE_PASSWORD
FROM_EMAIL = "nciwebtools@gmail.com"
TO_EMAIL = "xiaozheng.yao@nih.gov"
SUBJECT = "Test Email"
BODY_TEXT = "This is a test email sent using AWS SES SMTP interface."

# Create the email message
msg = MIMEMultipart()
msg['From'] = FROM_EMAIL
msg['To'] = TO_EMAIL
msg['Subject'] = SUBJECT
msg.attach(MIMEText(BODY_TEXT, 'plain'))

# Send the email
try:
    server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
    server.starttls()
    print("smtp start")
    server.login(SMTP_USERNAME, SMTP_PASSWORD)
    print("smtp login")
    server.sendmail(FROM_EMAIL, TO_EMAIL, msg.as_string())
    server.close()
    print("Email sent successfully!")
except Exception as e:
    print(f"Error: {e}")