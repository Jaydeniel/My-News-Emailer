import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

def send_email(subject: str, html_body: str, text_body: str = None):
    host = os.environ.get("SMTP_HOST", "smtp.gmail.com")
    port = int(os.environ.get("SMTP_PORT", "587"))
    user = os.environ.get("SMTP_USERNAME")
    pwd  = os.environ.get("SMTP_PASSWORD")
    use_starttls = os.environ.get("SMTP_STARTTLS", "true").lower() == "true"
    use_ssl = os.environ.get("SMTP_SSL", "false").lower() == "true"

    from_email = os.environ.get("MAIL_FROM")
    to_emails = [e.strip() for e in os.environ.get("MAIL_TO", "").split(",") if e.strip()]

    if not from_email or not to_emails:
        raise RuntimeError("MAIL_FROM and MAIL_TO must be set in environment (.env)")

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = from_email
    msg["To"] = ", ".join(to_emails)

    if text_body:
        msg.attach(MIMEText(text_body, "plain", "utf-8"))
    msg.attach(MIMEText(html_body, "html", "utf-8"))

    if use_ssl or port == 465:
        with smtplib.SMTP_SSL(host, port) as server:
            if user and pwd:
                server.login(user, pwd)
            server.sendmail(from_email, to_emails, msg.as_string())
    else:
        with smtplib.SMTP(host, port) as server:
            if use_starttls:
                server.starttls()
            if user and pwd:
                server.login(user, pwd)
            server.sendmail(from_email, to_emails, msg.as_string())