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

client = pymongo.MongoClient("mongodb://localhost:27017")
db = client["Monitoring"]

def get_reference_data():
	set_data = []
	dict_list = {}
	user_type = db.reference_user_type.find_one({"reference_code":session['user_type']},{"ranking":1,"_id":0})
	user_type_cursor = db.reference_user_type.find({},{"_id":0}).sort("ranking")
	for x in user_type_cursor:
		x_data = dict(x)
		if int(x_data['ranking']) >= user_type['ranking']:
			set_data.append(x_data)
	dict_list['reference_user_type'] = set_data
	
	set_data=[]
	index_list = {
	"employee_id" :1,"index" : 1,"SN" :1,"first_name" :1,"middle_name" :1,
	"last_name" :1,"suffix" :1,"company" :1,"department" :1,"section" :1,
	"branch" :1,"location" :1,"user_type" :1,"user" :1,"password" :1,
	"schedule_type" :1, "is_flexi" :1,"date_hired" :1,"_id":0,"slvl_total":1,"slvl_remaining":1
	}

	#EMPLOYEE

	if session["user_type"] == "Administrator":
		cursor =  db.reference_employee.find({"is_deleted":False},index_list).sort("last_name")
		
	elif session["user_type"] == "Supervisor":
		cursor =  db.reference_employee.find({"is_deleted":False,"department":session["department"],"section":session["section"]},index_list).sort("last_name")
	elif session["user_type"] == "Department Head":
		cursor =  db.reference_employee.find({"is_deleted":False,"department":session["department"]},index_list).sort("last_name")
	else:
		cursor =  db.reference_employee.find({"_id":ObjectId(session["_id"])})
	set_data =[]
	for item in cursor:
		set_data.append(dict(item))
	dict_list['reference_employee'] = set_data
	
	#BRANCH

	if session["user_type"] == "Administrator":
		cursor =  db.reference_branch.find({"is_deleted":False},{"_id":0}).sort("reference_code")
	else:
		cursor =  db.reference_branch.find({"is_deleted":False,"reference_code":session["branch"]},common_dict)
	
	set_data =[]
	for item in cursor:
		set_data.append(dict(item))
	dict_list['reference_branch'] = set_data	

	#Company
	if session["user_type"] == "Administrator":
		cursor =  db.reference_company.find({"is_deleted":False},{"_id":0}).sort("reference_code")
	else:
		cursor =  db.reference_company.find({"is_deleted":False,"reference_code":session["company"]},
			common_dict)

	set_data =[]
	for item in cursor:
		set_data.append(dict(item))
	dict_list['reference_company'] = set_data

	#Department
	if session["user_type"] == "Administrator":
		cursor =  db.reference_department.find({"is_deleted":False},{"_id":0}).sort("reference_code")
	else:
		cursor =  db.reference_department.find({"is_deleted":False,"reference_code":session["department"]},
			common_dict)

	set_data =[]
	for item in cursor:
		set_data.append(dict(item))
	dict_list['reference_department'] = set_data

	#Location
	if session["user_type"] == "Administrator":
		cursor =  db.reference_location.find({"is_deleted":False},
			{"_id":0}).sort("reference_code")
	else:
		cursor =  db.reference_location.find({"is_deleted":False,
			"reference_code":session["location"]},
			common_dict)

	set_data =[]
	for item in cursor:
		set_data.append(dict(item))
	dict_list['reference_location'] = set_data


	#Section
	if session["user_type"] == "Administrator":
		cursor =  db.reference_section.find({"is_deleted":False},
			{"_id":0}).sort("reference_code")
	elif session["user_type"] == "Department Head":
		cursor =  db.reference_section.find({"is_deleted":False,
			"reference_link":session['department']},
			{"_id":0}).sort("reference_code")
			
	else:
		cursor =  db.reference_section.find({"is_deleted":False,
			"reference_code":session["section"]},
			common_dict)

	set_data =[]
	for item in cursor:
		set_data.append(dict(item))
	dict_list['reference_section'] = set_data

	#Schedule_Type
	if session["user_type"] == "Administrator" or session['user_type'] =="Department Head":
		cursor =  db.reference_schedule_type.find({"is_deleted":False},{"_id":0}).sort("reference_code")
	else:
		cursor =  db.reference_schedule_type.find({"is_deleted":False,"reference_code":session["schedule_type"]},
			{"_id":0})

	set_data =[]
	for item in cursor:
		set_data.append(dict(item))
	dict_list['reference_schedule_type'] = set_data

	#is_flexi
	if session["user_type"] == "Administrator":
		cursor =  db.reference_is_flexi.find({"is_deleted":False},{"_id":0}).sort("reference_code")
	else:
		cursor =  db.reference_is_flexi.find({"is_deleted":False,"reference_code":session["is_flexi"]},
			{"_id":0})

	set_data =[]
	for item in cursor:
		set_data.append(dict(item))
	dict_list['reference_is_flexi'] = set_data



	return(dict_list)






def selected_employee(data):
	set_data =[]
	start_date = dt.strptime(data["date_from"],"%Y-%m-%d")
	end_date  = dt.strptime(data["date_to"],"%Y-%m-%d")
	start_now = start_date.strftime("%m/%d/%Y")	
	end_now = end_date.strftime("%m/%d/%Y")	
	if data["index"] == "ALL":
		if session["user_type"] == "Administrator":
			if data['department'] == "ALL":
				dict_crit = {
				"is_deleted":False
				}
			else:
				dict_crit = {
				"is_deleted":False,
				"department":data["department"]
				}

		elif session["user_type"] == "Department Head":
			dict_crit = {
			"is_deleted":False,
			"department":session["department"]
			}			
		elif session["user_type"] == "Supervisor":
			dict_crit = {
			"is_deleted":False,
			"department":session["department"],
			"section":session["section"],
			}
		else:
			dict_crit = {
			"is_deleted":False,
			"index":int(data["index"])
			}				
	else:
		dict_crit = {
			"is_deleted":False,
			"index":int(data["index"])
		}			


	cursor = db.reference_employee.find(dict_crit).sort("last_name")
	for item in cursor:
		x = dict(item)
		x["cutoff"] = start_now + " - " + end_now
		x["start_date"] = start_now
		x["end_date"] = end_now

		set_data.append(x)
	return(set_data)
