import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

USER = os.environ.get("SMTP_USER")
PASS = os.environ.get("SMTP_PASSWORD") 

def send_email(subject, body, to_email):
    # Email configuration
    # Requires route settings in Google Workspace 
    smtp_server = "smtp-relay.gmail.com" #"smtp.gmail.com"
    smtp_port = 25 #587  # 465 for SSL
    smtp_user = "shared@thinkxinc.com" if not USER else USER
    smtp_password = "" if not PASS else PASS
    print(f'send mail "{subject}" from {smtp_user} to {to_email}.')

    # Set up the email
    msg = MIMEMultipart()
    msg['From'] = smtp_user
    msg['To'] = to_email
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'plain'))

    # Send the email
    try:
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(smtp_user, smtp_password)
        text = msg.as_string()
        server.sendmail(smtp_user, to_email, text)
        server.quit()
        print("Email sent successfully")
    except Exception as e:
        print(f"Failed to send email: {e}")

send_email("Test", "test is test.", 'kaz@thinkxinc.com')