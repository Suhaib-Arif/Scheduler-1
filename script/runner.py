import models
from database import engine, SessionLocal
from models import Companies
import smtplib
from email.message import EmailMessage
import mimetypes
from tqdm import tqdm
import time
import os
import socket
from twilio.rest import Client 

models.Base.metadata.create_all(bind=engine)

db = SessionLocal()


companies = db.query(Companies).filter(Companies.email_sent==False).all()

FROM = os.environ.get("FROM")
APP_PASSWORD = os.environ.get("APP_PASSWORD")
account_id = os.environ.get("account_id")
auth_token = os.environ.get("auth_token")
to = os.environ.get("PHONENUMBER")



with open('script/email.txt') as file:
    message = file.read()

SUBJECT = "Application for Software Developer Position - MD. Suhaib Arif Siddiqui"

server = smtplib.SMTP('smtp.gmail.com', 587)
server.starttls()

server.login(FROM, APP_PASSWORD)

pdf_attachment_path = os.path.join("script", "resumefolder", "SuhaibResume.pdf")

error_message = None

def send_message(emails_sent: int, error_message: str):
    client = Client(account_id, auth_token)
    message = client.messages.create(
        from_='+16174090570',  # Use from_ instead of from
        body=f'Sucessfully applied to {emails_sent} companies today' if not error_message else f'Sucessfully applied to {emails_sent} companies today\n error occoured {error_message}',
        to=to
    )

emails_counter = 0

try:   
    for company in tqdm(companies):
        email = message.replace("[Hiring Manager's Name]", company.HRname).replace("[Company Name]", company.company)
        
        msg = EmailMessage()
        msg.set_content(email)  # Set the body of the email
        msg['Subject'] = SUBJECT  # Set the email subject
        msg['From'] = FROM
        msg['To'] = company.email  # Recipient's email address

        if pdf_attachment_path:
            # Guess the MIME type of the PDF
            mime_type, _ = mimetypes.guess_type(pdf_attachment_path)
            if mime_type is None:
                mime_type = 'application/pdf'  # Set the MIME type explicitly if unknown

            # Add the PDF attachment
            with open(pdf_attachment_path, 'rb') as f:
                msg.add_attachment(f.read(), maintype=mime_type.split('/')[0], subtype=mime_type.split('/')[1], filename=pdf_attachment_path.split('/')[-1])


        for attempt in range(3): 
            try:
                server.send_message(msg)
                emails_counter +=1

                company.email_sent = True
                db.commit()  # Commit the update to the database

                break  
            except smtplib.SMTPDataError as e:
                print(f"Error sending to {company.email}: {e}")
                if e.smtp_code == 550 and "Daily user sending limit exceeded" in e.smtp_error.decode():
                    print("Daily sending limit exceeded. Stopping further emails.")
                    raise e
                time.sleep(10) 
except Exception as e:
    error_message = f"An error occurred: {str(e)}"

finally:

    send_message(emails_sent=emails_counter, error_message=error_message)
    server.quit()
    db.close()
