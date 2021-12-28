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
from bson import ObjectId 
from app.variables import dict_getter as dg
import random


client = pymongo.MongoClient("mongodb://localhost:27017")
db = client["Monitoring"]
message = ''

remove_dict = dg('remove_dict')


def end_user_login(data):
	employee_dict = ""
	query = {
		"user":data["user"]
		,"password":data["password"],
		"is_deleted":False
		}
	employee_dict = db['reference_employee'].find(query,remove_dict)

	if employee_dict:
		try:
			if employee_dict['verified'] == "No":
				return("No Email address link to this account")	

		except:
			return("No Email address link to this account")	
		for item in employee_dict:
			if item == "_id":
				session[item] = str(employee_dict[item])

			else:			
				session[item] = employee_dict[item]

		trans = get_employee_record(int(session['index']))
		session['branch'] = trans['branch']
		session['location'] = trans['location']				

		session["user"] = session["last_name"] + ", " + session["first_name"]	+ " " + session["middle_name"] + ". " + session["suffix"]			
		session['login_name'] = employee_dict['user']
		session['employee_id'] = employee_dict['employee_id'].zfill(6)	


		return("Success")

	return("")


