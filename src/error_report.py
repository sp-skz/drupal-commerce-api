import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import os
from datetime import datetime

########### VARIABLES AJUSTES FOR GMAIL ACCOUNT

stmp = 'smtp.gmail.com'
port = 465

######### Reciver Email

receiver = ['sportoles@sekuenz.com', 'mnosas@sekuenz.com']

class ErrorReport:
    def __init__(self):
        self.user = os.getenv('GOOGLE_USER')
        self.password = os.getenv('APP_PW')
        self.stmp = stmp
        self.port = port
        self.subject = f'Status Report {datetime.now().day} {datetime.now().month}'
        self.receiver = receiver
        self.body = ''

    def add_name(self, name):
        self.subject = f'Status Report for {name} {datetime.now().day} {datetime.now().month}'

    def add_message(self, message):
        self.body = self.body + f'\n {message}'

    def send(self):
        message = MIMEMultipart()
        message["From"] = self.user
        message["To"] = ', '.join(self.receiver)
        message["Subject"] = self.subject

        message.attach(MIMEText(self.body, "plain"))

        with smtplib.SMTP('smtp.gmail.com:587') as server:
            server.ehlo('Gmail')
            server.starttls()
            server.login(self.user, self.password)
            server.sendmail(self.user, self.receiver, message.as_string())