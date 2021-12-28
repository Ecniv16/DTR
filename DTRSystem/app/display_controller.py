from app import *
from .utilities_controller import *

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

client = pymongo.MongoClient("mongodb://localhost:27017")
db = client["Monitoring"]
message = ''
mega = Mega()


def display_leave_detail(index):
    set_data = []
    dict_list = db.utilities_leave_application.find_one({"index": int(index)})
    cursor = db.utilities_leave_detail.find({"ref_index": int(index)})
    for item in cursor:
        x = dict(item)
        x["leave_type"] = dict_list["leave_type"]
        x["reason"] = dict_list["reason"]
        set_data.append(x)

    return(set_data)


def utilities_display(content, param, index):
    if param + content == "profile":
        result = display_profile()

    elif param + content == "leave":
        result = display_leave()

    elif param + content == "archived_leave":
        result = archived_leave()

    elif param + content in ["missing_logs", "ot", "ob", "wfh", "day_offset"]:
        result = display_common(content)

    elif param + content in ["archived_ob", "archived_ot", "archived_wfh", "archived_missing_logs", "archived_day_offset"]:
        result = archived_common(content, index)

    return(result)


def display_profile():
    set_data = []
    dict_list = {}
    x = db.reference_employee_1.find_one(
        {"index": session['index']}, {"meta": 0, "_id": 0})
    set_data = []
    pending_data = []
    leave_form_count = 0
    # Get Pending Leave Detail
    leave_personal_dict = find_module("utilities_leave_application", {"meta.is_deleted": False, "basic_info.ref_index": session['index'], "$and": [
        {"basic_info.status": {"$ne": "Approved"}}, {"basic_info.status": {"$ne": "Cancelled"}}, {"basic_info.status": {"$ne": "Disapproved"}}]}, {"meta": 0, "_id": 0})

    for lp in leave_personal_dict:
        x = find_module("utilities_leave_detail", {
            "ref_index": lp['index']}, {"meta": 0, "_id": 0})
        hours_paid = 0
        hours_not_paid = 0
        if x:
            for x_item in x:
                hours_paid += x_item['hours_paid']
                hours_not_paid += x_item['hours_not_paid']

        lp.update({
            "hours_paid": hours_paid,
            "hours_not_paid": hours_not_paid
        })

    # Get Pending Common Count
    pending_count = {}
    for item in ['leave', 'ob', 'ot', 'missing_logs', 'wfh', 'day_offset']:
        pending_count[item] = count_module(f"utilities_{item}_application", {"meta.is_deleted": False, "basic_info.ref_index": int(session['index']),
                                                                             "basic_info.status": {"$ne": "Approved"}})

    # Get Pending Common Detail
    pending_list = {}
    for item in ['leave', 'ob', 'ot', 'missing_logs', 'wfh', 'day_offset']:

        set_data = []
        pending_list_cursor = find_module(f"utilities_{item}_application", {"meta.is_deleted": False, "basic_info.ref_index": session['index'], "$and": [{"basic_info.status": {
            "$ne": "Approved"}}, {"basic_info.status": {"$ne": "Cancelled"}}, {"basic_info.status": {"$ne": "Disapproved"}}]}, {"meta": 0, "_id": 0})
        for list_item in pending_list_cursor:
            if item == 'leave':
                start_date = dt.strptime(list_item["date_from"], "%Y-%m-%d")
            else:
                start_date = dt.strptime(list_item["date"], "%Y-%m-%d")
            full_time = dt.strftime(start_date, "%m/%d/%Y")
            full_time = dt.strptime(full_time, "%m/%d/%Y")
            sched, area, location = get_sched_and_area(
                start_date, session['index'])
            day_remarks = get_today_sched(sched, full_time, area)
            list_item['day_remarks'] = day_remarks['day_remarks']
            list_item['branch'] = area
            list_item['location'] = location
            set_data.append(list_item)
        pending_list[item] = set_data
    dict_list.update({
        "pending_leave_count": pending_count['leave'],
        "pending_ot_count": pending_count['ot'],
        "pending_ob_count": pending_count['ob'],
        "pending_wfh_count": pending_count['wfh'],
        "pending_day_offset_count": pending_count['day_offset'],
        "pending_missing_logs_count": pending_count['missing_logs'],
        "leave_personal": leave_personal_dict,
        "ot": pending_list['ot'],
        "ob": pending_list['ob'],
        "missing_logs": pending_list['missing_logs'],
        "wfh": pending_list['wfh'],
        "day_offset": pending_list['day_offset'],
    })

    cursor = list(db.reference_leave.find({"is_deleted": False}, {
                  'reference_name': 1, 'reference_code': 1, '_id': 0}))
    set_data = []
    get_field = field_getter()
    leave_field = get_field['leave_field']
    leave_dict = get_applicable_record_now(
        'reference_leave_credit', session['index'], {'meta': 0, '_id': 0}, '')
    for x in cursor:

        if x['reference_code'] in leave_field:
            if not leave_dict:
                x.update({
                    "no_hours": 0,
                    "remaining_hours": 0,
                    "ref_index": 0
                })

            else:
                x.update({
                    "no_hours": int(leave_dict[str(x['reference_code'])]),
                    "remaining_hours": int(leave_dict[str(x['reference_code'])+"_r"]),
                    "ref_index": leave_dict['ref_index']
                })

        set_data.append(x)
        dict_list['reference_leave'] = set_data

    set_data = []
    if not get_applicable_record_now('reference_leave_credit', session['index'], {'meta': 0, '_id': 0}, ''):
        set_data.append({
            'SL': 0,
            'VL': 0,
            'BL': 0,
            'SP': 0,
            'BRL': 0,
            'ML': 0,
            'PL': 0,
            'MC': 0,
            'VS': 0,
            'SL_r': 0,
            'VL_r': 0,
            'BL_r': 0,
            'SP_r': 0,
            'BRL_r': 0,
            'ML_r': 0,
            'PL_r': 0,
            'MC_r': 0,
            'VS_r': 0,
            'ref_index': 0
        })
    else:
        set_data.append(get_applicable_record_now(
            'reference_leave_credit', session['index'], {'meta': 0, '_id': 0}, ''))

    dict_list['leave'] = set_data

    return(dict_list)


def display_leave():
    # list of For Approval Leave
    date_now = dt.now() - timedelta(hours=0, minutes=60)
    set_data = []
    dict_list = {}
    index_list = {"index": 1, "last_name": 1,
                  "first_name": 1, "middle_name": 1, "_id": 0}
    if session['user_type'] == "Department Head":
        lp = find_module("utilities_leave_application", {"meta.is_deleted": False, "basic_info.dm_name": session['SN'],
                                                         "basic_info.status": "For DM's Approval"}, {"meta": 0, "_id": 0})

    else:
        lp = find_module("utilities_leave_application", {"meta.is_deleted": False, "basic_info.supervisor_name": session['SN'],
                                                         "basic_info.status": "For SV/SSV's Approval"}, {"meta": 0, "_id": 0})

    for z in lp:
        y = find_module("utilities_leave_detail", {
            "ref_index": int(z['index'])}, {"_id": 0})
        hours_paid = 0
        hours_not_paid = 0
        if y:
            for x_item in y:
                hours_paid += x_item['hours_paid']
                hours_not_paid += x_item['hours_not_paid']
        z.update({
            "hours_paid": hours_paid,
            "hours_not_paid": hours_not_paid,
            "ref_index": int(z['index']),

        })

        set_data.append(z)
    dict_list['leave'] = set_data
    return(dict_list)


def display_common(content):
    # list of For Approval Common Application
    set_data = []
    dict_list = {}
    if session['user_type'] == "Department Head":
        lp = find_module(f"utilities_{content}_application", {"meta.is_deleted": False, "basic_info.dm_name": session['SN'],
                                                              "basic_info.status": "For DM's Approval"}, {"meta": 0, "_id": 0})
    else:
        lp = find_module(f"utilities_{content}_application", {"meta.is_deleted": False, "basic_info.supervisor_name": session['SN'],
                                                              "basic_info.status": "For SV/SSV's Approval"}, {"meta": 0, "_id": 0})

    for rec in lp:
        full_date = dt.strptime(rec['date'], '%Y-%m-%d')
        full_date = dt.strptime(full_date.strftime('%m/%d/%Y'), '%m/%d/%Y')
        latest_data = get_sched_and_area(
            rec['date'], rec['basic_info']['ref_index'])
        remarks = get_today_sched(latest_data[0], full_date, latest_data[1])
        rec.update({
            'location': latest_data[2],
            'day_remarks': remarks['day_remarks']
        })
        set_data.append(rec)

    dict_list[content] = set_data
    return(dict_list)


def archived_leave():
    # list of For Archived Leave Application
    date_now = dt.now() - timedelta(hours=0, minutes=60)
    set_data = []
    dict_list = {}
    is_expired = 0
    if session['user_type'] == "Administrator":
        lp = find_module("utilities_leave_application", {"basic_info.effective_end": {"$ne": ""}},
                         {"meta": 0, "_id": 0})
    elif session['user_type'] == "Department Head":
        lp = find_module("utilities_leave_application", {"$or": [
            {"basic_info.dm_name": session['SN'],
                "basic_info.dm_remarks_1": {"$ne": ""}},
            {"basic_info.ref_index": session['index']}], "basic_info.effective_end": {"$ne": ""}},
            {"meta": 0, "_id": 0})
    else:
        lp = find_module("utilities_leave_application", {"$or": [
            {"basic_info.supervisor_name": session['SN'], "basic_info.supervisor_remarks_1": {
                "$ne": ""}},
            {"basic_info.ref_index": session['index']}], "basic_info.effective_end": {"$ne": ""}},
            {"meta": 0, "_id": 0})

    for z in lp:
        y = find_module("utilities_leave_detail", {
                        "ref_index": z['index']}, {"_id": 0})
        hours_paid = 0
        hours_not_paid = 0
        if y:
            for x_item in y:
                hours_paid += x_item['hours_paid']
                hours_not_paid += x_item['hours_not_paid']

        if dt.strptime(z['basic_info']['effective_end'], "%Y-%m-%d") + timedelta(days=1) < date_now:
            is_expired = 1

        z.update({
            "hours_paid": hours_paid,
            "hours_not_paid": hours_not_paid,
            "ref_index": int(z['basic_info']['ref_index']),
            "is_expired": is_expired
        })

        set_data.append(z)
    dict_list['leave'] = set_data
    return(dict_list)


def archived_common(content, index):
    # list of For Archived Common Application
    date_now = dt.now() - timedelta(hours=0, minutes=60)
    set_data = []
    dict_list = {}
    query = query_getter()
    if index:
        query.update({"index": int(index)})

    lp = find_module(f"utilities_{content}_application", query, {
                     "meta": 0, "_id": 0})

    for rec in lp:
        start_date = dt.strptime(rec["date"], "%Y-%m-%d")
        start_date = dt.strftime(start_date, "%m/%d/%Y")
        full_time = dt.strptime(start_date, "%m/%d/%Y")
        sched, branch, location = get_sched_and_area(
            rec["date"], rec['basic_info']['ref_index'])
        day_remarks = get_today_sched(sched, full_time, branch)
        rec['day_remarks'] = day_remarks['day_remarks']
        rec['branch'] = branch
        rec['location'] = location

        if dt.strptime(rec['basic_info']['effective_end'], "%Y-%m-%d") + timedelta(days=1) < date_now:
            is_expired = 1

        else:
            is_expired = 0
        rec['is_expired'] = is_expired
        rec['basic_info']['ref_index'] = rec['basic_info']['ref_index']
        set_data.append(dict(rec))

    dict_list[content] = set_data

    return(dict_list)


def query_getter():
    # Query for Report
    if session['user_type'] == "Administrator":
        query = {"basic_info.effective_start": {"$ne": ""}}
    elif session['user_type'] == "Department Head":
        query = {"$or": [
            {"basic_info.dm_name": session['SN'],
                "basic_info.dm_remarks_1": {"$ne": ""}},
            {"basic_info.ref_index": session['index']}], "basic_info.effective_end": {"$ne": ""}}
    else:
        query = {"$or": [
            {"basic_info.supervisor_name": session['SN'], "basic_info.supervisor_remarks_1": {
                "$ne": ""}},
            {"basic_info.ref_index": session['index']}], "basic_info.effective_end": {"$ne": ""}}

    return(query)


def display_pending():
    dict_list = {}
    for collection in ['leave', 'ob', 'ot', 'missing_logs', 'wfh', 'day_offset']:
        if session['user_type'] == "Department Head":
            lp = count_module(f'utilities_{collection}_application', {"meta.is_deleted": False, "basic_info.dm_name": session['SN'],
                                                                      "basic_info.status": "For DM's Approval"})

        else:
            lp = count_module(f'utilities_{collection}_application', {"meta.is_deleted": False, "basic_info.supervisor_name": session['SN'],
                                                                      "basic_info.status": "For SV/SSV's Approval"})

        dict_list[collection] = lp
    return(dict_list)

    for collection in collection_list:
        cursor = list(db['reference_employee'].find(search_dict))
        # return(cursor)
        col_count = 0
        for x in cursor:

            if session['user_type'] == "Department Head":
                lp = count_module(collection, {"is_deleted": False, "ref_index": str(x['index']),
                                               "status": "For DM's Approval"})

            elif session['user_type'] == "SV/DM":
                lp = count_module(collection, {"is_deleted": False, "ref_index": str(x['index']),
                                               "$or": [{"status": "For DM's Approval"}, {"status": "For SV/SSV's Approval"}]})

            else:
                lp = count_module(collection, {"is_deleted": False, "ref_index": str(
                    x['index']), "status": "For SV/SSV's Approval"})

            col_count += lp

        dict_list[collection] = col_count
        session[collection] = col_count

        tot_count += col_count

    session['pending_count'] = tot_count
    return(dict_list)
