import os
import smtplib
import ssl

from email.message import EmailMessage
from email.utils import formataddr

from dotenv import load_dotenv


load_dotenv()


SMTP_HOST = os.getenv("SMTP_HOST")
SMTP_PORT = int(
    os.getenv(
        "SMTP_PORT",
        "465"
    )
)

SMTP_USERNAME = os.getenv(
    "SMTP_USERNAME"
)

SMTP_PASSWORD = os.getenv(
    "SMTP_PASSWORD"
)

SMTP_FROM_EMAIL = os.getenv(
    "SMTP_FROM_EMAIL",
    SMTP_USERNAME
)

SMTP_FROM_NAME = os.getenv(
    "SMTP_FROM_NAME",
    "Minecraft Hosting"
)

SMTP_USE_SSL = os.getenv(
    "SMTP_USE_SSL",
    "true"
).lower() in {
    "1",
    "true",
    "yes"
}


def validate_email_settings():
    required_settings = {
        "SMTP_HOST": SMTP_HOST,
        "SMTP_USERNAME": SMTP_USERNAME,
        "SMTP_PASSWORD": SMTP_PASSWORD,
        "SMTP_FROM_EMAIL": SMTP_FROM_EMAIL
    }

    missing_settings = [
        name
        for name, value in required_settings.items()
        if not value
    ]

    if missing_settings:
        raise RuntimeError(
            "Missing email settings: "
            + ", ".join(missing_settings)
        )


def create_verification_message(
    recipient_email: str,
    verification_code: str
):
    message = EmailMessage()

    message["Subject"] = (
        "Verify your Minecraft Hosting account"
    )

    message["From"] = formataddr(
        (
            SMTP_FROM_NAME,
            SMTP_FROM_EMAIL
        )
    )

    message["To"] = recipient_email

    message.set_content(
        "Your Minecraft Hosting verification "
        f"code is: {verification_code}\n\n"
        "The code expires in 10 minutes.\n\n"
        "If you did not create this account, "
        "ignore this email."
    )

    message.add_alternative(
        f"""
        <!DOCTYPE html>
        <html lang="en">
        <body style="margin: 0; padding: 30px; background: #181818; color: #ffffff; font-family: Arial, sans-serif;">
            <div style="max-width: 520px; margin: 0 auto; padding: 30px; background: #252525; border: 1px solid #3a3a3a; border-radius: 14px;">
                <h1 style="margin: 0 0 18px;">
                    Verify your email
                </h1>

                <p>
                    Use this code to verify your Minecraft Hosting account:
                </p>

                <div style="margin: 24px 0; padding: 18px; background: #181818; border-radius: 10px; color: #73d67c; font-size: 32px; font-weight: bold; letter-spacing: 8px; text-align: center;">
                    {verification_code}
                </div>

                <p>
                    This code expires in 10 minutes.
                </p>

                <p style="margin-bottom: 0; color: #aaaaaa; font-size: 14px;">
                    If you did not create this account, ignore this email.
                </p>
            </div>
        </body>
        </html>
        """,
        subtype="html"
    )

    return message


def send_verification_email(
    recipient_email: str,
    verification_code: str
):
    validate_email_settings()

    message = create_verification_message(
        recipient_email,
        verification_code
    )

    ssl_context = (
        ssl.create_default_context()
    )

    if SMTP_USE_SSL:
        with smtplib.SMTP_SSL(
            SMTP_HOST,
            SMTP_PORT,
            timeout=30,
            context=ssl_context
        ) as smtp:
            smtp.login(
                SMTP_USERNAME,
                SMTP_PASSWORD
            )

            smtp.send_message(
                message
            )

        return

    with smtplib.SMTP(
        SMTP_HOST,
        SMTP_PORT,
        timeout=30
    ) as smtp:
        smtp.ehlo()

        smtp.starttls(
            context=ssl_context
        )

        smtp.ehlo()

        smtp.login(
            SMTP_USERNAME,
            SMTP_PASSWORD
        )

        smtp.send_message(
            message
        )