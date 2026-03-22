"""
email_service.py
----------------
Sends email notifications when a job application status changes.
Uses Gmail SMTP via fastapi-mail.
"""

from fastapi_mail import FastMail, MessageSchema, ConnectionConfig, MessageType
from config import get_settings

settings = get_settings()

# Email connection config
conf = ConnectionConfig(
    MAIL_USERNAME=settings.mail_username,
    MAIL_PASSWORD=settings.mail_password,
    MAIL_FROM=settings.mail_from,
    MAIL_PORT=settings.mail_port,
    MAIL_SERVER=settings.mail_server,
    MAIL_STARTTLS=True,
    MAIL_SSL_TLS=False,
    USE_CREDENTIALS=True,
)

STATUS_COLORS = {
    "applied":   "#3B82F6",
    "interview": "#F59E0B",
    "offer":     "#10B981",
    "rejected":  "#EF4444",
}

STATUS_MESSAGES = {
    "applied":   "Your application has been submitted. Good luck!",
    "interview": "Great news! You've been selected for an interview. Prepare well!",
    "offer":     "Congratulations! You've received a job offer!",
    "rejected":  "Unfortunately this application didn't work out. Keep going — the right opportunity is coming!",
}


def build_email_html(company: str, role: str, status: str, user_email: str) -> str:
    color   = STATUS_COLORS.get(status, "#6B7280")
    message = STATUS_MESSAGES.get(status, "Your application status has been updated.")

    return f"""
    <!DOCTYPE html>
    <html>
    <head><meta charset="UTF-8"></head>
    <body style="margin:0;padding:0;background:#f4f6f8;font-family:Arial,sans-serif;">
      <table width="100%" cellpadding="0" cellspacing="0" style="background:#f4f6f8;padding:40px 0;">
        <tr>
          <td align="center">
            <table width="520" cellpadding="0" cellspacing="0"
              style="background:#ffffff;border-radius:12px;overflow:hidden;box-shadow:0 4px 12px rgba(0,0,0,0.08);">

              <!-- Header -->
              <tr>
                <td style="background:{color};padding:32px;text-align:center;">
                  <h1 style="margin:0;color:#ffffff;font-size:22px;font-weight:700;">
                    Job Application Update
                  </h1>
                  <p style="margin:8px 0 0;color:rgba(255,255,255,0.85);font-size:14px;">
                    AI Job Assistant
                  </p>
                </td>
              </tr>

              <!-- Body -->
              <tr>
                <td style="padding:32px;">
                  <p style="margin:0 0 20px;color:#374151;font-size:15px;">
                    Hi <strong>{user_email}</strong>,
                  </p>
                  <p style="margin:0 0 24px;color:#374151;font-size:15px;">
                    {message}
                  </p>

                  <!-- Job Card -->
                  <table width="100%" cellpadding="0" cellspacing="0"
                    style="background:#f9fafb;border:1px solid #e5e7eb;border-radius:8px;margin-bottom:24px;">
                    <tr>
                      <td style="padding:20px;">
                        <table width="100%" cellpadding="0" cellspacing="0">
                          <tr>
                            <td style="padding:6px 0;">
                              <span style="color:#6b7280;font-size:13px;">Company</span><br>
                              <strong style="color:#111827;font-size:15px;">{company}</strong>
                            </td>
                          </tr>
                          <tr>
                            <td style="padding:6px 0;">
                              <span style="color:#6b7280;font-size:13px;">Role</span><br>
                              <strong style="color:#111827;font-size:15px;">{role}</strong>
                            </td>
                          </tr>
                          <tr>
                            <td style="padding:6px 0;">
                              <span style="color:#6b7280;font-size:13px;">Status</span><br>
                              <span style="display:inline-block;margin-top:4px;padding:4px 12px;
                                background:{color};color:#fff;border-radius:20px;
                                font-size:13px;font-weight:600;text-transform:capitalize;">
                                {status}
                              </span>
                            </td>
                          </tr>
                        </table>
                      </td>
                    </tr>
                  </table>

                  <p style="margin:0;color:#9ca3af;font-size:13px;text-align:center;">
                    This notification was sent by AI Job Assistant.
                  </p>
                </td>
              </tr>

            </table>
          </td>
        </tr>
      </table>
    </body>
    </html>
    """


async def send_status_email(user_email: str, company: str, role: str, status: str):
    """
    Send a job status update email to the user.
    Fails silently so it never breaks the main API response.
    """
    if not settings.mail_username or not settings.mail_password:
        return  # Email not configured — skip silently

    try:
        html = build_email_html(company, role, status, user_email)

        message = MessageSchema(
            subject=f"Job Update: {company} — {status.capitalize()}",
            recipients=[user_email],
            body=html,
            subtype=MessageType.html,
        )

        fm = FastMail(conf)
        await fm.send_message(message)

    except Exception as e:
        # Never crash the API because of email failure
        print(f"[Email] Failed to send to {user_email}: {e}")
