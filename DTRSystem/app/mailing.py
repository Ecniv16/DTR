import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText


#The mail addresses and password

def sent_verification(recieptient_address,data):
    sender_address = 'bdcdtrsystem@gmail.com'
    sender_pass = 'bdc@dtrsys'
    receiver_address = recieptient_address
    #Setup the MIME
    mail_content = """ Dear Mr/Ms.""" + "Vincent" + """
        This message is to verify your Account.
        Your new Password is:""" + "ABC" + """
        Sign in to your Account:http://35.194.125.235:8969/""" 
        



