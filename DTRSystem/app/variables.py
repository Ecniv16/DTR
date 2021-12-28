from app import *
from app.templates.utilities.controller import * 
from app.controller import * 
from pprint import pprint
import os
import pandas as pd
import json

import numpy_financial as npf
import pymongo
from datetime import datetime as dt
from datetime import timedelta
from dateutil.relativedelta import *
from mega import Mega
from bson import ObjectId 
from .functions import *

client = pymongo.MongoClient("mongodb://localhost:27017")
db = client["Monitoring"]

reference_remove_dict = {
	"is_deleted":0,
	"deleted_by":0,
	"date_deleted":0,
	"reason_delete": 0,
	"reason_edit":0,
	"edited_by":0,
	"date_edited":0,
	"date_now":0,
	"time_now":0,
	"encoded_by":0
}


report_remove_dict = {
	"_id":0,
	"is_deleted":0,
	"deleted_by":0,
	"date_deleted":0,
	"reason_delete": 0,
	"reason_edit":0,
	"edited_by":0,
	"date_edited":0,
	"date_now":0,
	"time_now":0,
	"encoded_by":0,
	"user":0,
	"password":0,
}




audit_trail_list = {
	"is_deleted": False,
	"date_now": "",
	"time_now": "",
	"date_deleted": "",
	"deleted_by":"",
	"edited_by":"",
	"date_edited":"",
	"reason_delete":"",
	"reason_edit":"",
	"encoded_by":"",	
}


employee_field_name = [
	'employee_id',
	'SN',
	'first_name',
	'middle_name',
	'last_name',
	'suffix',
	'company',
	'department',
	'section',
	'branch',
	'location',
	'user_type',
	'user',
	'password',
	'schedule_type',
	'is_flexi',
	'date_hired',
	'position',
	"is_perfect_attendance"
]

leave_field_name = [
	'SL',
	'VL',
	'BL',
	'SP',
	'BRL',
	'ML',
	'PL',
	'MC',
	'VS'
	]

leave_field_name_2 = [
	'SL',
	'VL',
	'BL',
	'SP',
	'BRL',
	'ML',
	'PL',
	'MC',
	'VS',
	'SL_r',
	'VL_r',
	'BL_r',
	'SP_r',
	'BRL_r',
	'ML_r',
	'PL_r',
	'MC_r',
	'VS_r'	
	]


def dict_getter(collection):
	date_now = dt.now() - timedelta(hours=0, minutes=60)
	date_now = date_now.strftime("%m/%d/%Y")
	time_now = dt.now() - timedelta(hours=0, minutes=60)
	full_time = dt.now()
	
	dict_list = {}
	dict_list['default_dict'] = {
		'meta':{
			"is_deleted":False,
			"deleted_by":"",
			"date_deleted":"",
			"reason_delete": "",
			"reason_edit":"",
			"edited_by":"",
			"date_edited":"",
			"date_now":date_now,
			"time_now":time_now,
			"encoded_by":session['user'],
		},
		'_id':ObjectId()		
	}	
	dict_list['utilities_leave_application'] = {
		"date_filed":"",
		"leave_type":"",
		"date_from":"",
		"date_to":"",
		"resume":"",
		"reason":"",
		"days_of_leave":"",		
		"from_vl":"",
		"no_hours":"",
		"paid":"",
		"not_paid":"",
		"index": "",
		"_id": ObjectId()		
	}

	dict_list['utilities_leave_application_draft'] = {
		"date_filed":"",
		"leave_type":"",
		"date_from":"",
		"date_to":"",
		"resume":"",
		"reason":"",
		"days_of_leave":"",		
		"ref_index":session['index'],
		"from_vl":"",
		"no_hrs":"",
		"index": "",
		"_id": ObjectId()		
	}


	dict_list['standard_dict'] = {
		'meta':{
			"is_deleted":False,
			"deleted_by":"",
			"date_deleted":"",
			"reason_delete": "",
			"reason_edit":"",
			"edited_by":"",
			"date_edited":"",
			"date_now":date_now,
			"time_now":time_now,
			"encoded_by":session['user'],
		},
		'basic_info':{
			"supervisor_remarks_1":"",
			'supervisor_remarks_2':"",
			"dm_remarks_1":"",
			"dm_remarks_2":"",
			"status":"For SV/SSV's Approval",
			"supervisor_name":session['immediate_supervisor'],
			"dm_name":session['department_head'],
			"remarks_date":"",
			"effective_start":"",
			"effective_end":"",
			"attachment":"",
			"ref_index":session['index'],
			"SN":session['SN'],
			"employee_id":session['employee_id'],
			"name":session['user'],
			"dept_sec":session['department'] +"/"+ session['section'],
			"designation":session['position'],		

		}
		
	}
	dict_list['default_leave_credit'] = {
		'SL': 0,
		'SL_r':0,
		'VL':0,
		'VL_r':0,
		'BL':0,
		'BL_r':0,
		'BRL':0,
		'BRL_r':0,
		'PL':0,
		'PL_r':0,
		'SP':0,
		'SP_r':0,
		'ML':0,
		'ML_r':0,
		'VS':0,
		'VS_r':0,
		'MC':0,
		'MC_r':0,
	}
	return(dict_list[collection])