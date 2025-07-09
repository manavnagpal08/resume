import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# 🔧 CONFIG — Replace with your Gmail & App Password
SENDER_EMAIL = "youremail@gmail.com"
APP_PASSWORD = "your-app-password"

def send_email_to_candidate(name, score, feedback):
    try:
        receiver_email = "example@example.com"  # Replace with actual logic or candidate email
        subject = "🎉 Resume Screening Result"
        body = f"""
        Hi,

        Congratulations! Your resume has been shortlisted based on our automated screening system.

        ✅ Score: {score}%
        💬 Feedback: {feedback}

        We will contact you soon regarding the next steps.

        Best,
        HR Team
        """

        msg = MIMEMultipart()
        msg["From"] = SENDER_EMAIL
        msg["To"] = receiver_email
        msg["Subject"] = subject

        msg.attach(MIMEText(body, "plain"))

        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()
            server.login(SENDER_EMAIL, APP_PASSWORD)
            server.send_message(msg)

        print(f"Email sent to {receiver_email}")
    except Exception as e:
        print(f"❌ Email failed: {e}")
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# 🔧 CONFIG — Replace with your Gmail & App Password
SENDER_EMAIL = "youremail@gmail.com"
APP_PASSWORD = "your-app-password"

def send_email_to_candidate(name, score, feedback):
    try:
        receiver_email = "example@example.com"  # Replace with actual logic or candidate email
        subject = "🎉 Resume Screening Result"
        body = f"""
        Hi,

        Congratulations! Your resume has been shortlisted based on our automated screening system.

        ✅ Score: {score}%
        💬 Feedback: {feedback}

        We will contact you soon regarding the next steps.

        Best,
        HR Team
        """

        msg = MIMEMultipart()
        msg["From"] = SENDER_EMAIL
        msg["To"] = receiver_email
        msg["Subject"] = subject

        msg.attach(MIMEText(body, "plain"))

        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()
            server.login(SENDER_EMAIL, APP_PASSWORD)
            server.send_message(msg)

        print(f"Email sent to {receiver_email}")
    except Exception as e:
        print(f"❌ Email failed: {e}")
