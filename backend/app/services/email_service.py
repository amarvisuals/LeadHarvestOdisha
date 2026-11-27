import logging
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Optional
import httpx

from app.core.config import settings

logger = logging.getLogger("leadharvest.email")


def _wrap_html(title: str, body_html: str) -> str:
    return f"""
    <div style="font-family:Inter,Segoe UI,Arial,sans-serif;max-width:560px;margin:24px auto;border:1px solid #e2e8f0;border-radius:16px;overflow:hidden;background:#ffffff;">
      <div style="background:#0f766e;color:#ffffff;padding:20px 24px;">
        <h2 style="margin:0;font-size:18px;">LeadHarvest India</h2>
      </div>
      <div style="padding:24px;color:#1e293b;font-size:14px;line-height:1.6;">
        <h3 style="margin-top:0;color:#0f172a;">{title}</h3>
        {body_html}
      </div>
      <div style="background:#f8fafc;padding:14px 24px;font-size:12px;color:#64748b;border-top:1px solid #e2e8f0;">
        LeadHarvest India · Built for Indian B2B Agencies &amp; Freelancers
      </div>
    </div>
    """


class EmailService:
    """Transactional email abstraction supporting Console, SMTP, and Resend."""

    async def send(self, to_email: str, subject: str, title: str, body_html: str) -> bool:
        html = _wrap_html(title, body_html)
        provider = settings.EMAIL_PROVIDER.lower()

        if provider == "console":
            logger.info(f"[EMAIL-CONSOLE] To: {to_email} | Subject: {subject}")
            return True

        if provider == "resend" and settings.RESEND_API_KEY:
            try:
                async with httpx.AsyncClient(timeout=10.0) as client:
                    res = await client.post(
                        "https://api.resend.com/emails",
                        headers={"Authorization": f"Bearer {settings.RESEND_API_KEY}"},
                        json={
                            "from": settings.EMAIL_FROM,
                            "to": [to_email],
                            "subject": subject,
                            "html": html,
                        },
                    )
                    return res.status_code in (200, 201)
            except Exception as e:
                logger.error(f"Resend email error: {e}")
                return False

        if provider == "smtp" and settings.SMTP_HOST:
            try:
                msg = MIMEMultipart("alternative")
                msg["Subject"] = subject
                msg["From"] = settings.EMAIL_FROM
                msg["To"] = to_email
                msg.attach(MIMEText(html, "html"))
                with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=10) as server:
                    server.starttls()
                    if settings.SMTP_USER and settings.SMTP_PASSWORD:
                        server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
                    server.sendmail(settings.EMAIL_FROM, [to_email], msg.as_string())
                return True
            except Exception as e:
                logger.error(f"SMTP email error: {e}")
                return False

        logger.info(f"[EMAIL-FALLBACK] To: {to_email} | Subject: {subject}")
        return True

    async def send_verification(self, to_email: str, name: str, token: str):
        link = f"{settings.FRONTEND_URL}/verify-email?token={token}"
        await self.send(
            to_email,
            "Verify your LeadHarvest India email",
            f"Welcome, {name}!",
            f"<p>Please verify your email address to unlock saved history and smart deduplication:</p>"
            f"<p><a href='{link}' style='display:inline-block;padding:10px 18px;background:#0f766e;color:#fff;text-decoration:none;border-radius:8px;font-weight:bold;'>Verify Email</a></p>",
        )

    async def send_password_reset(self, to_email: str, name: str, token: str):
        link = f"{settings.FRONTEND_URL}/reset-password?token={token}"
        await self.send(
            to_email,
            "Reset your LeadHarvest India password",
            "Password Reset Request",
            f"<p>Hi {name}, click below to choose a new password (valid for 1 hour):</p>"
            f"<p><a href='{link}' style='display:inline-block;padding:10px 18px;background:#0f766e;color:#fff;text-decoration:none;border-radius:8px;font-weight:bold;'>Reset Password</a></p>",
        )

    async def send_payment_receipt(self, to_email: str, name: str, plan_name: str, total_inr: int, invoice_no: str):
        await self.send(
            to_email,
            f"Payment Receipt – {invoice_no}",
            "Thank you for upgrading!",
            f"<p>Hi {name}, your <strong>{plan_name}</strong> plan is now active.</p>"
            f"<p>Amount paid: <strong>INR {total_inr:,}</strong><br/>Invoice: <strong>{invoice_no}</strong></p>",
        )

    async def send_payment_failed(self, to_email: str, name: str, plan_name: str):
        await self.send(
            to_email,
            "Action required: Payment failed for LeadHarvest India",
            "Payment Failed – 3-Day Grace Period Active",
            f"<p>Hi {name}, your renewal payment for <strong>{plan_name}</strong> failed. "
            f"Your plan remains active for 3 days while you update your payment method in Billing.</p>",
        )


email_service = EmailService()
