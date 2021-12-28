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

client = pymongo.MongoClient("mongodb://localhost:27017")
db = client["Monitoring"]
def get_reference_data():
	set_data = []
	dict_list = {}
	dict_list['reference_month'] = list(db.reference_month.find({"is_deleted":False}))	
	dict_list['reference_cutoff'] = list(db.reference_cutoff.find({"is_deleted":False}))	


	return(dict_list)

def display_leave_form(index):
	set_data=[]
	dict_list={}
	leave_dict = db.utilities_leave_application.find_one({"meta.is_deleted":False,"index":int(index)})
	index_list = {"index":1,"last_name":1,"first_name":1,"middle_name":1,"_id":0}
	if session["user_type"] == "Administrator":
		cursor =  db.reference_employee.find({"is_deleted":False,"index":int(leave_dict['basic_info']['ref_index'])},index_list).count()		
	elif session["user_type"] == "Supervisor" or session['user_type'] =="Senior Supervisor":
		cursor =  db.reference_employee.find({"is_deleted":False,"index":int(leave_dict['basic_info']['ref_index']),"department":session["department"],"section":session["section"]},index_list).count()
	elif session["user_type"] == "Department Head":
		cursor =  db.reference_employee.find({"is_deleted":False,"index":int(leave_dict['basic_info']['ref_index']),"department":session["department"]},index_list).count()
	else:
		cursor =  db.reference_employee.find({"index":int(session["index"])}).count()


	if cursor ==0:
		set_data = []

	else:
		x = db.reference_leave.find_one({'reference_code':leave_dict['leave_type']},{'_id':0,'reference_name':1})
		leave_dict['leave_name'] = x['reference_name']
		leave_dict['ref_index'] = int(leave_dict['basic_info']["ref_index"])

		details = db.utilities_leave_detail.find({"ref_index":leave_dict['index']})
		paid_count = 0
		not_paid_count = 0
		for deets in details:
			paid_count += deets['hours_paid']
			not_paid_count += deets['hours_not_paid']

		leave_dict.update({
			"not_paid_count":not_paid_count,
			"paid_count": paid_count})
		
		set_data.append(leave_dict)

		
	dict_list['leave_form'] = set_data

	set_data = []
	cursor = db.leave_attachment.find({'is_deleted':False,'file_index':int(index)})

	for x in cursor:
		set_data.append(dict(x))
	dict_list['leave_attachment'] = set_data
	









	count = db.leave_attachment.find({'is_deleted':False,'file_index':int(index)}).count()
	dict_list['leave_attachment_count'] = count




	return(dict_list)





