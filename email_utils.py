"""
Envio de e-mail via SMTP do Gmail (usando uma "senha de app" da conta remetente).
Recebe as credenciais por parâmetro (não lê secrets sozinho) para poder ser usado
tanto pelo app Streamlit quanto pelo script standalone do GitHub Actions.

Por que Gmail SMTP em vez de um serviço transacional (Resend/SendGrid): sem verificar
um domínio próprio, esses serviços só liberam envio para o e-mail da própria conta.
O Gmail via SMTP manda para qualquer destinatário sem essa restrição.
"""
import mimetypes
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders

SMTP_HOST = "smtp.gmail.com"
SMTP_PORT = 465

MAX_ANEXO_BYTES = 5 * 1024 * 1024  # 5MB


def enviar_email(destino, assunto, corpo_html, remetente_email, senha_app, anexos=None):
    """
    Envia um e-mail via SMTP do Gmail. Retorna (sucesso: bool, erro: str|None).
    `anexos`, se informado, é uma lista de tuplas (nome_arquivo, conteudo_bytes).
    Anexos maiores que 5MB (somados) são recusados antes de tentar enviar.
    """
    if not remetente_email or not senha_app:
        return False, "GMAIL_EMAIL / GMAIL_APP_PASSWORD não configurados."

    anexos = anexos or []
    tamanho_total = sum(len(conteudo) for _, conteudo in anexos)
    if tamanho_total > MAX_ANEXO_BYTES:
        return False, "Anexo(s) excedem o limite de 5MB."

    try:
        msg = MIMEMultipart("mixed")
        msg["Subject"] = assunto
        msg["From"] = remetente_email
        msg["To"] = destino

        alternativo = MIMEMultipart("alternative")
        alternativo.attach(MIMEText(corpo_html, "html", "utf-8"))
        msg.attach(alternativo)

        for nome_arquivo, conteudo in anexos:
            tipo, _ = mimetypes.guess_type(nome_arquivo)
            tipo_principal, tipo_sub = (tipo.split("/", 1) if tipo else ("application", "octet-stream"))
            parte = MIMEBase(tipo_principal, tipo_sub)
            parte.set_payload(conteudo)
            encoders.encode_base64(parte)
            parte.add_header("Content-Disposition", f'attachment; filename="{nome_arquivo}"')
            msg.attach(parte)

        with smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT, timeout=20) as smtp:
            smtp.login(remetente_email, senha_app)
            smtp.sendmail(remetente_email, [destino], msg.as_string())
        return True, None
    except Exception as e:
        return False, str(e)
