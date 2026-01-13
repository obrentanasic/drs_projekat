import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
import logging
from config import Config

logger = logging.getLogger(__name__)

class EmailService:
    def __init__(self):
        self.smtp_server = Config.SMTP_SERVER
        self.smtp_port = Config.SMTP_PORT
        self.smtp_username = Config.SMTP_USERNAME
        self.smtp_password = Config.SMTP_PASSWORD
        self.from_email = Config.FROM_EMAIL
        self.enabled = Config.EMAIL_ENABLED
        
        # Debugging info - BITNO: ne disable-uj zbog praznih kredencijala
        logger.info(f" EmailService initialized")
        logger.info(f" Enabled: {self.enabled}")
        logger.info(f" SMTP: {self.smtp_server}:{self.smtp_port}")
        logger.info(f" From: {self.from_email}")
        

        if self.enabled:
            logger.info(" Email service ENABLED (MailHog mode - no auth needed)")
        else:
            logger.warning(" Email service DISABLED (set EMAIL_ENABLED=1 to enable)")
    
    def send_email(self, to_email, subject, html_content, text_content=None):
        """Slanje email-a - STVARNO SLANJE U MAILHOG"""
        if not self.enabled:
            logger.info(f" Email service disabled. Would send to {to_email}: {subject}")
            return True
        
        logger.info(f" Sending email to: {to_email}")
        logger.info(f" Subject: {subject}")
        logger.info(f" Using SMTP: {self.smtp_server}:{self.smtp_port}")
        
        try:
            # Kreiraj poruku
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = self.from_email
            msg['To'] = to_email
            
            # Dodaj tekstualni deo (ako postoji)
            if text_content:
                msg.attach(MIMEText(text_content, 'plain'))
            
            # Dodaj HTML deo
            msg.attach(MIMEText(html_content, 'html'))
            
            # MailHog ne zahteva STARTTLS ili login
            logger.info(f" Connecting to MailHog...")
            
            with smtplib.SMTP(self.smtp_server, self.smtp_port, timeout=10) as server:
                # MailHog je development SMTP server
                # Nema enkripcije, nema autentifikacije
                server.send_message(msg)
            
            logger.info(f" Email successfully sent to {to_email}")
            logger.info(f" Check MailHog at: http://localhost:18025")
            return True
            
        except Exception as e:
            logger.error(f" FAILED to send email to {to_email}")
            logger.error(f" Error details: {e}")
            logger.error(f" SMTP Config used: {self.smtp_server}:{self.smtp_port}")
            
            # Dodatni debug info
            import socket
            try:
                # Testiraj konekciju
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(5)
                result = sock.connect_ex((self.smtp_server, self.smtp_port))
                if result == 0:
                    logger.error(f"Port {self.smtp_port} is OPEN but SMTP failed")
                else:
                    logger.error(f" Port {self.smtp_port} is CLOSED or blocked")
                sock.close()
            except:
                pass
                
            return False
    
    def send_welcome_email(self, to_email, first_name):
        """Slanje welcome email-a pri registraciji"""
        subject = "Dobrodošli na QuizPlatform!"
        
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0; }}
                .content {{ padding: 30px; background: #f9f9f9; border-radius: 0 0 10px 10px; }}
                .welcome {{ font-size: 24px; color: #333; margin-bottom: 20px; }}
                .features {{ margin: 20px 0; }}
                .feature {{ background: white; padding: 15px; margin: 10px 0; border-left: 4px solid #667eea; border-radius: 5px; }}
                .footer {{ margin-top: 30px; padding-top: 20px; border-top: 1px solid #ddd; color: #666; font-size: 12px; text-align: center; }}
                .button {{ display: inline-block; background: #667eea; color: white; padding: 12px 30px; text-decoration: none; border-radius: 5px; margin: 20px 0; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>🎉 Dobrodošli na QuizPlatform!</h1>
            </div>
            <div class="content">
                <div class="welcome">Poštovani/na {first_name},</div>
                
                <p>Drago nam je što ste se pridružili našoj platformi! Vaš nalog je uspešno kreiran.</p>
                
                <div class="features">
                    <h3>📚 Šta možete da radite:</h3>
                    <div class="feature">
                        <strong>🎮 Igrajte kvizove</strong>
                        
                    </div>
                    <div class="feature">
                       
                       
                    </div>
                    <div class="feature">
                       
                    </div>
                </div>
                
                <p>Vaša početna uloga je <strong>IGRAČ</strong>. Ukoliko želite da postavljate sopstvene kvizove, 
                kontaktirajte administratora za promenu uloge u MODERATOR.</p>
                
                <center>
                    <a href="http://localhost:5173" class="button">Započnite igru</a>
                </center>
                
                <p>Ukoliko imate bilo kakva pitanja, slobodno nam se obratite.</p>
                
             
            </div>
            <div class="footer">
                <p>Ovo je automatski generisana poruka. Molimo ne odgovarajte na ovaj email.</p>
                <p>© {datetime.now().year} 
            </div>
        </body>
        </html>
        """
        
        text = f"""
        Dobrodošli na QuizPlatform!
        
        Poštovani/na {first_name},
        
        Drago nam je što ste se pridružili našoj platformi! Vaš nalog je uspešno kreiran.
        
        Vaša početna uloga je IGRAČ. Ukoliko želite da postavljate sopstvene kvizove, 
        kontaktirajte administratora za promjenu uloge u MODERATOR.
        
        Posetite našu platformu: http://localhost:5173
        
        
        
        Ovo je automatski generisana poruka. Molimo ne odgovarajte na ovaj email.
        © {datetime.now().year} QuizPlatform. Sva prava zadržana.
        """
        
        return self.send_email(to_email, subject, html, text)
    
    def send_role_change_email(self, to_email, first_name, old_role, new_role):
        """Slanje email-a pri promeni uloge (PO SPECIFIKACIJI!)"""
        subject = "Promena uloge - QuizPlatform"
        
        # Određivanje šta nova uloga donosi
        role_benefits = ""
        if new_role == "MODERATOR":
            role_benefits = """
            <div class="benefits">
                <h3>🎨 Nove mogućnosti kao MODERATOR:</h3>
                <ul>
                    <li>Kreiranje sopstvenih kvizova</li>
                    <li>Uređivanje postojećih kvizova</li>
                    <li>Pregled statistike vaših kvizova</li>
                    <li>Odobravanje od strane administratora pre objavljivanja</li>
                </ul>
            </div>
            """
        elif new_role == "ADMINISTRATOR":
            role_benefits = """
            <div class="benefits">
                <h3>⚙️ Nove mogućnosti kao ADMINISTRATOR:</h3>
                <ul>
                    <li>Upravljanje svim korisnicima platforme</li>
                    <li>Odobravanje/odbijanje kvizova</li>
                    <li>Pregled svih statistika platforme</li>
                    <li>Generisanje izveštaja</li>
                    <li>Blokiranje/odblokiranje korisnika</li>
                </ul>
            </div>
            """
        
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background: linear-gradient(135deg, #4CAF50 0%, #45a049 100%); color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0; }}
                .content {{ padding: 30px; background: #f9f9f9; border-radius: 0 0 10px 10px; }}
                .role-change {{ background: white; padding: 20px; margin: 20px 0; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
                .role-old {{ color: #666; text-decoration: line-through; }}
                .role-new {{ color: #4CAF50; font-weight: bold; font-size: 20px; }}
                .benefits {{ background: #e8f5e9; padding: 20px; margin: 20px 0; border-radius: 10px; border-left: 4px solid #4CAF50; }}
                .footer {{ margin-top: 30px; padding-top: 20px; border-top: 1px solid #ddd; color: #666; font-size: 12px; text-align: center; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>🔄 Promjena uloge</h1>
                <p>Vaša uloga je ažurirana</p>
            </div>
            <div class="content">
                <h2>Poštovani/na {first_name},</h2>
                <p>Obavještavamo vas da je vaša uloga promenjena.</p>
                
                <div class="role-change">
                    <p><strong>Stara uloga:</strong> <span class="role-old">{old_role}</span></p>
                    <p><strong>Nova uloga:</strong> <span class="role-new">{new_role}</span></p>
                    <p><strong>Datum promene:</strong> {datetime.now().strftime('%d.%m.%Y %H:%M')}</p>
                </div>
                
                {role_benefits}
                
                <p>Ukoliko niste tražili ovu promjenu ili imate bilo kakvih pitanja, kontaktirajte nas odmah.</p>
                
                
            </div>
            <div class="footer">
                <p>Ovo je automatski generisana poruka. Molimo ne odgovarajte na ovaj email.</p>
                <p>© {datetime.now().year} QuizPlatform. Sva prava zadržana.</p>
            </div>
        </body>
        </html>
        """
        
        text = f"""
        Promena uloge - QuizPlatform
        
        Poštovani/na {first_name},
        
        Obaveštavamo vas da je vaša uloga na QuizPlatform promenjena.
        
        Stara uloga: {old_role}
        Nova uloga: {new_role}
        Datum promene: {datetime.now().strftime('%d.%m.%Y %H:%M')}
        
       
        
        
        Ovo je automatski generisana poruka. Molimo ne odgovarajte na ovaj email.
        © {datetime.now().year} 
        """
        
        return self.send_email(to_email, subject, html, text)

# Globalna instanca
email_service = EmailService()
