from pydantic import EmailStr
from huey.exceptions import CancelExecution
from .setup import huey
from app.config.settings import get_settings
from app.utils.emails.send_email import dispatch_email
from app.config.settings import get_settings


settings = get_settings()


@huey.task(retries=2,  retry_delay=15, name="task_send_email")
def task_send_email(email_type:  str, email_to:  EmailStr | list[EmailStr], email_data:  dict):

    email_data.update({
        "support_email": settings.support_email
    })

    try:

        dispatch_email(email_to, email_type, email_data)

    except:

        raise CancelExecution()
