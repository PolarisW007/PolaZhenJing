"""QQ Email SMTP mailer for sending verification codes."""
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart


def send_verification_code(to_email: str, code: str) -> bool:
    """Send a 6-digit verification code via QQ Email SMTP.

    Returns True on success, False on failure.
    """
    qq_email = os.getenv('QQ_EMAIL')
    auth_code = os.getenv('QQ_EMAIL_AUTH_CODE')

    if not qq_email or not auth_code:
        print('[Mailer] QQ_EMAIL or QQ_EMAIL_AUTH_CODE not configured. Skipping email.')
        return False

    subject = 'PolaZhenjing — Email Verification Code'
    html_body = f"""
    <div style="font-family: -apple-system, sans-serif; max-width: 480px; margin: 0 auto;
                padding: 2rem; background: #050508; color: #fff; border-radius: 12px;">
        <h2 style="color: #E4BF7A; margin: 0 0 1rem;">PolaZhenjing</h2>
        <p style="color: rgba(255,255,255,0.7); line-height: 1.6;">
            Your verification code is:
        </p>
        <div style="font-size: 2rem; font-weight: 700; color: #E4BF7A;
                    letter-spacing: 0.3em; padding: 1rem 0; text-align: center;">
            {code}
        </div>
        <p style="color: rgba(255,255,255,0.5); font-size: 0.85rem;">
            This code expires in 5 minutes. If you did not request this, please ignore.
        </p>
    </div>
    """

    msg = MIMEMultipart('alternative')
    msg['Subject'] = subject
    msg['From'] = qq_email
    msg['To'] = to_email
    msg.attach(MIMEText(html_body, 'html', 'utf-8'))

    try:
        with smtplib.SMTP_SSL('smtp.qq.com', 465, timeout=10) as server:
            server.login(qq_email, auth_code)
            server.send_message(msg)
        print(f'[Mailer] Verification code sent to {to_email}')
        return True
    except Exception as e:
        print(f'[Mailer] Failed to send email: {e}')
        return False
