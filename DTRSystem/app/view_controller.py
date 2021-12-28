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

def display_reference(content) -> list:
    if content == "schedule_type":
        set_data = []
        code = db.reference_schedule_type.distinct('code')
        for x in code:
            set_data.append(find_last_module(f'reference_{content}',{"code":x,"meta.is_deleted":False} , {"meta":0,"_id":0}))
        return(set_data)
    else:
        return(list(db[f'reference_{content}'].find({"meta.is_deleted":False},{"meta":0,"_id":0})))

def display_archive_reference(content) -> list:
    set_data =[]
    code = db.reference_schedule_type.distinct('code')
    for x in code:
        latest = find_last_module(f'reference_{content}',{"code":x,"meta.is_deleted":False} , {"meta":0,"_id":0})

        for item in find_module(f'reference_{content}', {"code":x,"meta.is_deleted":False,"date":{"$ne":latest['date']}}, {"meta":0,"_id":0}):
            set_data.append(item)
    return(set_data)




def display_reference_detail(content,index:int) -> dict:
    return(db[f'reference_{content}'].find_one({"meta.is_deleted":False,"index":int(index)},{"meta":0,"_id":0}))

def display_reference_employee_detail(content,index:int) -> dict:
    display_dict = find_last_module('reference_employee_1', {"index":int(index)}, {"meta":0,"_id":0})
    display_dict.update(find_last_module('reference_employee_2', {"index":int(index)}, {"meta":0,"_id":0,"index":0,'applied':0}))
    display_dict.update(find_last_module('reference_employee_3', {"index":int(index)}, {"meta":0,"_id":0,"index":0,'applied':0}))
    display_dict.update(find_last_module('reference_employee_4', {"index":int(index)}, {"meta":0,"_id":0,"index":0,'applied':0}))
    display_dict.update(find_last_module('reference_employee_5', {"index":int(index)}, {"meta":0,"_id":0,"index":0,'applied':0}))
    display_dict.update(find_last_module('reference_employee_6', {"index":int(index)}, {"meta":0,"_id":0,"index":0,'applied':0}))
    return(display_dict)

def display_employee_record_detail(content,ref_index:int) -> dict:
    x = db[f'reference_{content}'].find_one({"meta.is_deleted":False,"ref_index":int(ref_index)},{"meta":0,"_id":0})
    employee_info = db[f'reference_employee_1'].find_one({'index':x['index'],'meta.is_deleted':False},{'meta':0,'_id':0})
    x.update({
        'employee_id': employee_info['employee_id'],
        'SN': employee_info['SN'],
        'name': f"{employee_info['last_name']}, {employee_info['first_name']} {employee_info['middle_name']}. {employee_info['suffix']}"
    })

    return(x)

def display_reference_employee():
    set_data = []
    cursor = db['reference_employee_1'].find({"meta.is_deleted":False},{"meta":0,"_id":0}).sort('last_name')
    for x in cursor:
        x.update(find_last_module('reference_employee_2', {"index":int(x['index'])}, {"_id":0,"index":0}))
        x.update(find_last_module('reference_employee_3', {"index":int(x['index'])}, {"meta":0,"_id":0,"index":0,'applied':0}))
        x.update(find_last_module('reference_employee_4', {"index":int(x['index'])}, {"meta":0,"_id":0,"index":0,'applied':0}))
        x.update(find_last_module('reference_employee_5', {"index":int(x['index'])}, {"meta":0,"_id":0,"index":0,'applied':0}))
        x.update(find_last_module('reference_employee_6', {"index":int(x['index'])}, {"meta":0,"_id":0,"index":0,'applied':0}))
        set_data.append(x)

    return(set_data)


def display_reference_employee_record():
    set_data = []
    cursor = db['reference_employee_1'].find({"meta.is_deleted":False},{"meta":0,"_id":0,"applied":0}).sort('last_name')
    dict_list = {}
    designation_data = []
    sched_loc_data = []
    superior_data = []          
    for x in cursor:
        designation_cursor = db['reference_employee_2'].find({"meta.is_deleted":False,"index":x['index']},{'_id':0}).sort('applied',-1)
        sched_loc_cursor = db['reference_employee_3'].find({"meta.is_deleted":False,"index":x['index']},{'_id':0}).sort('applied',-1)
        
        employee_detail  = {
            'employee_id': x['employee_id'],
            'SN': x['SN'],
            'name': f"{x['last_name']}, {x['first_name']} {x['middle_name']}. {x['suffix']}"
        }
        if count_module('reference_employee_2', {"meta.is_deleted":False,"index":x['index']}) > 1:        
            for designation in designation_cursor:
                if count_module('reference_employee_2', {"meta.is_deleted":False,"index":x['index']}) > 1:
                    designation.update(employee_detail)      
                    designation_data.append(designation)

        if count_module('reference_employee_3', {"meta.is_deleted":False,"index":x['index']}) > 1:

            for sched_loc in sched_loc_cursor: 
                sched_loc.update(employee_detail)
                sched_loc_data.append(sched_loc)

    dict_list['designation'] = designation_data
    dict_list['sched_loc'] = sched_loc_data

    return(dict_list)


def get_employee_list(query)->dict:

    x = db['reference_employee_1'].find_one(query,{"meta":0,"_id":0})
    x.update(find_last_module('reference_employee_2', {"index":int(x['index'])}, {"meta":0,"_id":0,"index":0}))
    x.update(find_last_module('reference_employee_3', {"index":int(x['index'])}, {"meta":0,"_id":0,"index":0,'applied':0}))
    x.update(find_last_module('reference_employee_4', {"index":int(x['index'])}, {"meta":0,"_id":0,"index":0,'applied':0}))
    x.update(find_last_module('reference_employee_5', {"index":int(x['index'])}, {"meta":0,"_id":0,"index":0,'applied':0}))
    x.update(find_last_module('reference_employee_6', {"index":int(x['index'])}, {"meta":0,"_id":0,"index":0,'applied':0}))


    return(x)    

def get_employee_name(SN:str):
    dict_list = find_one_module('reference_employee_1',{"SN":SN,"meta.is_deleted":False},{"_id":0,"meta":0})
    name = "N/A"
    if str(SN) != '#N/A' and str(SN) != 'N/A':
        name = f'{dict_list["last_name"]}, {dict_list["first_name"]} {dict_list["middle_name"]}. {dict_list["suffix"]}'
    return(name)


def get_employee_list_for_report(query) -> list:
    set_data = []
    dict_list = {}

    if session['user_type'] == "Administrator":
        cursor = list(db['reference_employee_2'].find(query,{"meta":0,"_id":0}))
    else:
        cursor = list(db['reference_employee_5'].find(query,{"meta":0,"_id":0}))
    
def get_employee_leave_credit() ->list:
    set_data = []
    dict_list = {}
    cursor = find_module_sorted('reference_employee_1',{'meta.is_deleted':False},{'meta':0,'_id':0,'applied':0,'ref_index':0},'last_name',1)
    for item in cursor:
        # cred = find_last_module('reference_leave_credit', {'meta.is_deleted':False,'index':item['index']}, {'meta':0,'_id':0,'index':0})
        cred = get_applicable_record_now('reference_leave_credit', item['index'], {'meta':0,'_id':0,'index':0},'')
        if cred:
            item.update(cred)
        else:
            item.update(dict_getter('default_leave_credit'))
            item.update({
                'ref_index':0,
                'applied':"1900-01-01 00:00"[:10]})            
        set_data.append(item)
    return(set_data)

def get_employee_leave_credit_detail(index:int) ->list:
    set_data = []
    dict_list = {}
    cursor = find_module_sorted('reference_employee_1',{'meta.is_deleted':False,'index':int(index)},{'meta':0,'_id':0,'applied':0,'ref_index':0},'last_name',1)
    for item in cursor:
        # cred = find_last_module('reference_leave_credit', {'meta.is_deleted':False,'index':item['index']}, {'meta':0,'_id':0,'index':0})
        cred = get_applicable_record_now('reference_leave_credit', index, {'meta':0,'_id':0,'index':0},'')
        if cred:
            item.update(cred)
            item.update({'applied':item['applied'][:10]})
        else:
            item.update(dict_getter('default_leave_credit'))
            item.update({
                'ref_index':0,
                'applied':"1900-01-01 00:00"[:10]})
        
        set_data.append(item)
    return(set_data)

def get_employee_detail(category): #category : 5 for employee superiors, 6 for employee email address
    date_now = dt.now()
    date_now = dt.strptime(date_now.strftime("%Y-%m-%d"),"%Y-%m-%d")   
    set_data = []
    dict_list = {}
    cursor = find_module_sorted('reference_employee_1', {'meta.is_deleted':False}, {'meta':0,'_id':0},'last_name',1)
    for item in cursor:
        x = get_applicable_record_now('reference_employee_2', item['index'], {'meta':0,'index':0,'ref_index':0,'_id':0}, date_now)
        if category != 6:
            z = get_applicable_record_now(f'reference_employee_{category}', item['index'], {'meta':0,'index':0,'_id':0}, date_now)
        else:
            z = find_one_module(f'reference_employee_{category}', {'index':item['index']}, {'_id':0}) 

        if category == 5:
            z['immediate_supervisor'] = get_employee_name(z['immediate_supervisor'])
            z['department_head'] = get_employee_name(z['department_head'])

        item.update(x)
        item.update(z)

        set_data.append(item)

    return(set_data) 

def admin_dashboard():
    dict_list = {}
    dict_list['employee'] = count_module('reference_employee_1',{'meta.is_deleted':False})
    dict_list['area'] = len(db.reference_schedule_type.distinct('code',{'meta.is_deleted':False}))
    dict_list['company'] = len(db.reference_company.distinct('code',{'meta.is_deleted':False}))
    return(dict_list)   