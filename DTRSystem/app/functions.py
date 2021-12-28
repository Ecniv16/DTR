from app import *

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
import xlsxwriter
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

client = pymongo.MongoClient("mongodb://localhost:27017")
db = client["Monitoring"]
def_path = "/home/admin/app/dtr/development/data/"
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FILES_DIR = os.path.join(BASE_DIR, 'file')


def sent_verification(content, data):
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


def random_with_N_digits(n):
    range_start = 10**(n-1)
    range_end = (10**n)-1
    return random.randint(range_start, range_end)


def date_time_now():
    date_now = dt.now() - timedelta(hours=0, minutes=60)
    date_now = date_now.strftime("%m/%d/%Y")
    time_now = dt.now() - timedelta(hours=0, minutes=60)
    full_time = dt.now()
    time_now = time_now.strftime("%H:%M")

    date_time_dict = {
        "date_now": date_now,
        "time_now": time_now,
        "full_time": full_time
    }

    return(date_time_dict)


def get_sched_and_area(date_value, index: int):
    if type(date_value) is str:
        date_value = dt.strptime(date_value, "%Y-%m-%d")
    latest_dict = get_applicable_record_now('reference_employee_3', index, {
                                            'meta': 0, '_id': 0}, date_value)
    sched = latest_dict['schedule_type']
    area = latest_dict['area']
    location = latest_dict['location']
    return([sched, area, location])


def get_latest_record(date_value, index):
    super_dict = {}
    for x in range(1, 5):
        super_dict.update(get_applicable_record_now(
            f'reference_employee_{x}', index, {"meta": 0, "_id": 0}, date_value))

    return(super_dict)


def get_today_sched(reference_code, full_time, branch):
    time_now = full_time
    full_time = full_time
    date_now = full_time.strftime("%m/%d/%Y")
    time_now = time_now.strftime("%H:%M")
    day_name = full_time.strftime("%a")
    schedule_time = ""
    sched_in = ""
    sched_out = ""
    param_in = ""
    param_out = ""
    allowed_out = ""
    week_num = week_number_of_month(full_time)
    find_rec = {}
    day_dict = {
        "Mon": "mw",
        "Tue": "tw",
        "Wed": "ww",
        "Thu": "thw",
        "Fri": "fw",
        "Sat": "saw",
        "Sun": "suw",
    }
    if not find_one_module('reference_schedule_type', {'code': reference_code, 'meta.is_deleted': False}, {'_id': 0}):
        reference_code = 'N1'
    sched_cursor = find_module('reference_schedule_type', {
                               'code': reference_code, 'meta.is_deleted': False}, {'_id': 0})
    for item in sched_cursor:

        date_trans = dt.strptime(item["date"], "%Y-%m-%d")

        if full_time >= date_trans:

            find_rec.update(item)

    if not find_rec:
        find_rec = find_one_module('reference_schedule_type', {
                                   'code': 'N1', 'meta.is_deleted': False}, {'_id': 0})

    apply_date = dt.strptime(dt.strftime(dt.strptime(
        find_rec['date'], "%Y-%m-%d"), "%m/%d/%Y"), "%m/%d/%Y")
    apply_week = week_number_of_month(apply_date)
    add_even = apply_week % 2

    total_hour = 0
    for item in day_dict:
        if day_name == item:
            if (week_num % 2) == add_even:
                param_in = day_dict[item] + "1_in"
                param_out = day_dict[item] + "1_out"
            else:
                param_in = day_dict[item] + "2_in"
                param_out = day_dict[item] + "2_out"
    sched_in = find_rec[param_in]
    sched_out = find_rec[param_out]

    out_time = timedelta(hours=int(sched_out[:2]), minutes=int(sched_out[3:]))
    in_time = timedelta(hours=int(sched_in[:2]), minutes=int(sched_in[3:]))

    no_of_hours = out_time - in_time
    t = str(no_of_hours).split(":")
    total_hour = round((int(t[0])*60)+(int(t[1])*1), 0)/60
    if total_hour > 0:
        total_hour -= 1

    schedule_time = sched_in + " - " + sched_out
    allowed_out = dt.strptime(sched_out, "%H:%M") + \
        timedelta(hours=0, minutes=15)
    allowed_out = allowed_out.strftime("%H:%M")
    # time_remaining = str(timedelta(hours=int(allowed_out[:2]), minutes=int(allowed_out[3:])) - timedelta(hours=int(time_now[:2]), minutes=int(time_now[3:])))
    if timedelta(hours=int(allowed_out[:2]), minutes=int(allowed_out[3:])) >= timedelta(hours=int(time_now[:2]), minutes=int(time_now[3:])):
        time_remaining = str(timedelta(hours=int(allowed_out[:2]), minutes=int(
            allowed_out[3:])) - timedelta(hours=int(time_now[:2]), minutes=int(time_now[3:])))
    else:
        time_remaining = str("00:00")

    t = time_remaining.split(":")
    total_mins = round((int(t[0])*60)+(int(t[1])*1), 0)
    day_remarks = ""

    date_now = dt.strftime(date_converter(date_now), "%Y-%m-%d")
    holiday = db.reference_holiday.find_one({"date": date_now})
    if holiday:
        if holiday['area'] == branch:
            day_remarks = holiday['type']

        elif holiday['area'] == "ALL":
            day_remarks = holiday['type']

    if day_name == "Sun":
        if day_remarks != "":
            day_remarks = day_remarks + "/" + "RD"
        else:
            day_remarks = "RD"
    elif total_hour == 0:
        if day_remarks != "":
            day_remarks = day_remarks + "/" + "DO"
        else:
            day_remarks = "DO"

    dict_list = {
        "day_name": day_name,
        "week_num": week_num,
        "sched_in": sched_in,
        "sched_out": sched_out,
        "schedule_time": schedule_time,
        "allowed_out": allowed_out,
        "time_remaining": total_mins,
        "time_now": time_now,
        "working_hour": total_hour,
        "day_remarks": day_remarks,

    }

    return(dict_list)


def week_number_of_month(date_value):
    return (date_value.isocalendar()[1])


def data_converter(key, values):
    if 'date' in key:

        if values == '':
            new_values = "1900-01-01"
        else:
            values = dt.strptime(values.replace("'", ""), "%m/%d/%Y")
            new_values = dt.strftime(values, "%Y-%m-%d")
    else:
        if values == "'nan'":
            new_values = ""
        else:
            new_values = values

    return(new_values)


def get_last_day(date_value):
    last_day = last_day_of_month(date_value)
    last_day = str(last_day.day)
    return(last_day)


def get_last_day_2(date_value):
    first_day = f'{date_value.year}-{str(date_value.month).zfill(2)}-01'
    first_day = dt.strptime(first_day, "%Y-%m-%d") - timedelta(days=1)
    last_day = first_day.day
    return(last_day)


def get_date_range(start, date_now, last_day) -> list:
    if start == 1:
        cs, ce, ps, pe = "01", "15", "16", get_last_day_2(date_now)
        prev_start = f'{date_now.year}-{date_now.month-1}-{ps}'
        prev_end = f'{date_now.year}-{date_now.month-1}-{pe}'

    else:
        cs, ce, ps, pe = "16", str(last_day), "01", "15"
        prev_start = f'{date_now.year}-{date_now.month-1}-{ps}'
        prev_end = f'{date_now.year}-{date_now.month-1}-{pe}'

    cutoff_start = f'{date_now.year}-{date_now.month}-{cs}'
    cutoff_end = f'{date_now.year}-{date_now.month}-{ce}'
    cutoff_start = dt.strptime(cutoff_start, "%Y-%m-%d")
    cutoff_end = dt.strptime(cutoff_end, "%Y-%m-%d")
    prev_start = dt.strptime(prev_start, "%Y-%m-%d")
    prev_end = dt.strptime(prev_end, "%Y-%m-%d")

    date_dict = {'cutoff_start':cutoff_start,
        'cutoff_end': cutoff_end,
        'prev_start': prev_start, 
        'prev_start':prev_start}
    return(date_dict)


def date_converter(date_value):
    new_date = dt.strptime(date_value, "%m/%d/%Y")
    new_date = dt.strftime(new_date, "%Y-%m-%d")
    new_date = dt.strptime(new_date, "%Y-%m-%d")
    return(new_date)


def find_module(collection, query, cover):
    set_data = []
    cursor = list(db[collection].find(query, cover))
    for x in cursor:
        set_data.append(x)

    return(set_data)


def find_module_sorted(collection, query, cover, sorter, ordering):
    set_data = []
    cursor = db[collection].find(query, cover).sort(sorter, ordering)
    for x in cursor:
        set_data.append(x)

    return(set_data)


def find_last_module(collection, query, cover):
    set_data = []
    if collection == "reference_schedule_type":
        cursor = list(db[collection].find(query, cover).sort("date", -1))
    else:
        cursor = list(db[collection].find(query, cover).sort("applied", -1))

    for x in cursor:
        return(x)

    return(set_data)


def find_last_item(collection, query, cover, order_by):
    set_data = []

    cursor = list(db[collection].find(query, cover).sort(order_by, -1))

    for x in cursor:
        return(x)

    return(set_data)


def find_one_module(collection, query, cover):
    details_dict = db[collection].find_one(query, cover)
    return(details_dict)


def insert_one_module(collection, query):
    details_dict = db[collection].insert_one(query)
    return(details_dict)


def update_one_module(collection, criteria, query):
    details_dict = db[collection].update_one(criteria, {"$set": query})
    return(details_dict)


def count_module(collection, query):
    set_data = []
    rec_count = db[collection].find(query).count()

    return(rec_count)


def employee_cursor():
    if session["user_type"] == "Administrator":
        search_dict = {"meta.is_deleted": False}

    elif session["user_type"] == "Supervisor" or session['user_type'] == "Senior Supervisor":
        search_dict = {"meta.is_deleted": False,
                       "immediate_supervisor": session["SN"]}

    elif session["user_type"] == "Department Head":
        search_dict = {"meta_is_deleted": False,
                       "department_head": session["SN"]}

    else:
        search_dict = {"index": session["SN"]}

    return(search_dict)


def field_getter():
    dict_list = {
        "leave_field": ["VL", "SL", "BL", "SP", "ML", "PL", "MC", "VS", "BRL"],
    }

    return(dict_list)


def convert_nan_to_zero(raw_data):
    if str(raw_data) == "nan" or raw_data == '':
        data = 0

    else:
        data = float(str(raw_data).replace("'", ""))

    return(data)


def convert_nan_to_string(raw_data):
    if str(raw_data) == "nan":
        data = ""

    else:
        print(raw_data)
        data = str(raw_data).replace("'", "")

    return(data)


def convert_nan_to_date(raw_data):
    if str(raw_data) == "nan":
        data = "1900-01-01"

    else:
        data = dt.strftime(date_converter(
            str(raw_data).replace("'", "")), '%Y-%m-%d')

    return(data)


def disapproved_leave(data):
    date_now = dt.now() - timedelta(hours=0, minutes=60)
    date_now = date_now.strftime("%m/%d/%Y")
    db.utilities_leave_application.update_one({"index": int(data['index'])}, {
                                              "$set": {"basic_info.status": "Disapproved/Cancelled"}})
    cursor = list(db.utilities_leave_detail.find(
        {"ref_index": int(data['index'])}))
    total_hour = 0
    from_vl = float(data['from_vl'])

    for details in cursor:
        total_hour += details['hours_paid']

    total_hour = total_hour - from_vl

    find_rec = get_applicable_record_now(
        'reference_leave_credit', session['index'], {'meta': 0, '_id': 0}, '')
    if find_rec:
        if data['leave_type'] == "VL":
            db.reference_leave_credit.update_one({"ref_index": int(find_rec['ref_index'])}, {
                                                 "$inc": {data['leave_type']+"_r": total_hour}})

        elif data['leave_type'] == "VS":
            db.reference_leave_credit.update_one({"ref_index": int(find_rec['ref_index'])}, {
                                                 "$inc": {data['leave_type']+"_r": 8, "VL_r": from_vl}})

        elif data['leave_type'] != "UT":
            db.reference_leave_credit.update_one({"ref_index": int(find_rec['ref_index'])}, {
                                                 "$inc": {data['leave_type']+"_r": total_hour, "VL_r": from_vl}})


def approval_remarks(data, application, file_type, remarks):

    if "DM" in remarks or remarks == "Approved":
        remarks = "approved"
    else:
        remarks = "disapproved"

    content = {
        "receiver": session['email'],
        "subject": 'DTR SYSTEM: '+file_type+' APPROVAL - ' + data['name'],
        "message": """Youve """ + remarks + " " + application + """ application no: """ + data['ref_index']
    }
    sent_verification(content, data)
    return("Successfu")


def last_day_of_month(any_day):
    # this will never fail
    # get close to the end of the month for any day, and add 4 days 'over'
    if any_day.month == 12:
        new_date = f"{any_day.year + 1}-01-01"
    else:
        new_date = f"{any_day.year}-{any_day.month + 1}-01"

    new_date = dt.strptime(new_date, "%Y-%m-%d")
    end_of_the_month = new_date - timedelta(days=1)

    # subtract the number of remaining 'overage' days to get last day of current month, or said programattically said, the previous day of the first of next month
    return end_of_the_month


def get_leave_application(index, date_now, effective_date):
    sl_hl, paid = "", ""
    leave_remark, approved_date = "", ""
    leave_type, proper = "", ""
    date_start, date_end = "", ""
    applied, working_hour = 0, 0
    paid_hour, not_paid = 0, 0
    effective_start = ""
    leave_index = 0
    application_cursor = db.utilities_leave_application.find(
        {"basic_info.ref_index": index, "basic_info.status": "Approved", "meta.is_deleted": False})

    for leave in application_cursor:
        details_dict = db.utilities_leave_detail.find_one({"ref_index": int(leave['index']),
                                                           "date_now": date_now})
        if details_dict:

            if details_dict['hours_paid'] > 0 and details_dict['hours_not_paid'] > 0:
                sl_hl = f"{leave['leave_type']}:W{details_dict['hours_paid']}/L{details['hours_not_paid']}"
            elif details_dict['hours_paid'] > 0:
                sl_hl = f"{leave['leave_type']}:W{details_dict['hours_paid']}"

            else:
                sl_hl = f"{leave['leave_type']}:L{details_dict['hours_not_paid']}"

            effective_start = details_dict['effective_start']

            paid_hour += details_dict['hours_paid']
            proper = leave['basic_info']['supervisor_remarks_2']
            leave_index = leave['index']

    paid_hour = paid_hour/8
    temp_dict = {
        "sl_hl": sl_hl,
        'effective_start': effective_start,
        'paid_hour': paid_hour,
        'proper': proper,
        'index': leave_index

    }
    # print(date_now,temp_dict)
    return(temp_dict)


def add_leave_basic(index, date_now, date_end):
    application_cursor = db.utilities_leave_application.find({"basic_info.ref_index": index, "basic_info.status": "Approved",
                                                              "meta.is_deleted": False})

    add_to_basic = 0
    add_to_absent = 0

    for leave in application_cursor:

        details = db.utilities_leave_detail.find(
            {"ref_index": int(leave['index']), "effective_start": date_now})

        for x in details:

            if not(dt.strptime(date_now, '%Y-%m-%d') <= date_converter(x['date_now']) and dt.strptime(date_end, '%Y-%m-%d') >= date_converter(x['date_now'])):
                if leave['leave_type'] == "VS":
                    add_to_basic += 8

                else:
                    add_to_basic += x['hours_paid']

    add_to_basic = add_to_basic/8

    return(add_to_basic)


def create_excel_file(set_data):
    mega = Mega()
    m = mega.login("vinceagoyaoy11@gmail.com", "bdcn@001")
    # try:
    filename = "DTR_report.xlsx"
    path_open = str(os.path.join(FILES_DIR, filename))
    workbook = xlsxwriter.Workbook(
        path_open)
    # except:
    # workbook = xlsxwriter.Workbook('E:\\DTR_report.xlsx')
    # path_open = str(os.path.join('E:\\','DTR_report.xlsx'))
    worksheet = workbook.add_worksheet()
    set_data = set_data

    # Start from the first cell. Rows and columns are zero indexed.
    row = 0
    col = 0

    # Iterate over the data and write it out row by row.
    merge_format = workbook.add_format({
        'bold': 1,
        'align': 'center',
        'valign': 'vcenter'
    })
    worksheet.merge_range('A1:A2', 'Code', merge_format)
    worksheet.merge_range('B1:B2', 'Employee Name', merge_format)
    worksheet.merge_range('C1:C2', 'Department', merge_format)
    worksheet.merge_range('D1:D2', 'Date Hired', merge_format)
    worksheet.merge_range('E1:E2', 'Date Separated', merge_format)
    worksheet.merge_range('F1:H1', 'Regular day', merge_format)
    worksheet.merge_range('I1:J1', 'Rest day', merge_format)
    worksheet.merge_range('K1:L1', 'Regular holiday', merge_format)
    worksheet.merge_range(
        'M1:N1', 'Regular holiday falling on rest day', merge_format)
    worksheet.merge_range('O1:P1', 'Special holiday', merge_format)
    worksheet.merge_range(
        'Q1:R1', 'Special holiday falling on rest day', merge_format)
    worksheet.write(1, 5, "BASIC (days)", merge_format)
    worksheet.write(1, 6, "OT (hrs)", merge_format)
    worksheet.write(1, 7, "ABSENT (days)", merge_format)
    worksheet.write(1, 8, "BASIC (hrs)", merge_format)
    worksheet.write(1, 9, "OT (hrs)", merge_format)
    worksheet.write(1, 10, "BASIC", merge_format)
    worksheet.write(1, 11, "OT", merge_format)
    worksheet.write(1, 12, "BASIC", merge_format)
    worksheet.write(1, 13, "OT", merge_format)
    worksheet.write(1, 14, "BASIC", merge_format)
    worksheet.write(1, 15, "OT", merge_format)
    worksheet.write(1, 16, "BASIC", merge_format)
    worksheet.write(1, 17, "OT", merge_format)

    row = 2

    for dicts in set_data:
        col = 0
        for item in dicts:
            # if item == "employee_id":
            # 	worksheet.write(row, col,dicts[item].zfill(6))
            # 	col +=1
            if item != "index" and item != "SN":
                worksheet.write(row, col, dicts[item])
                col += 1
        row += 1

    # Write a total using a formula.

    workbook.close()

    filename = "DTR_report.xlsx"

    # path_open = str(os.path.join("/home/admin/apps/dtr/development/data/",filename))

    file = m.find(filename)
    m.delete(file[0])
    # files = m.upload("E:\\DTR_report.xlsx")

    files = m.upload(path_open)
    x = m.get_upload_link(files)

    return(x)


def create_excel_file_x(set_data):
    mega = Mega()
    m = mega.login("vinceagoyaoy11@gmail.com", "bdcn@001")
    filename = "DTR_report_2.xlsx"
    path_open = str(os.path.join(FILES_DIR, filename))
    workbook = xlsxwriter.Workbook(
        path_open)
    worksheet = workbook.add_worksheet()
    set_data = set_data

    # Start from the first cell. Rows and columns are zero indexed.
    row = 0
    col = 0

    # Iterate over the data and write it out row by row.
    merge_format = workbook.add_format({
        'bold': 1,
        'align': 'center',
        'valign': 'vcenter'
    })

    worksheet.merge_range('B1:C1', 'TARDINESS', merge_format)
    worksheet.merge_range('D1:G1', 'ABSENCES', merge_format)
    worksheet.write(1, 0, "NAME")
    worksheet.write(1, 1, "In Minutes")
    worksheet.write(1, 2, "Frequency in a Month")
    worksheet.write(1, 3, "Properly Filed")
    worksheet.write(1, 4, "Improperly Filed")
    worksheet.write(1, 5, "Unfiled Leave")
    worksheet.write(1, 6, "Undertime")

    row = 2

    for dicts in set_data:
        col = 0
        for item in dicts:

            if item != "index" and item != "SN" and item != "employee_id":
                worksheet.write(row, col, dicts[item])
                col += 1
        row += 1
    workbook.close()

    file = m.find(filename)
    try:
        m.delete(file[0])

    except:
        x = ""

    files = m.upload(path_open)
    x = m.get_upload_link(files)

    return(x)


def list_of_employee(data):
    dict_list = {
        'company': '',
        'department': '',
        'section': '',
        'meta.is_deleted': False
    }
    for x in ['company', 'department', 'section']:
        if data[x] == "ALL":
            dict_list[x] = {"$ne": ""}
        else:
            dict_list[x] = data[x]
    set_data = []
    sort_cursor = db['reference_employee_1'].find({'meta.is_deleted': False}, {
                                                  "meta": 0, "_id": 0, "applied": 0}).sort('last_name')
    for x in sort_cursor:
        dict_list['index'] = x['index']

        if db['reference_employee_2'].find_one(dict_list, {"index": 1, "_id": 0}):
            z = x
            z.update(db['reference_employee_2'].find_one(
                dict_list, {"index": 1, "_id": 0}))
            set_data.append(z)

    return(set_data)


def time_conversion(time_value):
    if "+" in time_value:
        converted_time = timedelta(days=1, hours=int(
            time_value[:2]), minutes=int(time_value.replace('+', '')[3:]))
    elif time_value == "":
        converted_time = ""
    else:
        converted_time = timedelta(
            hours=int(time_value[:2]), minutes=int(time_value.replace('+', '')[3:]))

    return(converted_time)


def get_first(time_dict: list):
    first_in = ""
    first_in_val = timedelta(days=1)
    for time_value in time_dict:
        if time_value != '':
            if first_in_val > time_conversion(time_value):
                first_in = time_value
                first_in_val = time_conversion(time_value)

    return (first_in)


def get_last(time_dict: dict) -> dict:
    last_out = ""
    last_out_val = timedelta(days=0)
    for time_value in time_dict:
        if time_value != '':
            if time_value and last_out_val < time_conversion(time_value):
                last_out = time_value
                last_out_val = time_conversion(time_value)

    return (last_out)


def time_diff_late(time_1: str, basis_time: str):
    result = 0
    if time_1 and basis_time:
        if time_conversion(basis_time) < time_conversion(time_1):
            diff = time_conversion(time_1) - time_conversion(basis_time)
            result = str(diff).split(":")
            result = round((int(result[0])*60)+(int(result[1])*1), 0)
            if result <= 3:
                result = 0

    return (result)


def time_diff_undertime(time_1: str, basis_time: str):
    result = 0
    if time_1 and basis_time:
        if time_conversion(basis_time) > time_conversion(time_1):

            diff = time_conversion(basis_time) - time_conversion(time_1)
            result = str(diff).split(":")
            result = round((int(result[0])*60)+(int(result[1])*1), 0)

    return (result)


def get_ot_details(first_in, last_out, basis_in, basis_out, ot_hrs, is_holiday):
    ot_am, ot_pm = timedelta(days=0), timedelta(days=0)
    total_ot = 0
    if first_in and last_out and int(ot_hrs) > 0:
        if first_in[3:] == "03":
            first_in = f"{first_in[:2]}:00"

        if is_holiday:
            total_ot = time_diff_undertime(first_in, last_out)/60

        else:
            ot_am = time_diff_undertime(first_in, basis_in)
            ot_pm = time_diff_undertime(basis_out, last_out)

            if ot_am/60 < 1:
                ot_am = 0
            if ot_pm/60 < 1:
                ot_pm = 0

            total_ot = (ot_am + ot_pm)/60

    if total_ot % .5 > 0:
        total_ot -= (total_ot % .5)

    if total_ot > 6:
        total_ot -= 1

    if total_ot > int(ot_hrs):
        total_ot = int(ot_hrs)

    return (total_ot)


def with_default(data):
    if data:
        return(data)
    else:
        return('')


def check_difference(dict_1, dict_2, basis, ot_hrs):
    basic_in, basic_out = 0, 0
    raw_in, raw_out = 0, 0
    no_of_lates = 0
    under_time = 0
    first_in, last_out = "", ""
    basic, reg_ot = 0, 0
    remarks = ['SH', 'DO', "RD", 'RH', "SH/RD", "SH/DO", "RH/RD", "RH/DO"]
    first_in = get_first(
        [dict_1['first_in'], dict_1['last_out'], dict_2['first_in'], dict_2['last_out']])
    last_out = get_last([dict_1['first_in'], dict_1['last_out'],
                        dict_2['first_in'], dict_2['last_out']])
    if time_diff_undertime(dict_1['first_in'], dict_1['last_out']) >= basis['working_hour'] * 60:
        basic += 0
    else:
        if dict_1['first_in'] and dict_1['last_out']:
            if dict_1['first_in'] and dict_2['first_in']:
                if time_conversion(dict_1['first_in']) > time_conversion(dict_2['first_in']):
                    basic_in += time_diff_undertime(
                        dict_2['first_in'], dict_1['first_in'])
                    if time_conversion(basis['sched_in']) < time_conversion(dict_2['first_in']):
                        no_of_lates += time_diff_late(time_conversion(
                            dict_2['first_in']), basis['sched_in'])

                    else:
                        raw_in += time_diff_undertime(
                            dict_2['first_in'], basis['sched_in'])
                    basic_in -= no_of_lates + raw_in

            if dict_1['last_out'] and dict_2['last_out']:
                if time_conversion(dict_1['last_out']) < time_conversion(dict_2['last_out']):
                    basic_out += time_diff_undertime(
                        dict_1['last_out'], dict_2['last_out'])
                    if time_conversion(basis['sched_out']) < time_conversion(dict_2['last_out']):
                        under_time += time_diff_undertime(
                            time_conversion(dict_2['last_out']), basis['sched_out'])
                    else:
                        raw_out += time_diff_undertime(
                            basis['sched_out'], dict_2['last_out'])
                    basic_out -= under_time + raw_out

            basic = basic_out + basic_in

        else:
            if first_in != '' and last_out != '' and first_in == last_out:
                if time_conversion(first_in) >= time_conversion("14:00"):
                    first_in = ''
                else:
                    last_out = ''

            if first_in and last_out:
                if not any(xs in basis['day_remarks'] for xs in remarks):
                    basic = time_diff_undertime(first_in, last_out)

                    no_of_lates = time_diff_late(first_in, basis['sched_in'])
                    under_time = time_diff_undertime(
                        last_out, basis['sched_out'])

                    if basic >= (basis['working_hour'] * 60):

                        basic = ((basis['working_hour'] * 60) -
                                 (no_of_lates+under_time))/480

                    else:
                        if basic >= 360:
                            basic -= 60
                            basic = basic/480

    return(basic)


def adjustment_basic(index, date_now, date_end):
    record = get_latest_record(dt.strptime(date_now, '%Y-%m-%d'), index)
    att_in, ob_in, logs_in = "", "", ""
    att_out, ob_out, logs_out = "", "", ""
    basic, reg_ot, absent = 0, 0, 0
    ob_cursor = db['utilities_ob_application'].find(
        {"meta.is_deleted": False, 'basic_info.ref_index': index, "basic_info.effective_start": date_now})
    logs_cursor = db['utilities_missing_logs_application'].find(
        {"meta.is_deleted": False, 'basic_info.ref_index': index, "basic_info.effective_start": date_now})
    ot_cursor = db['utilities_ot_application'].find(
        {"meta.is_deleted": False, 'basic_info.ref_index': index, "basic_info.effective_start": date_now})
    day_remarks = ''
    remarks = ['SH', 'DO', "RD", 'RH']

    collections = {'ob': 'ob', 'missing_logs': 'logs',
                   'wfh': 'wfh', 'day_offset': 'day_offset'}
    for collection in collections:
        cursor = db[f'utilities_{collection}_application'].find({"meta.is_deleted": False, 'basic_info.ref_index': index,
                                                                 "basic_info.effective_start": date_now, "basic_info.status": 'Approved'}, {"meta": 0, "_id": 0})
        for x in cursor:
            if 'offset' in collection:
                basis = get_today_sched(record['schedule_type'], dt.strptime(
                    x['offset_day'], '%Y-%m-%d'), record['area'])
            else:
                basis = get_today_sched(record['schedule_type'], dt.strptime(
                    x['date'], '%Y-%m-%d'), record['area'])
            ot_hrs = 0
            dict_list = {}
            list_data = []
            time_list = []
            set_data_past = []
            set_data_current = []
            pass_cut_off = []
            current_cut_off = []
            current_dict, pass_dict = {}, {}
            att_dict = db['attendance_record'].find_one({'index': index, 'date': x['date']}, {
                                                        'first_in': 1, 'last_out': 1, '_id': 0})

            if att_dict:
                att_in = with_default(att_dict['first_in'])
                att_out = with_default(att_dict['last_out'])

            if not any(d['date'] == x['date'] for d in list_data):
                if not x['date'] in set_data_past:
                    set_data_past.append(x['date'])
                if not x['date'] in set_data_current:
                    set_data_current.append(x['date'])
                dict_list = {
                    'date': x['date'],
                    'att_in': att_in,
                    'att_out': att_out
                }
                pass_cut_off.append(dict_list)
                current_cut_off.append({'date': x['date']})

            for item in collections:
                col = db[f'utilities_{item}_application'].find_one(
                    {'basic_info.ref_index': index, 'date': x['date']}, {'meta': 0, '_id': 0})
                if col and dt.strptime(date_now, "%Y-%m-%d") > dt.strptime(col['basic_info']['effective_start'], "%Y-%m-%d") and item != 'day_offset':
                    pass_cut_off[list(set_data_past).index(
                        x['date'])][f'{collections[item]}_in'] = col[f'{collections[item]}_am']
                    pass_cut_off[list(set_data_past).index(
                        x['date'])][f'{collections[item]}_out'] = col[f'{collections[item]}_pm']
                elif col and dt.strptime(date_now, "%Y-%m-%d") == dt.strptime(col['basic_info']['effective_start'], "%Y-%m-%d") and item != 'day_offset':
                    current_cut_off[list(set_data_current).index(
                        x['date'])][f'{collections[item]}_in'] = col[f'{collections[item]}_am']
                    current_cut_off[list(set_data_current).index(
                        x['date'])][f'{collections[item]}_out'] = col[f'{collections[item]}_pm']

            for item in current_cut_off:
                for keys in item:
                    if 'in' in keys or 'out' in keys:
                        time_list.append(item[keys])

            first_in = get_first(time_list)
            last_out = get_last(time_list)
            if first_in != '' and last_out != '' and first_in == last_out:
                if time_conversion(first_in) >= time_conversion("14:00"):
                    first_in = ''
                else:
                    last_out = ''

            current_dict = {
                'first_in': first_in,
                'last_out': last_out
            }
            time_list = []
            for item in pass_cut_off:
                for keys in item:
                    if 'in' in keys or 'out' in keys:
                        time_list.append(item[keys])

            first_in = get_first(time_list)
            last_out = get_last(time_list)
            if first_in != '' and last_out != '' and first_in == last_out:
                if time_conversion(first_in) >= time_conversion("14:00"):
                    first_in = ''
                else:
                    last_out = ''

            pass_dict = {
                'first_in': first_in,
                'last_out': last_out
            }
            if not(dt.strptime(date_now, '%Y-%m-%d') <= dt.strptime(x['date'], '%Y-%m-%d') and dt.strptime(date_end, '%Y-%m-%d') >= dt.strptime(x['date'], '%Y-%m-%d')):
                basic += check_difference(pass_dict,
                                          current_dict, basis, ot_hrs)

    return(basic)


def adjustment_ot(index, date_now):
    record = get_latest_record(dt.strptime(date_now, '%Y-%m-%d'), index)
    att_in, ob_in, logs_in = "", "", ""
    att_out, ob_out, logs_out = "", "", ""
    basic, reg_ot, absent = 0, 0, 0
    rd_basic, rd_ot = 0, 0
    rh_basic, rh_ot = 0, 0
    rd_rh_basic, rd_rh_ot = 0, 0
    sh_basic, sh_ot = 0, 0
    sh_rd_basic, sh_rd_ot = 0, 0
    ob_cursor = db['utilities_ob_application'].find(
        {"meta.is_deleted": False, 'basic_info.ref_index': index, "basic_info.effective_start": date_now})
    logs_cursor = db['utilities_missing_logs_application'].find(
        {"meta.is_deleted": False, 'basic_info.ref_index': index, "basic_info.effective_start": date_now})
    ot_cursor = db['utilities_ot_application'].find(
        {"meta.is_deleted": False, 'basic_info.ref_index': index, "basic_info.effective_start": date_now})
    day_remarks = ''
    remarks = ['SH', 'DO', "RD", 'RH']
    collections = {'ob': 'ob', 'missing_logs': 'logs',
                   'wfh': 'wfh', 'day_offset': 'day_offset'}
    cursor = db[f'utilities_ot_application'].find({"meta.is_deleted": False, 'basic_info.ref_index': index,
                                                   "basic_info.effective_start": date_now, "basic_info.status": 'Approved'}, {"meta": 0, "_id": 0})

    for x in cursor:

        ot_hrs = int(x['ot_hrs'])
        regular_ot, sp_basic, sp_ot = 0, 0, 0
        dict_list = {}
        list_data = []
        time_list = []
        set_data_past = []
        set_data_current = []
        pass_cut_off = []
        current_cut_off = []
        current_dict, pass_dict = {}, {}
        att_dict = db['attendance_record'].find_one({'index': index, 'date': x['date']}, {
                                                    'first_in': 1, 'last_out': 1, '_id': 0})

        basis = get_today_sched(record['schedule_type'], dt.strptime(
            x['date'], '%Y-%m-%d'), record['area'])
        if att_dict:
            att_in = with_default(att_dict['first_in'])
            att_out = with_default(att_dict['last_out'])
            time_list.append(att_in)
            time_list.append(att_out)
        if not any(d['date'] == x['date'] for d in list_data):
            if not x['date'] in set_data_past:
                set_data_past.append(x['date'])
            if not x['date'] in set_data_current:
                set_data_current.append(x['date'])

            pass_cut_off.append(dict_list)
            current_cut_off.append({'date': x['date']})

            for item in collections:

                col = db[f'utilities_{item}_application'].find_one(
                    {'basic_info.ref_index': index, 'date': x['date']}, {'meta': 0, '_id': 0})
                if col and dt.strptime(date_now, "%Y-%m-%d") >= dt.strptime(col['basic_info']['effective_start'], "%Y-%m-%d") and 'offset' not in item:
                    time_list.append(col[f'{collections[item]}_am'])
                    time_list.append(col[f'{collections[item]}_pm'])

                if col and 'offset' in item:
                    basis = get_today_sched(record['schedule_type'], dt.strptime(
                        col['offset_day'], '%Y-%m-%d'), record['area'])
                else:
                    basis = get_today_sched(record['schedule_type'], dt.strptime(
                        x['date'], '%Y-%m-%d'), record['area'])

            first_in = get_first(time_list)
            last_out = get_last(time_list)
            if first_in != '' and last_out != '' and first_in == last_out:
                if time_conversion(first_in) >= time_conversion("14:00"):
                    first_in = ''
                else:
                    last_out = ''

        if not any(xs in basis['day_remarks'] for xs in remarks):
            regular_ot = get_ot_details(
                first_in, last_out, basis['sched_in'], basis['sched_out'], ot_hrs, False)
        else:
            ot_result = get_ot_details(
                first_in, last_out, basis['sched_in'], basis['sched_out'], ot_hrs, True)
            if ot_result > 8:
                sp_basic = 8
                sp_ot = ot_result - 8
            else:
                sp_basic = ot_result
        reg_ot += regular_ot
        if basis['day_remarks'] in ['RH/RD', 'RH/DO']:

            rd_rh_basic += sp_basic
            rd_rh_ot += sp_ot
        elif any(xs in basis['day_remarks'] for xs in ['SH/RD', 'SH/DO']):

            sh_rd_basic += sp_basic
            sh_rd_ot += sp_ot
        elif basis['day_remarks'] == 'SH':
            sh_basic += sp_basic
            sh_ot += sp_ot
        elif basis['day_remarks'] == 'RH':
            rh_basic += sp_basic
            rh_ot += sp_ot
        elif basis['day_remarks'] in ['RD', 'DO']:
            rd_basic += sp_basic
            rd_ot += sp_ot

    dict_list = {
        'reg_ot': reg_ot,
        'rd_rh_basic': rd_rh_basic,
        'rd_rh_ot': rd_rh_ot,
        'sh_rd_basic': sh_rd_basic,
        'sh_rd_ot': sh_rd_ot,
        'sh_basic': sh_basic,
        'sh_ot': sh_ot,
        'rh_basic': rh_basic,
        'rh_ot': rh_ot,
        'rd_basic': rd_basic,
        'rd_ot': rd_ot,
    }

    return (dict_list)


def leave_vs_deduction(deduction, paid_hour):

    if deduction > 60:
        if paid_hour and deduction > paid_hour * 480:

            deduction = deduction - (paid_hour * 480)

        elif paid_hour * 480 > deduction:
            deduction = 0

    return(deduction)


def query_setter(content):
    query = {}
    query['default'] = {'meta.is_deleted': False}
    query['reference_employee_2'] = {
        'company': {'$ne': ""},
        'department': {'$ne': ""},
        'section': {'$ne': ""},
        'meta.is_deleted': False
    }
    if content not in query:
        return(query['default'])

    return(query[content])


def get_applicable_record_now(collection, index, cover, date_now):
    if not date_now:
        date_now = dt.strftime(dt.now(), "%Y-%m-%d")
        date_now = dt.strptime(date_now, "%Y-%m-%d")
    query = query_setter(collection)
    query.update({'index': int(index)})

    cursor = find_module(collection, query, cover)
    super_dict = {}
    latest_date = dt.strptime('1900-01-01', "%Y-%m-%d")
    latest_dict = {}
    for item in cursor:
        date_trans = dt.strptime(item['applied'][:10], "%Y-%m-%d")
        if date_now >= date_trans:

            if latest_date <= date_trans:

                latest_date = date_trans
                latest_dict = item

    if latest_dict:
        latest_dict.update({'applied': latest_dict['applied'][:10]})
    super_dict.update(latest_dict)

    return(super_dict)


class Custom_Function:
    def curr_year(curr_date):
        new_year = str(curr_date.year)
        return(new_year)

    def curr_month(curr_date):
        new_month = str(curr_date.month).zfill(2)
        return(new_month)

    def adv_month(curr_date):
        new_month = str(curr_date.month + 1).zfill(2)
        return(new_month)

    def prev_month(curr_date):
        new_month = str(curr_date.month - 1).zfill(2)
        return(new_month)