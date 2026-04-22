from __future__ import annotations

import smtplib
from email.message import EmailMessage
from typing import Union

from app.config import Settings


class MailService:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def _require_config(self) -> None:
        required = [
            self.settings.smtp_host,
            str(self.settings.smtp_port),
            self.settings.smtp_username,
            self.settings.smtp_password,
            self.settings.smtp_from_email,
        ]
        if any(not item for item in required):
            raise ValueError("SMTP is not fully configured. Set SMTP env vars.")

    def send_email(self, *, to_email: str, subject: str, body: str) -> None:
        self._require_config()
        msg = EmailMessage()
        from_name = self.settings.smtp_from_name.strip() or "VerifAI TPO"
        msg["From"] = f"{from_name} <{self.settings.smtp_from_email}>"
        msg["To"] = to_email
        msg["Subject"] = subject
        msg.set_content(body)

        port = int(self.settings.smtp_port)
        use_ssl = port == 465

        smtp_cls: Union[type[smtplib.SMTP], type[smtplib.SMTP_SSL]]
        smtp_cls = smtplib.SMTP_SSL if use_ssl else smtplib.SMTP

        with smtp_cls(self.settings.smtp_host, port, timeout=30) as server:
            if not use_ssl:
                server.ehlo()
                if server.has_extn("starttls"):
                    server.starttls()
                    server.ehlo()
            server.login(self.settings.smtp_username, self.settings.smtp_password)
            server.send_message(msg)
