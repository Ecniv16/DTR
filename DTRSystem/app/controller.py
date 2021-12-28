from app import *

import pandas as pd


import pymongo
from datetime import datetime as dt
from datetime import timedelta
from dateutil.relativedelta import *
# from app.functions import *
from . import functions
from . import variables
# from app.variables import *
from app.view_controller import *
from bson import ObjectId
import random
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText


# The mail addresses and password

client = pymongo.MongoClient("mongodb://localhost:27017")
db = client["Monitoring"]
message = ''
common_dict = {
    "reference_code": 1, "reference_name": 1, "reference_link": 1,
    "index": 1, "_id": 0, "reference_address": 1, "reference_contact": 1,
    "reference_eadd": 1
}


# uSER lOGIN
def end_user_login(data):
    employee_dict = ""
    query = {
        "user": data["user"], "password": data["password"],
        "meta.is_deleted": False
    }
    get_user = find_one_module(
        "reference_employee_4", query, {"meta": 0, '_id': 0})

    if get_user:
        col_use = 'reference_employee_4'
        query_use = {'index': get_user['index'], "meta.is_deleted": False}
        record_count = count_module(col_use, query_use)
        cover_query = {'meta': 0, '_id': 0}
        if record_count > 1:
            latest_cred = find_last_module(col_use, query_use, cover_query)

            if not(latest_cred['user'] == query['user'] and latest_cred['password'] == query['password']):
                return('Please Use the updated username and password')

        employee_dict = find_one_module("reference_employee_6", {
                                        "index": get_user['index']}, {"meta": 0, '_id': 0})
        if 'verified' not in employee_dict or employee_dict['verified'] == "No":
            return("No Email address link to this account")

        dict_list = display_reference_employee_detail(
            'employee', get_user['index'])

        for x in dict_list:
            session[x] = dict_list[x]

        session["index"] = dict_list['index']
        session["user"] = dict_list["last_name"] + ", " + dict_list["first_name"] + \
            " " + dict_list["middle_name"] + ". " + dict_list["suffix"]
        session['login_name'] = dict_list['user']
        session['employee_id'] = dict_list['employee_id'].zfill(6)
        session['post_count'] = 0

        return("Success")

    return("")


def google_login(email):
    employee_dict = find_one_module("reference_employee_6", {
                                    "email": email, "verified": "Yes"}, {"meta": 0, '_id': 0})
    dict_list = display_reference_employee_detail(
        'employee', employee_dict['index'])
    for x in dict_list:
        session[x] = dict_list[x]

    session["index"] = dict_list['index']

    session["user"] = f"{dict_list['last_name']}, {dict_list['first_name']} {dict_list['middle_name']}. {dict_list['suffix']}"
    session['login_name'] = dict_list['user']
    session['employee_id'] = dict_list['employee_id'].zfill(6)
    session['post_count'] = 0
    return("Success")


def upload_dtr(data):
    date_now = dt.now() - timedelta(hours=0, minutes=60)
    date_now = date_now.strftime("%m/%d/%Y")
    time_now = dt.now() - timedelta(hours=0, minutes=60)
    full_time = dt.now()
    time_now = time_now.strftime("%H:%M")
    x_field = ['AM_IN', 'AM_OUT', 'PM_IN', 'PM_OUT', 'OT_IN', 'OT_OUT']
    uploaded_file = request.files['file']
    uploaded_file.save(os.path.join(
        FILES_DIR, uploaded_file.filename))
    path_open = str(os.path.join(
        FILES_DIR, uploaded_file.filename))
    field_name = ["date", "AM_IN", "PM_IN",
                  "OT_IN", "AM_OUT", "PM_OUT",
                  "OT_OUT", "SN"]
    csvData = pd.read_csv(r'' + path_open, encoding="ISO-8859-1")
    dict_list = {}
    for i, row in csvData.iterrows():

        for item in field_name:
            data_row = row[item]
            if item == "date":
                dict_list[item] = data_converter(item, data_row)
            else:
                dict_list[item] = convert_nan_to_string(data_row)

        start_date = dt.strptime(dict_list["date"], "%Y-%m-%d")
        SN = db['reference_employee_1'].find_one(
            {"SN": dict_list["SN"], "meta.is_deleted": False})
        if SN:
            record = get_latest_record(start_date, SN['index'])
            record_value(x_field, record, start_date, full_time, dict_list)
    set_data = []
    cursor = list(db.attendance_record.find({"full_time": full_time}))
    for rec in cursor:
        set_data.append(rec)
    return(set_data)


def record_value(x_field, record, start_date, full_time, dict_list):

    first_in, last_out = "", ""
    dict_list['_id'] = ObjectId()
    dict_list['name'] = f"{record['last_name']}, {record['first_name']} {record['middle_name']}. {record['suffix']}"
    dict_list["section"] = record["section"]
    dict_list["employee_id"] = record["employee_id"]
    dict_list['date'] = start_date.strftime("%Y-%m-%d")
    day_dict = get_today_sched(
        record["schedule_type"], start_date, record['area'])
    dict_list["day_remarks"] = day_dict["day_remarks"]
    for x in x_field:
        if first_in:
            first_in = dict_list[x]
        else:
            if dict_list[x]:
                last_out = dict_list[x]
    dict_list['first_in'] = first_in
    dict_list['last_out'] = last_out
    dict_list['full_time'] = full_time
    dict_list['index'] = record['index']
    att_rec = db.attendance_record.find_one({"date": dict_list['date'],
                                             "SN": dict_list["SN"]})
    if not att_rec:
        db.attendance_record.insert_one(dict_list)
    else:
        dict_list.pop("_id")
        db.attendance_record.update_one(
            {"date": dict_list['date'], "SN": dict_list["SN"]}, {"$set": dict_list})

    return(dict_list)


def week_number_of_month(date_value):
    return (date_value.isocalendar()[1])
