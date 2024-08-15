import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from django.conf import settings
from django.core.mail import EmailMessage

def send_notification_email(subject, message, recipient_list):
    smtp_server = settings.EMAIL_HOST
    smtp_port = settings.EMAIL_PORT
    smtp_user = settings.EMAIL_HOST_USER
    smtp_password = settings.EMAIL_HOST_PASSWORD
    from_email = smtp_user
    try:
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(smtp_user, smtp_password)
            for recipient in recipient_list:
                msg = MIMEMultipart()
                msg['From'] = from_email
                msg['To'] = recipient
                msg['Subject'] = subject
                msg.attach(MIMEText(message, 'plain'))
                server.sendmail(from_email, recipient, msg.as_string())
        return True
    except Exception as e:
        print(f"Failed to send email: {e}")
        return False

def send_approve_users(title, message, recipient_list, file_attachments=[], content_subtype=''):
    try:
        email = EmailMessage(
            f'{title}',
            f'{message}',
            settings.EMAIL_HOST_USER,
            recipient_list,
        )
        if file_attachments:
            for file in file_attachments:
                file_name = file.split('/')[-1]
                email.attach_file(file)
        
        if content_subtype:
            email.content_subtype = content_subtype

        email.send(fail_silently=False)
        return True
    except Exception as e:
        print(f"Failed to send email: {e}")
        return False