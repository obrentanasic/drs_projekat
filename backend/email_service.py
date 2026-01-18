import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class EmailService:
    def __init__(self):
        self.smtp_server = 'quiz_mailhog'  
        self.smtp_port = 1025               # Port unutar Docker mreže
        self.from_email = 'noreply@quizplatform.com'
        self.enabled = True 
        
        logger.info(f" EmailService CONFIGURED")
        logger.info(f"   SMTP Server: {self.smtp_server}:{self.smtp_port}")
        logger.info(f"   From Email: {self.from_email}")
        logger.info(f"   Enabled: {self.enabled}")
    
    def send_email(self, to_email, subject, html_content, text_content=None):
        """Slanje email-a"""
        logger.info(f" SENDING EMAIL to: {to_email}")
        logger.info(f"   Subject: {subject}")
        logger.info(f"   SMTP Server: {self.smtp_server}:{self.smtp_port}")
        
        try:
            # Test konekcije
            import socket
            logger.info(f"   Testing connection to {self.smtp_server}:{self.smtp_port}...")
            
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5)
            result = sock.connect_ex((self.smtp_server, self.smtp_port))
            sock.close()
            
            if result != 0:
                logger.error(f"    Connection FAILED (error code: {result})")
                logger.error(f"   Trying alternative: 172.18.0.2:1025")
                
                self.smtp_server = '172.18.0.2'
                logger.info(f"   Retrying with IP: {self.smtp_server}:{self.smtp_port}")
            
            # Kreiraj poruku
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = self.from_email
            msg['To'] = to_email
            
            if text_content:
                msg.attach(MIMEText(text_content, 'plain'))
            msg.attach(MIMEText(html_content, 'html'))
            
            # Slanje emaila
            with smtplib.SMTP(self.smtp_server, self.smtp_port, timeout=10) as server:
                server.ehlo()
                server.send_message(msg)
                logger.info(f"    Email SENT successfully to {to_email}")
                return True
                
        except Exception as e:
            logger.error(f"    Email sending FAILED: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return False
    
    def send_role_change_email(self, to_email, first_name, old_role, new_role):
        """Slanje email-a pri promeni uloge"""
        subject = "Promena uloge - QuizPlatform"
        
        html = f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6;">
            <h2>Promjena uloge - QuizPlatform</h2>
            <p>Poštovani/na {first_name},</p>
            <p>Vaša uloga na QuizPlatform je promjenjena.</p>
            <div style="background: #f5f5f5; padding: 15px; border-radius: 5px; margin: 15px 0;">
                <p><strong>Stara uloga:</strong> {old_role}</p>
                <p><strong>Nova uloga:</strong> {new_role}</p>
                <p><strong>Datum promene:</strong> {datetime.now().strftime('%d.%m.%Y %H:%M')}</p>
            </div>
            
        </body>
        </html>
        """
        
        text = f"""Promena uloge - QuizPlatform

Poštovani/na {first_name},

Vaša uloga na QuizPlatform je promjenjena.

Stara uloga: {old_role}
Nova uloga: {new_role}
Datum promene: {datetime.now().strftime('%d.%m.%Y %H:%M')}


"""
        
        return self.send_email(to_email, subject, html, text)

# Globalna instanca
email_service = EmailService()