from app import *
from app.variables import dict_getter as dg
from app.functions import *
from app.functions import Custom_Function as cf
from app.sample import *
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
mega = Mega()


client = pymongo.MongoClient("mongodb://localhost:27017")
db = client["Monitoring"]
message = ''


class Leave:
    def __init__(self, data, total, marker, index):
        self.data = data
        self.total = total
        self.marker = marker
        self.index = index

    def check_if_vs_type(self):
        if self.data['leave_type'] == "VS":
            self.total['leave_avail'] = 8
            self.total['vs'] -= 8
        else:
            self.total['vs'] = 0
        return(self.total)

    # wp 1
    def wp_if_leave_avail_gt_working_hour(self, defaults, working_hour, date_now, batch):
        if batch == 0:
            update_query_default = {
                'hours_paid': working_hour,
            }
            update_query_total = {
                'leave_avail': self.total['leave_avail'] - working_hour
            }
        else:
            working_hour = float(self.data['no_hours_ut'])
            update_query_default = {
                'hours_paid': float(self.data['no_hours_ut']),
            }
            update_query_total = {
                'leave_avail': self.total['leave_avail'] - float(self.data['no_hours_ut'])
            }

        if self.total['leave_avail'] > working_hour and self.marker == 0:
            defaults.update(update_query_default)
            self.total.update(update_query_total)
            self.check_if_date_existing(
                defaults, working_hour, date_now, batch)

    # wp 2

    def wp_if_vl_leave_avail_gt_working_hour(self, defaults, working_hour, date_now, batch):
        if batch == 0:
            update_query_default = {
                'hours_paid': working_hour,
            }
            update_query_total = {
                'vl': self.total['vl'] - (working_hour - self.total['leave_avail']),
                'from_vl': self.total['from_vl'] + (working_hour - self.total['leave_avail']),
                'leave_avail': 0
            }
        else:
            working_hour = float(self.data['no_hours_ut'])
            update_query_default = {
                'hours_paid': float(self.data['no_hours_ut']),
            }
            update_query_total = {
                'vl': self.total['vl'] - (working_hour - self.total['leave_avail']),
                'from_vl': self.total['from_vl'] + (working_hour - self.total['leave_avail']),
                'leave_avail': 0
            }

        if self.total['leave_avail'] + self.total['vl'] > working_hour and self.marker == 0:
            defaults.update(update_query_default)
            self.total.update(update_query_total)
            self.check_if_date_existing(
                defaults, working_hour, date_now, batch)

    def wp_if_vl_gt_working_hour(self, defaults, working_hour, date_now, batch):  # wp 3
        if batch == 0:
            update_query_default = {
                'hours_paid': self.total['vl'] + self.total['leave_avail'],
                'hours_not_paid': working_hour - (self.total['vl'] + self.total['leave_avail'])
            }
            update_query_total = {
                'vl': 0,
                'from_vl': self.total['from_vl'] + update_query_default['hours_paid'],
                'leave_avail': 0
            }
        else:
            working_hour = float(self.data['no_hours_ut'])
            update_query_default = {
                'hours_paid': self.total['vl'] + self.total['leave_avail'],
                'hours_not_paid': working_hour - (self.total['vl'] + self.total['leave_avail'])
            }
            update_query_total = {
                'vl': 0,
                'from_vl': self.total['from_vl'] + defaults['hours_paid'],
                'leave_avail': 0
            }

        if self.total['vl'] > 0 and self.marker == 0:
            defaults.update(update_query_default)
            self.total.update(update_query_total)
            self.check_if_date_existing(
                defaults, working_hour, date_now, batch)

    def wp_if_marker_is_zero(self, defaults, working_hour, date_now, batch):  # wp 4
        if batch != 0:
            working_hour = float(self.data['no_hours_ut'])
        if self.marker == 0:
            defaults.update({
                'hours_paid': 0,
                'hours_not_paid': working_hour,
                'is_with_pay': 'No'
            })
            self.total.update({
                'vl': 0,
                'leave_avail': 0
            })

            self.check_if_date_existing(
                defaults, working_hour, date_now, batch)

    def check_if_date_existing(self, defaults, working_hour, date_now, batch):
        count_checker = count_module('utilities_leave_detail',
                                     {"ref_index": self.index, "date_now": date_now})
        if count_checker == 0:
            self.total['no_of_hours'] += working_hour
            self.total['days_of_leave'] += working_hour / 8
            self.total['paid'] += defaults['hours_not_paid']
            self.total['not_paid'] += defaults['is_with_pay']
            insert_leave_detail(self.index, date_now, working_hour,
                                defaults['hours_paid'], defaults['hours_not_paid'], defaults['is_with_pay'], batch)
            self.marker = 1
        return([self.total, self.marker])

    def update_of_leave_credits(self):
        update_criteria = {"ref_index": session['index']}

        query = {
            'VS': {
                f"{self.data['leave_type']}_r": self.total['vs'],
                'VL_r': self.total['vl']
            },
            'VL': {
                'VL_r': self.total['leave_avail']
            },
            'Others': {
                f"{self.data['leave_type']}_r": self.total['leave_avail'],
                'VL_r': self.total['vl']
            }

        }
        if self.data['leave_type'] not in ['VL', 'VS']:
            update_query = query['Others']
        else:
            update_query = query[self.data['leave_type']]

        result = update_one_module(
            'reference_leave_credit', update_criteria, update_query)
        return(result)


class Approval:
    def __init__(self, data, category):
        self.data = data
        self.category = category
        self.remarks = ""
        self.action = ""

    def check_approver(self):
        approver = {
            "Save SV Remarks": self.data['supervisor_remarks_1'],
            "Save DM Remarks": self.data['dm_remarks_1']
        }
        self.remarks = approver[self.data['action']]
        return(approver[self.data['action']])

    def get_effective_date(self, date_now, last_day):
        if date_now.day >= 1 and date_now.day <= 20:
            range_date_dict = get_date_range(1,date_now,last_day)
            
        

    def approval_effectivity(self):
        date_now = dt.strftime(dt.now(),"%m/%d/%Y")
        find_query = {'ref_index': int(self.data['ref_index'])}
        cursor = find_module(f'utilities_{self.category}_application', find_query, {})
        for dates in cursor:
            file_date = date_converter(dates['date_now'])
            last_day = get_last(date_now)
            file_date_details = {
                '1': {
                    'file_start': f'{cf.curr_year(file_date)}-{cf.curr_month(file_date)}-01',
                    'file_end': f'{cf.curr_year(file_date)}-{cf.curr_month(file_date)}-20'
                },
                '2': {
                    'file_start': f'{cf.curr_year(file_date)}-{cf.curr_month(file_date)}-16',
                    'file_end': f'{cf.curr_year(file_date)}-{cf.adv_month(file_date)}-05'
                }
            }
            default_dict = file_date_details['1']
            if file_date.day > 15:
                default_dict = file_date_details['2']
            #get_effective_date







def upload_to_mega(data,category,index):
    if request.files['file'].filename != "":
        uploaded_data=request.files['file']
        folder_path = "Employee_files"
        ext = uploaded_data.filename[uploaded_data.filename.find('.',0) - len(uploaded_data.filename):]
        filename = str(session['SN']) +"_"+ category + "_attachment_" +  str(index) + ext
        m = mega.login("vinceagoyaoy11@gmail.com","bdcn@001")
        folder = m.find(folder_path)

        uploaded_data.save(os.path.join(FILES_DIR,filename))

        files = m.upload(os.path.join(FILES_DIR,filename),folder[0])
        x = m.get_upload_link(files)
        db['utilities_' + category + '_application'].update_one({"index":int(index)},{"$set":{'basic_info.attachment':x}})



def check_if_sv(dict_list):
    if session['user_type'] == "Supervisor" or session['user_type'] == "Senior Supervisor":
        dict_list['basic_info']['dm_remarks_2'] = "For DM's Approval"
        dict_list['basic_info']['status'] = "For DM's Approval"
    else:
        dict_list = {}
    return(dict_list)


def insert_leave_detail(index, date_now, working_hour, hours_paid, hours_not_paid, is_with_pay, ut):
    detail_dict = {
        "ref_index": index,
        "date_now": date_now,
        "working_hour": working_hour,
        "hours_paid": hours_paid,
        "hours_not_paid": hours_not_paid,
        "is_with_pay": is_with_pay,
        "UT": ut,
        "index": int(session['index']),
        "effective_start": ""
    }
    db['utilities_leave_detail'].insert_one(detail_dict)


def compute_wp(ex, batch):
    """Compute leave with pay (whole day)"""
    start_date, end_date = "", ""
    if ex.data['from_date_wp'] != "" and batch == 0:
        start_date = dt.strptime(ex.data["from_date_wp"], "%Y-%m-%d")
        end_date = dt.strptime(ex.data["to_date_wp"], "%Y-%m-%d")
    elif ex.data['from_date_ut'] != "" and batch == 1:
        start_date = dt.strptime(ex.data["from_date_ut"], "%Y-%m-%d")
        end_date = dt.strptime(ex.data["to_date_ut"], "%Y-%m-%d")

    while start_date != "" and start_date <= end_date:
        latest_dict = get_applicable_record_now(
            'reference_employee_3', session['index'], {'meta': 0, '_id': 0}, start_date)
        sched, area = latest_dict['schedule_type'], latest_dict['area']
        sched_dict = get_today_sched(sched, start_date, area)
        working_hour = sched_dict['working_hour']
        dict_of_default = {
            'hours_paid': 0,
            'hours_not_paid': 0,
            'is_with_pay': 'Yes'
        }
        date_now = start_date.strftime("%Y-%m-%d")
        if sched_dict['day_remarks'] == "":
            ex.wp_if_leave_avail_gt_working_hour(
                dict_of_default, working_hour, date_now, batch)  # wp1
            ex.wp_if_vl_leave_avail_gt_working_hour(
                dict_of_default, working_hour, date_now, batch)  # wp2
            ex.wp_if_vl_gt_working_hour(
                dict_of_default, working_hour, date_now, batch)  # wp3
            ex.wp_if_marker_is_zero(
                dict_of_default, working_hour, date_now, batch)  # wp4
            ex.marker = 0
        start_date += timedelta(days=1)


def compute_wop(ex, batch):
    """Compute leave without pay (whole day)"""
    if ex.data['from_date_wop'] != "":
        start_date = dt.strptime(ex.data["from_date_wop"], "%Y-%m-%d")
        end_date = dt.strptime(ex.data["to_date_wop"], "%Y-%m-%d")
        while start_date <= end_date:
            latest_dict = get_applicable_record_now(
                'reference_employee_3', session['index'], {'meta': 0, '_id': 0}, start_date)
            sched, area = latest_dict['schedule_type'], latest_dict['area']
            sched_dict = get_today_sched(sched, start_date, area)
            working_hour = sched_dict['working_hour']
            dict_of_default = {
                'hours_paid': 0,
                'hours_not_paid': working_hour,
                'is_with_pay': 'No'
            }
            date_now = start_date.strftime("%Y-%m-%d")
            if sched_dict['day_remarks'] == "":
                ex.check_if_date_existing(
                    dict_of_default, working_hour, date_now, batch)
            start_date += timedelta(days=1)


def file_leave(data):
    index = count_module('utilities_leave_application', {}) + 1
    dict_list = dg('standard_dict')
    dict_list.update(dg('utilities_leave_application'))
    dict_list.update({'index': index})
    for x in dg('utilities_leave_application'):
        if x in data:
            dict_list[x] = data[x]

    dict_list.update(check_if_sv(dict_list))
    list_of_total_zero = ['from_vl', 'days_of_leave', 'no_of_hours',
                          'vl', 'leave_avail', 'vs', 'total_paid', 'total_not_paid']
    dict_of_total = {}
    for var in list_of_total_zero:
        dict_of_total[var] = 0

    insert_one_module('utilities_leave_application', dict_list)  # Insert Data
    vl_dict = get_applicable_record_now(
        'reference_leave_credit',
        session['index'],
        {'meta': 0, '_id': 0}, ''
    )
    marker = 0
    dict_of_total['vl'] = vl_dict.get('VL_r', 0)
    dict_of_total['leave_avail'] = vl_dict.get(f"{data['leave_type']}_r", 0)
    dict_of_total['vs'] = vl_dict.get('VS_r', 0)
    ex = Leave(data, dict_of_total, marker, index)
    ex.total.update(ex.check_if_vs_type())
    compute_wp(ex, 0)
    ex.marker = 0
    compute_wop(ex, 0)
    ex.marker = 0
    compute_wp(ex, 1)
    return(ex)


def leaves_module(data):

    ex = file_leave(data)
    update_criteria = {"index": ex.index}
    raw_date_list = [data['from_date_wp'], data['to_date_wp'],
                     data['from_date_wop'], data['to_date_wop'],
                     data['from_date_ut'], data['to_date_ut']]
    new_date_list = []
    for x in raw_date_list:
        if x != "":
            new_date_list.append(x)

    date_from, date_to = min(new_date_list), max(new_date_list)

    update_query = {
        'days_of_leave': ex.total['days_of_leave'],
        'from_vl': ex.total['from_vl'],
        'no_hours': ex.total['no_of_hours'],
        'date_from': date_from,
        'date_to': date_to,

    }
    update_one_module('utilities_leave_application',
                      update_criteria, update_query)  # update leave application
    ex.update_of_leave_credits()  # execute to update leave credits
    upload_to_mega(data, 'leave', ex.index)
    return("Successfully Filed")


def utilities_module(data, ref_index, collection):
    if collection == "utilities_leave_application":
        result = leaves_module(data)
    return(result)

