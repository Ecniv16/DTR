from app import *
import requests

from pprint import pprint
import os
import pandas as pd
import json
import hashlib
import numpy_financial as npf
import pymongo
from datetime import datetime as dt
from datetime import timedelta
from dateutil.relativedelta import *
from app.functions import *
from app.variables import *
from bson import ObjectId 
import csv

client = pymongo.MongoClient("mongodb://localhost:27017")
db = client["Monitoring"]

# Normal Reference Insert Update Module
def insert_reference(data,content):
    insert_dict = dict_getter('default_dict')
    for item in data:
        if item != "action":
            insert_dict[item] = data[item]
    try:
        record_count = count_module(f'reference_{content}', {"code":data['code'],"meta.is_deleted":False})
    except:
        record_count = count_module(f'reference_{content}', {"date":data['date'],"meta.is_deleted":False})
        
    if record_count == 0:
        index = int(count_module(f'reference_{content}', {})) +  1
        insert_dict['index'] = index
        result = insert_one_module(f'reference_{content}', insert_dict)
        notification = "New Record was Added!"
    else:
        notification = "Record was Already in the Database!"
    return(notification)

# Update Function Normal Reference
def update_reference(data,content:str,index:int):
    update_dict = db[f'reference_{content}'].find_one({"index":int(index),"meta.is_deleted":False})
    insert_dict = insert_dict = dict_getter('default_dict')
    if 'date' in update_dict:
        applied_date = update_dict['date']
    for item in update_dict:
        try:
            if data[item]:
                update_dict[item] = data[item]
            else:
                update_dict[item] = ''
        except:
            pass
               
    update_dict['meta']['reason_edit'] = data['reason_edit']
    update_dict['meta']['edited_by'] = session['user']  
    update_dict['meta']['date_edited'] =dt.now()
    if content == "schedule_type":     
        if applied_date != data['date']:
            index = int(count_module(f'reference_{content}', {})) +  1
            insert_dict.update(update_dict)
            insert_dict.update({'index':index,'_id':ObjectId()})
            result = insert_one_module(f'reference_{content}', insert_dict)    
            notification = "Record Successfully Updated"
        else:
            x = find_one_module(f'reference_{content}',{'index':int(index),"meta.is_deleted":False},{'_id':0})
            result = db[f'reference_employee_3'].update_many({'schedule_type':x['code']},{"$set":{'schedule_type':update_dict['code']}})            
            result = update_one_module(f'reference_{content}', {"index":int(index),"meta.is_deleted":False} , update_dict) 
            notification = "Record Successfully Updated"
    else:
        x = find_one_module(f'reference_{content}',{'index':int(index),"meta.is_deleted":False},{'_id':0})
        if content == 'company':
            result = db[f'reference_employee_2'].update_many({content:x['code']},{"$set":{content:update_dict['code']}})
        elif content == 'area':
            result = db[f'reference_employee_3'].update_many({content:x['code']},{"$set":{content:update_dict['code']}})
            result = db[f'reference_holiday'].update_many({'location':x['code']},{"$set":{'location':update_dict['code']}})
            result = db[f'reference_location'].update_many({'location':x['code']},{"$set":{'location':update_dict['code']}})        
        elif location == 'location':
            result = db[f'reference_employee_3'].update_many({content:x['code']},{"$set":{content:update_dict['code']}})
        elif content == 'department':
            section_cursor = db[f'reference_section'].find({'department':x['code'],'meta.is_deleted':False},{'_id':0})
            for y in section_cursor:
                result = db[f'reference_employee_2'].update_many({
                    'section':f"{y['department']}-{y['code']}"},{
                    "$set":{'section':f"{update_dict['code']}-{y['code']}","department":update_dict['code']}})
        
            result = db[f'reference_section'].update_many({'department':x['code']},{"$set":{'department':update_dict['code']}})        
        
        
        
        elif content == 'section':
            print(f"{x['department']}-{x['code']}")
            result = db[f'reference_employee_2'].update_many({content:f"{x['department']}-{x['code']}"},{"$set":{content:f"{update_dict['department']}-{update_dict['code']}"}})


        result = update_one_module(f'reference_{content}', {"index":int(index),"meta.is_deleted":False}, update_dict)
        notification = "Record Successfully Updated"        
    return(notification)

# Delete Function Normal Reference

def insert_reference_employee(data,content):
    index = 0
    for x in range(1,6):
        if x == 1:
            insert_dict = dict_getter('default_dict')
            record_count = count_module(f'reference_{content}_1', {"SN":data['SN_1'],"meta.is_deleted":False})
            if record_count == 0:
                index = int(count_module(f'reference_{content}_1', {})) +  1 
                result = insert_one_module(f'reference_{content}_6', {
                    'email':"",
                    'ver_code':"",
                    'verified':"No",
                    'index': index,
                    '_id':ObjectId()
                }) 
                notification = "New Record was Added!"
            else:
                notification = "Record was Already in the Database!"

        else:
            insert_dict = dict_getter('default_dict')

        for item in data:         
            if item != "action":
                if f'{x}' in item:
                    insert_dict[item.replace(f'_{x}','')] = data[item]   
            
        insert_dict['applied'] = "1900-01-01 00:00"
        insert_dict['index'] = index
        insert_dict['_id'] = ObjectId()
        result = insert_one_module(f'reference_{content}_{x}', insert_dict)


    return(notification)                  
       

                        
def update_reference_employee(data,content:str,index:int):
    date_now = dt.now() - timedelta(hours=0, minutes=60)
    date_now = date_now.strftime("%H:%M")
    print(update_dict)
    for x in range(1,6):
 
        if x == 1:
            update_dict = db[f'reference_{content}_1'].find_one({"index":int(index),"meta.is_deleted":False},{"_id":0})
            
            for item in update_dict:
                try:
                    if data[item]:
                        insert_dict[item.replace(f'_{x}','')] = data[item]   
                    else:
                        update_dict[item] = ''
                except:
                    pass

            update_dict['meta']['reason_edit'] = data['reason_edit']
            update_dict['meta']['edited_by'] = session['user']  
            update_dict['meta']['date_edited'] =dt.strftime(dt.now(),'%Y-%m-%d %H:%M')
            result = update_one_module(f'reference_{content}_1', {"index":int(index),"meta.is_deleted":False}, update_dict)    
            notification = "Record Successfully Updated"

        else:
            insert_dict = dict_getter('default_dict')
            update_dict = {'index':int(index)}
            for item in data:         
                if item != "action":
                    if f'{x}' in item and item != "reason_edit" and item != "applied":
                        update_dict[item.replace(f'_{x}','')] = data[item]
                        insert_dict[item.replace(f'_{x}','')] = data[item]                        

            update_dict.update({'applied':data['applied']})
            record_count = db[f'reference_employee_{x}'].count(update_dict)
            if record_count == 0:
                insert_dict['meta']['reason_edit'] = data['reason_edit']
                insert_dict['meta']['edited_by'] = session['user']  
                insert_dict['meta']['date_edited'] =dt.strftime(dt.now(),'%Y-%m-%d %H:%M')                
                insert_dict['applied'] = data['applied'] + " " +date_now
                insert_dict['ref_index'] = int(count_module(f'reference_{content}_{x}', {})) +  1
                insert_dict['index'] = int(index)
                insert_dict['_id'] = ObjectId()
                result = insert_one_module(f'reference_{content}_{x}', insert_dict) 

    return(notification)                            


def upload_reference_employee(data,content):
    file = request.files['file']
    decoded_file = file.read().decode('utf-8-sig').splitlines()
    reader = csv.DictReader(decoded_file)
    for data in reader:
        for x in range(1,6):
            insert_dict = dict_getter('default_dict')            
            if x == 1:
                record_count = count_module(f'reference_{content}_1', {"SN":data['SN_1'],"meta.is_deleted":False})  
                if record_count == 0:                
                    index = int(count_module(f'reference_{content}_1', {})) +  1
                    ref_index = int(count_module(f'reference_{content}_6', {})) +  1 
                    result = insert_one_module(f'reference_{content}_6', {
                        'email':"",
                        'ver_code':"",
                        'verified':"No",
                        'ref_index':ref_index,
                        'index': index,
                        '_id':ObjectId()
                    }) 
                    notification = "New Record was Added!"                    

            if record_count == 0:
                for item in data:    
                        
                    if item != "action":
                        if f'_{x}' in item:    
                                            
                            insert_dict[item.replace(f'_{x}','')] = data_converter(item, data[item])
                        
                insert_dict['applied'] = "1900-01-01 00:00"
                insert_dict['ref_index'] = int(count_module(f'reference_{content}_{x}', {})) +  1
                insert_dict['index'] = index
                insert_dict['_id'] = ObjectId()
                if x == 2:
                    insert_dict['section'] = data['department_2'] + '-'+ data['section_2']
                if x == 3:
                    insert_dict['location'] = data['area_3'] + '-'+ data['location_3']       
                if x == 4:
                    insert_dict['user'] = data['employee_id_1']
                    insert_dict['password'] = 'bdc@' + data['employee_id_1']
                    
                result = insert_one_module(f'reference_{content}_{x}', insert_dict) 
                
def update_login_details(data):
    update_dict = db['reference_employee_4'].find_one({"index":session['index'],"meta.is_deleted":False})

    for item in update_dict:
        try:
            if data[item]:
                update_dict[item] = data[item]
            else:
                update_dict[item] = ''
        except:
            pass
    update_dict['password'] = hashlib.sha1(data['password'].encode('utf-8')).hexdigest()           
    update_dict['meta']['edited_by'] = session['user']  
    update_dict['meta']['date_edited'] =dt.now()
    update_dict['applied'] = dt.strftime(dt.now(),'%Y-%m-%d %H:%M')
    update_dict['_id'] = ObjectId()
    result = insert_one_module(f'reference_employee_4', update_dict)    
    notification = "Record Successfully Updated"
   
    return(notification)





def insert_reference_leave_credit(data,index):

    date_now = dt.now() - timedelta(hours=0, minutes=60)
    time_now = date_now.strftime("%H:%M")   
    insert_dict = dict_getter('default_dict')
    update_dict = {}
    for item in data:
        if item not in ['action','reason_edit','applied','ref_index']:
            update_dict[item] = float(data[item])
    ref_index = int(count_module(f'reference_leave_credit', {})) +  1
    insert_dict.update(update_dict)
    insert_dict['applied'] = f"{data['applied']} {time_now}"
    insert_dict['ref_index'] = ref_index
    insert_dict['index'] = int(index)

    if int(data['ref_index']) == 0:    
        result = insert_one_module(f'reference_leave_credit', insert_dict)
    else:
        find_rec = find_one_module('reference_leave_credit',{'ref_index':int(data['ref_index'])},{'_id':0,'applied':1})
        if find_rec['applied'][:10] == data['applied']:
            update_dict.update({'meta.reason_edit':data['reason_edit']})
            result = update_one_module(f'reference_leave_credit',{'ref_index':int(data['ref_index'])},update_dict)
        else:
            result = insert_one_module(f'reference_leave_credit', insert_dict)

       
    notification = "New Record was Updated!"

    return(notification)


def delete_reference(data,content,index):
    if '3' in content or '2' in content or 'leave_credit' in content:    
        update_dict = db[f'reference_{content}'].find_one({"ref_index":int(index),"meta.is_deleted":False},{"meta":1,"_id":0})
    else:
        update_dict = db[f'reference_{content}'].find_one({"index":int(index),"meta.is_deleted":False},{"meta":1,"_id":0})

    update_dict['meta']['reason_delete'] = data['reason_delete']
    update_dict['meta']['deleted_by'] = session['user']
    update_dict['meta']['date_deleted'] =dt.now()
    update_dict['meta']['is_deleted'] =True
    if '3' in content or '2' in content or 'leave_credit' in content:    
        result = update_one_module(f'reference_{content}', {"ref_index":int(index),"meta.is_deleted":False}, update_dict)    
    else:
        result = update_one_module(f'reference_{content}', {"index":int(index),"meta.is_deleted":False}, update_dict)
          
    notification = "Record Successfully Deleted"
    return(notification)


def upload_leave_credit(data):
    file = request.files['file']
    decoded_file = file.read().decode('utf-8-sig').splitlines()
    reader = csv.DictReader(decoded_file)
    for data in reader:

        insert_dict = dict_getter('default_dict')            

        find_rec = find_one_module(f'reference_employee_1',  {"SN":data['SN_1'],"meta.is_deleted":False},{'index':1,'_id':0})  
        if find_rec:                
            index = find_rec['index']
            leave_credit_rec = find_one_module('reference_leave_credit',{'index':index,'meta.is_deleted':False,'applied':f"{convert_nan_to_date(data['applied'])} 00:00"}, {'meta':0,'_id':0,'index':0})
            if not leave_credit_rec:
                for item in data:
                    if '_1' not in item and not item == 'applied':
                        insert_dict[item] = convert_nan_to_zero(data_converter(item, data[item]))
                    elif item == 'applied':
                        applied_date = convert_nan_to_date(data['applied'])
                        insert_dict[item] = f"{applied_date} 00:00"

                insert_dict['ref_index'] = int(count_module(f'reference_leave_credit', {})) +  1
                insert_dict['index'] = index
                insert_dict['_id'] = ObjectId()                        

                result = insert_one_module(f'reference_leave_credit', insert_dict)                     


    return('Uploading Done')
                    
