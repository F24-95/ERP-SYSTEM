import asyncio
import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from src.core.logger import get_logger

logger = get_logger(__name__)

SMTP_SERVER = os.getenv("SMTP_SERVER")
SMTP_PORT = int(os.getenv("SMTP_PORT", 587))
SMTP_EMAIL = os.getenv("SMTP_EMAIL")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")


def _send_email_sync(to_email: str, subject: str, body: str) -> bool:
    """Blocking smtplib call, ported verbatim from legacy `email_services.py::send_email`.
    Only ever invoked via `send_email()` below, off the event loop thread.
    """
    try:
        msg = MIMEMultipart()
        msg["From"] = SMTP_EMAIL
        msg["To"] = to_email
        msg["Subject"] = subject
        msg.attach(MIMEText(body, "plain"))

        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.set_debuglevel(0)
        server.starttls()
        server.login(SMTP_EMAIL, SMTP_PASSWORD)
        server.send_message(msg)
        server.quit()

        logger.info(f"Email sent OK -> to={to_email} subject={subject}")
        return True
    except Exception as e:
        # Legacy used print() for both success and failure; routed through
        # the structured logger here instead (this project logs everywhere
        # else, no reason for this module to be the one place still using
        # print()). Same swallow-and-return-False behavior otherwise.
        logger.error(f"Email error: {e}")
        return False


async def send_email(to_email: str, subject: str, body: str) -> bool:
    """Async wrapper around the blocking smtplib call above.

    NOTE: legacy's `send_email` runs smtplib synchronously. In this async
    FastAPI app, calling that directly from a route/service coroutine would
    block the event loop for the duration of the SMTP round-trip. Ported the
    actual send logic byte-for-byte but wrapped it in `asyncio.to_thread` so
    it behaves like the rest of this codebase's I/O -- this is an
    adaptation to the async framework, not a change to what gets sent or
    how.
    """
    return await asyncio.to_thread(_send_email_sync, to_email, subject, body)


async def send_otp_email(email: str, otp: str, purpose: str = "verification") -> bool:
    if purpose == "login":
        subject = "Login OTP - Student ERP"
        reason_line = "Your OTP for login is"
    else:
        subject = "Email Verification OTP - Student ERP"
        reason_line = "Your OTP for email verification is"

    body = f"""
{reason_line}: {otp}

This OTP is valid for 10 minutes.
Do not share it with anyone.
"""
    return await send_email(email, subject, body)


async def send_reset_email(email: str, link: str) -> bool:
    subject = "Password Reset Request"
    body = f"""
Click below to reset password:

{link}

This link expires in 30 minutes.
"""
    return await send_email(email, subject, body)


async def send_verification_email(email: str, link: str) -> bool:
    subject = "Verify Your Email"
    body = f"""
Please verify your email by clicking the link below:

{link}
"""
    return await send_email(email, subject, body)
