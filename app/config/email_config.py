from .settings import get_settings

settings = get_settings()

EMAIL_DEFS = {
    'verify_email': {
        'subject': "Verify your Zonecam account",
        'mail_from': settings.mail_from,
        'template_name': "verify_email.html",
    },

    'verify_email_complete': {
        'subject': "Welcome to Zonecam",
        'mail_from': settings.mail_from,
        'template_name': "verify_email_complete.html",
    },



    "reset_password": {
        "subject": "Reset Your Password",
        "mail_from": settings.mail_from,
        "template_name": "reset_password.html",

    },

    "reset_password_complete": {
        "subject": "Password Reset Successful",
        "mail_from": settings.mail_from,
        "template_name": "reset_password_complete.html",

    }




}
