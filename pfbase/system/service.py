from django.core.mail import send_mail

class EmailSendNotification:
    """
    Email send notifications
    """
    @staticmethod
    def send_notification(subject, message, from_email, to, html_message=None):
        send_mail(subject, message, from_email, to, html_message=html_message)
