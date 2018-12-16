import json
import smtplib

from logger import Logger
from email.mime.text import MIMEText

log = Logger()

with open('config.json') as data_file:
    config = json.load(data_file)

smtpUsername = config["email"]["smtpUsername"]
smtpPassword = config["email"]["smtpPassword"]
smtpUrl = config["email"]["smtpUrl"]
smtpPort = config["email"].get("smtpPort") # optional
sender = config["email"]["sender"]
recipient = config["email"]["recipient"]


def send_email(message):
    email = """Nowe zdarzenie: {}""".format(message)

    msg = MIMEText(email, 'plain', 'utf-8')
    msg['Subject'] = "Powiadomienie o zdarzeniu"
    msg['From'] = "Lux Med Monitor<{}>".format(sender)
    msg['To'] = recipient

    try:
        server = smtplib.SMTP(host=smtpUrl, port=smtpPort, timeout=5)
        server.ehlo()
        server.starttls()
        server.set_debuglevel(True)
        server.login(smtpUsername, smtpPassword)
        server.sendmail(sender, recipient, msg.as_string())
        server.quit()
    except Exception as e:
        log.warn("Unable to send email. Error was: {}", e)
