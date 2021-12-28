from app import *
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

def sent_verification(content,data):
    sender_address = 'bdcdtrsystem@gmail.com'
    sender_pass = 'bdc@dtrsys'
    receiver_address = content['receiver']
    mail_content = content['message']
    message = MIMEMultipart()
    message['From'] = sender_address
    message['To'] = receiver_address
    message['Subject'] = content['subject']
    message.attach(MIMEText(mail_content, 'plain'))
    session = smtplib.SMTP('smtp.gmail.com', 587)
    session.starttls() 
    session.login(sender_address, sender_pass)
    text = message.as_string()
    session.sendmail(sender_address, receiver_address, text)
    session.quit()


def link_email(data):
	dict_list = ""
	today_date = date_time_now()
	date_now = today_date['date_now']
	time_now = today_date['time_now']
	date_now = today_date['date_now']
	query = {
		"user":data["user"]
		,"password":data["password"],
		"is_deleted":False
		}
	dict_list = find_one_module("reference_employee", query, reference_remove_dict)
	ver_code = random_with_N_digits(6)
	update_dict = db.reference_employee.update_one(query,{"$set":{
		"email":data['email'],
		"ver_code":str(ver_code),
		"verified":"No"
		}})

	content = {
		"receiver":data['email'],
		"subject":"DTR SYSTEM: VERIFICATION CODE",
		"message": """EMAIL VERIFICATION CODE:""" + str(ver_code)

	}
	sent_verification(content, data)
	return()

def register_email(data):
	dict_list = ""
	today_date = date_time_now()
	date_now = today_date['date_now']
	time_now = today_date['time_now']
	date_now = today_date['date_now']
	query = {
		"email":data['email'],
		"user":data["user"],
		"password":data["password"],
		"ver_code":data["ver_code"],
		"is_deleted":False
		}

	dict_list = find_one_module("reference_employee", query, reference_remove_dict)
	if dict_list:
		content = {
			"receiver":data['email'],
			"subject":"DTR SYSTEM: ACCOUNTS VERIFIED",
			"message": """Congratulations your account has been verified"""
		}
		sent_verification(content, data)		
		db.reference_employee.update_one(query,{"$set":{"verified":"Yes"}})
		return("1")
	else:
		return("2")