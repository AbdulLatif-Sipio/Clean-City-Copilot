import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import logging

def notify_municipal_committee(ticket_id: str, category: str, severity: str, description: str, location: str = "Hyderabad"):
    # Yahan apni Gmail aur App Password daalna
    sender_email = "ahmedsyedfazeel95@gmail.com"  
    sender_password = "Fazeel2006@#$"   
    receiver_email = "fazeels441@gmail.com" 
    
    subject = f"🚨 URGENT: New Civic Ticket Generated [{ticket_id}] - {severity.upper()} Severity"
    
    body = f"""
    Respected Municipal Authority,
    
    A new citizen complaint has been registered and triaged by CleanCity Copilot AI Engine.
    
    --------------------------------------------------
    📌 Ticket ID: {ticket_id}
    📂 Category: {category}
    ⚠️ Severity: {severity}
    📍 Location: {location}
    
    📝 Description:
    {description}
    --------------------------------------------------
    
    Please log in to the CleanCity Municipal Admin Dashboard to dispatch field units immediately.
    
    Regards,
    CleanCity Copilot Automated Dispatch System
    Alibaba Cloud AI Hackathon 2026
    """
    
    try:
        msg = MIMEMultipart()
        msg['From'] = sender_email
        msg['To'] = receiver_email
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'plain'))
        
        server = smtplib.SMTP('smtp.com', 587) # ya smtp.gmail.com
        server.starttls()
        server.login(sender_email, sender_password)
        server.sendmail(sender_email, receiver_email, msg.as_string())
        server.quit()
        
        logging.info(f"Municipal alert email successfully sent for ticket {ticket_id}")
    except Exception as e:
        logging.error(f"Failed to send email alert: {str(e)}")