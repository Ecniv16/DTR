from app import *
import requests

from pprint import pprint
import os
import pandas as pd
import json

import numpy_financial as npf
import pymongo
from datetime import datetime as dt
from datetime import timedelta
from dateutil.relativedelta import *
from app.functions import *
from app.variables import *
from bson import ObjectId 
import random
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from mega import Mega


client = pymongo.MongoClient("mongodb://localhost:27017")
db = client["Monitoring"]


def sent_verification(content,data):
    sender_address = 'bdcdtrsystem@gmail.com'
    sender_pass = 'bdc@dtrsys'
    receiver_address = content['receiver']
    #Setup the MIME
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


def random_with_N_digits(n):
    range_start = 10**(n-1)
    range_end = (10**n)-1
    return random.randint(range_start, range_end)


def find_email(email):
	x = find_one_module('reference_employee_6', {'email':email},{"_id":0})
	if x:
		return(1)
	return(0)


def link_email(data):
	dict_list = ""
	today_date = date_time_now()
	date_now = today_date['date_now']
	time_now = today_date['time_now']
	date_now = today_date['date_now']
	query = {
		"user":data["user"]
		,"password":data["password"],
		"meta.is_deleted":False
		}
	dict_list = find_one_module("reference_employee_4", query, reference_remove_dict)
	ver_code = random_with_N_digits(6)
	update_dict = db.reference_employee_6.update_one({"index":dict_list['index']},{"$set":{
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
		"user":data["user"],
		"password":data["password"],
		"meta.is_deleted":False
		}
	validation1 = find_one_module("reference_employee_4", query, reference_remove_dict)
	if validation1:		
		query2 = {
			"email":data['email'],
			"ver_code":data["ver_code"],
			"index": validation1['index']

			}
		validation2 = find_one_module("reference_employee_6",query2, reference_remove_dict)
		if validation2:
			content = {
				"receiver":data['email'],
				"subject":"DTR SYSTEM: ACCOUNTS VERIFIED",
				"message": """Congratulations your account has been verified"""
			}
			sent_verification(content, data)		
			db.reference_employee_6.update_one(query2,{"$set":{"verified":"Yes"}})
			return("1")
		else:
			return("2")