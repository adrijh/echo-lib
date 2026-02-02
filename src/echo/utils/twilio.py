import base64
import markdown
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import (
    Mail, Attachment, FileContent, FileName, 
    FileType, Disposition
)
import echo.config as cfg
from echo.utils.logs import configure_logger

logger = configure_logger(__name__)

class TwilioService:
    def __init__(self) -> None:
        self.sendgrid = SendGridAPIClient(cfg.SENDGRID_AUTH_TOKEN)

    def _generate_html_content(self, content_markdown: str) -> str:
        html_body = markdown.markdown(content_markdown)
        
        return f"""
        <html>
            <body style="font-family: Arial, sans-serif; color: #333; line-height: 1.6;">
                <div style="max-width: 600px; margin: auto; border: 1px solid #eee; padding: 20px; border-radius: 8px;">
                    <h2 style="color: #2c3e50; border-bottom: 2px solid #3498db; padding-bottom: 10px;">
                        Resumen de la Reunión
                    </h2>
                    <div style="margin-top: 20px;">
                        {html_body}
                    </div>
                    <hr style="border: 0; border-top: 1px solid #eee; margin: 20px 0;">
                    <footer style="font-size: 0.8em; color: #888; text-align: center;">
                        Este es un mensaje automático generado por el <strong>Sistema IA Queue Handler</strong>.
                        <br>Se adjunta la transcripción original para su referencia.
                    </footer>
                </div>
            </body>
        </html>
        """

    def _create_attachment(self, content: str, filename: str = "transcripcion_original.txt") -> Attachment:
        encoded_file = base64.b64encode(content.encode()).decode()
        return Attachment(
            FileContent(encoded_file),
            FileName(filename),
            FileType('text/plain'),
            Disposition('attachment')
        )

    def send_summary_email(self, subject: str, email_to: str, content_markdown: str, attachment_content: str = None) -> None:
        logger.info(f"Sending summary email to {email_to}...")

        full_html = self._generate_html_content(content_markdown)

        message = Mail(
            from_email=cfg.SENDGRID_MAIL_FROM,
            to_emails=email_to,
            subject=subject,
            html_content=full_html
        )

        if attachment_content:
            attachment = self._create_attachment(attachment_content)
            message.add_attachment(attachment)

        try:
            response = self.sendgrid.send(message)
            logger.info(f"Email with attachment sent successfully to {email_to}.")
        except Exception as e:
            logger.error(f"Error while sending email via SendGrid: {e}")