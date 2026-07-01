"""
Envio de e-mail via SMTP do Gmail (usando uma "senha de app" da conta remetente).
Recebe as credenciais por parâmetro (não lê secrets sozinho) para poder ser usado
tanto pelo app Streamlit quanto pelo script standalone do GitHub Actions.

Por que Gmail SMTP em vez de um serviço transacional (Resend/SendGrid): sem verificar
um domínio próprio, esses serviços só liberam envio para o e-mail da própria conta.
O Gmail via SMTP manda para qualquer destinatário sem essa restrição.
"""
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

SMTP_HOST = "smtp.gmail.com"
SMTP_PORT = 465


def enviar_email(destino, assunto, corpo_html, remetente_email, senha_app):
    """Envia um e-mail via SMTP do Gmail. Retorna (sucesso: bool, erro: str|None)."""
    if not remetente_email or not senha_app:
        return False, "GMAIL_EMAIL / GMAIL_APP_PASSWORD não configurados."
    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = assunto
        msg["From"] = remetente_email
        msg["To"] = destino
        msg.attach(MIMEText(corpo_html, "html", "utf-8"))

        with smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT, timeout=20) as smtp:
            smtp.login(remetente_email, senha_app)
            smtp.sendmail(remetente_email, [destino], msg.as_string())
        return True, None
    except Exception as e:
        return False, str(e)
