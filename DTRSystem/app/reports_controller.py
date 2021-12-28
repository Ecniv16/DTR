from app import *
import requests
from app.templates.utilities.controller import * 
from pprint import pprint
import os
import pandas as pd
import json
import xlsxwriter
import numpy_financial as npf
import pymongo
from datetime import datetime as dt
from datetime import timedelta
from dateutil.relativedelta import *
from app.functions import *
from app.variables import *
from bson import ObjectId 



def reports_view(data,content):
	# variables initial value
	remove_dict = report_remove_dict
	set_data =[]
	payroll_data = []
	acc_data = []
	dict_list ={}
	payroll_dict = {}
	delta = timedelta(days=1)
	# Checking type of report
	if content =="monthly":		
		cursor = list_of_employee(data)
		
	else:
		if content == "dtr" or content == "monthly":
			cursor = list_of_employee(data)	
		else:
			cursor = db['reference_employee_1'].find({'index':session['index']},{"index":1,"_id":0})

	for item in cursor:
		if content == "dtr" or content == "index":
			if data['cutoff_day'] == "1":
				start_date = dt.strptime(f"{data['cutoff_year']}-{data['cutoff_month']}-01", "%Y-%m-%d")
				end_date = dt.strptime(f"{data['cutoff_year']}-{data['cutoff_month']}-15", "%Y-%m-%d")
			else:
				start_date = dt.strptime(f"{data['cutoff_year']}-{data['cutoff_month']}-16", "%Y-%m-%d")
				last_day = get_last_day(start_date)	
				end_date = 	dt.strptime(f"{data['cutoff_year']}-{data['cutoff_month']}-{last_day}", "%Y-%m-%d")
		else:
			start_date = dt.strptime(f"{data['cutoff_year']}-{data['cutoff_month']}-01", "%Y-%m-%d")
			end_date  = last_day_of_month(start_date)

		
	# payroll
		basic, reg_ot, absent = 0, 0, 0
		rd_basic, rd_ot = 0, 0
		rh_basic, rh_ot = 0, 0
		rd_rh_basic, rd_rh_ot = 0, 0
		sh_basic, sh_ot = 0, 0
		sh_rd_basic, sh_rd_ot = 0, 0
		# for summary report
		lates, undertime, unfiled = 0, 0, 0
		total_lates, freq_lates = 0, 0
		total_undertime, freq_undertime = 0, 0
		total_ul = 0
		proper, improper = 0, 0
		remarks = ['SH','DO',"RD",'RH',"SH/RD","SH/DO","RH/RD","RH/DO"]
		index = item['index']	
		date_effective = dt.strftime(start_date, "%Y-%m-%d")
		end_effective = dt.strftime(end_date, "%Y-%m-%d")
		basic += add_leave_basic(index,date_effective,end_effective)
		basic += adjustment_basic(index,date_effective,end_effective)
		
		while start_date <= end_date:
			#local variable
			att_in, ob_in, logs_in, wfh_in = "","","",""
			att_out, ob_out, logs_out, wfh_out = "","","",""
			date_eff_ot,date_eff_ob,date_eff_logs,date_eff_wfh,date_eff_offset,date_eff_leave = "","","","","",""
			ob_index,ot_index,logs_index,wfh_index,offset_index,leave_index = 0, 0, 0, 0,0, 0
			first_in, last_out,offset_to = "", "",""
			paid_hour, hours_not_paid,ot_hrs = 0, 0, 0
			regular_ot, sp_basic, sp_ot = 0, 0, 0
			no_of_lates,under_time = 0, 0

			record = get_latest_record(start_date, index)
			# if record['user_type'] == "Administrator":
			# 	break
			date_now = start_date.strftime("%m/%d/%Y")

			# print(date_now,date_now,index)
			
			basis = get_today_sched(record['schedule_type'], start_date, record['area'])
			
			# Getting Biometric Data	
			att_rec = db['attendance_record'].find_one({'index':record['index'],
				'date':dt.strftime(date_converter(date_now),"%Y-%m-%d")})

			# Getting Leave Data	
			leave_rec = get_leave_application(record['index'], date_now,date_effective)

			# Getting Offset Data	
			offset_rec = db['utilities_day_offset_application'].find_one({"meta.is_deleted":False,'basic_info.status':'Approved',
				'basic_info.ref_index':record['index'],"date":start_date.strftime("%Y-%m-%d")})

			# Getting OB Data
			ob_rec = db['utilities_ob_application'].find_one({"meta.is_deleted":False,'basic_info.status':'Approved',
				'basic_info.ref_index':record['index'],"date":start_date.strftime("%Y-%m-%d")})
			
			# Getting MIL Data
			logs_rec = db['utilities_missing_logs_application'].find_one({"meta.is_deleted":False,'basic_info.status':'Approved',
				'basic_info.ref_index':record['index'],"date":start_date.strftime("%Y-%m-%d")})

			# Getting OT Data	
			ot_rec = db['utilities_ot_application'].find_one({"meta.is_deleted":False,'basic_info.status':'Approved',
				'basic_info.ref_index':record['index'],"date":start_date.strftime("%Y-%m-%d")})	

			# Getting WFH Data			
			wfh_rec = db['utilities_wfh_application'].find_one({"meta.is_deleted":False,'basic_info.status':'Approved',
				'basic_info.ref_index':record['index'],"date":start_date.strftime("%Y-%m-%d")})			
			day_remarks = basis['day_remarks']

			# assign Biometric Data
			if att_rec:
				att_in = att_rec['first_in']
				att_out = att_rec['last_out']

			# assign Offset Data
			if offset_rec:
				offset_to = offset_rec['offset_day']
				date_eff_offset = offset_rec['basic_info']['effective_start']
				offset_index = offset_rec['index']
				offset_basis = get_today_sched(record['schedule_type'], dt.strptime(offset_to, "%Y-%m-%d"), record['area'])	

			# assign Leave Application Data
			if leave_rec['sl_hl'] != '':
				leave_index = leave_rec['index']
				date_eff_leave = leave_rec['effective_start']

				if not day_remarks:
					day_remarks = leave_rec['sl_hl']
				else:
					day_remarks = f"{day_remarks}/{leave_rec['sl_hl']}"

				if leave_rec['paid_hour'] > 0:
					paid_hour = leave_rec['paid_hour']
					if date_eff_leave != date_effective:
						absent += paid_hour

				if leave_rec['proper'] == "Proper Filing":
					proper += 1
				else:
					improper += 1

			# assign OB Application Data
			if ob_rec:
				date_eff_ob = ob_rec['basic_info']['effective_start']
				ob_in = ob_rec['ob_am']
				ob_index = ob_rec['index']
				if time_conversion(ob_rec['ob_pm']) <= time_conversion("07:00"): 
					ob_out = f"{ob_rec['ob_pm']}+"
				else:
					ob_out = ob_rec['ob_pm']

			# assign Missing Logs Application Data
			if logs_rec:
				date_eff_logs = logs_rec['basic_info']['effective_start']
				logs_in = logs_rec['logs_am']
				logs_index = logs_rec['index']
				if logs_rec['logs_pm'] and time_conversion(logs_rec['logs_pm']) <= time_conversion("07:00"): 
					logs_out = f"{logs_rec['logs_pm']}+"
				else:
					logs_out = logs_rec['logs_pm']

			# assign WFH Application Data				
			if wfh_rec:
				date_eff_wfh = wfh_rec['basic_info']['effective_start']
				wfh_in = wfh_rec['wfh_am']
				wfh_index = wfh_rec['index']
				if wfh_rec['wfh_pm'] and time_conversion(wfh_rec['wfh_pm']) <= time_conversion("07:00"): 
					wfh_out = f"{wfh_rec['wfh_pm']}+"
				else:
					wfh_out = wfh_rec['wfh_pm']

			# assign OT Application Data	
			if ot_rec:
				date_eff_ot = ot_rec['basic_info']['effective_start']
				ot_hrs = ot_rec['ot_hrs']
				ot_index = ot_rec['index']

			# Initial In and Out
			list_of_times = [att_in,att_out]	

			# Checking of Effectivity 			
			if date_eff_ob == date_effective:
				list_of_times.append(ob_in)
				list_of_times.append(ob_out)
			
			if date_eff_logs == date_effective:
				list_of_times.append(logs_in)
				list_of_times.append(logs_out)

			if date_eff_wfh == date_effective:
				list_of_times.append(wfh_in)
				list_of_times.append(wfh_out)
	

			# Get The Final First In and  Last Out Applicable On this Cutoff
			first_in = get_first(list_of_times)
			last_out = get_last(list_of_times)

			
			if first_in != '' and last_out != '' and first_in == last_out:
				if time_conversion(first_in) >= time_conversion("14:00"):
					first_in =  ''
				else:
					last_out = ''

			if first_in and last_out and not offset_rec:
				if  not any(xs in day_remarks for xs in remarks):
					if record['flexi_type'] == "SV/SSV":
						working_hour = time_diff_undertime(first_in, last_out)						
						if working_hour >=360:
							working_hour -= 60						
						if working_hour < basis['working_hour'] * 60:
							under_time =  ((basis['working_hour'] * 60) - working_hour)							
							under_time = leave_vs_deduction(under_time, paid_hour)							
							absent += (under_time/480)
										
					elif record['flexi_type'] != "NO BIOMETRIC":	
						no_of_lates = time_diff_late(first_in, basis['sched_in'])
						no_of_lates = leave_vs_deduction(no_of_lates,paid_hour) 
						under_time = time_diff_undertime(last_out, basis['sched_out'])
						under_time = leave_vs_deduction(under_time,paid_hour)
						absent += (no_of_lates + under_time)/480
						
					regular_ot = get_ot_details(first_in, last_out, basis['sched_in'], basis['sched_out'], ot_hrs,False)

				else:
					ot_result = get_ot_details(first_in, last_out, basis['sched_in'], basis['sched_out'], ot_hrs,True) 
					if ot_result > 8:
						sp_basic = 8
						sp_ot = ot_result - 8
					else:
						sp_basic = ot_result
				
			elif first_in and last_out and offset_rec and date_eff_offset == date_effective:				
				if record['flexi_type'] == "SV/SSV":
					working_hour = time_diff_undertime(first_in, last_out)	
					if working_hour >=360:
						working_hour -= 60						
					if working_hour >= basis['working_hour'] * 60:
						absent -= ((offset_basis['working_hour']*60) -(no_of_lates + under_time))/480
						
					else:	
						under_time = ((basis['working_hour'] * 60) - working_hour)/480
						under_time = leave_vs_deduction(under_time, paid_hour)
						absent += under_time	

					
				elif record['flexi_type'] != "NO BIOMETRIC":					
					no_of_lates = time_diff_late(first_in, offset_basis['sched_in'])
					no_of_lates = leave_vs_deduction(no_of_lates, paid_hour)
					under_time = time_diff_undertime(last_out, offset_basis['sched_out'])
					under_time = leave_vs_deduction(under_time, paid_hour)
									
					regular_ot = get_ot_details(first_in, last_out, offset_basis['sched_in'], offset_basis['sched_out'], ot_hrs,False)
					absent -= ((offset_basis['working_hour']*60) -(no_of_lates + under_time))/480
			
				
			elif basis['working_hour'] > 0 and paid_hour == 0:

				if record['flexi_type'] != "NO BIOMETRIC":
					absent += 1	
																			
			if basis['day_remarks'] in ['RH/RD','RH/DO']:
				basic += 1
			elif basis['day_remarks'] in ['SH/RD','SH/DO']:
				basic += 1
			elif basis['day_remarks'] in ['DO']:
				basic += 1



			list_of_times = [att_in,att_out,ob_in,ob_out,logs_in,logs_out,wfh_in,wfh_out]

			first_in = get_first(list_of_times)
			last_out = get_last(list_of_times)

			if first_in != '' and last_out != '' and first_in == last_out:
				if time_conversion(first_in) >= time_conversion("14:00"):
					first_in =  ''
				else:
					last_out = ''

			if first_in and last_out and not offset_rec:
				if  not any(xs in day_remarks for xs in remarks):
					if record['flexi_type'] == "SV/SSV":
						working_hour = time_diff_undertime(first_in, last_out)
						
						if working_hour >=360:
							working_hour -= 60						
						if working_hour < basis['working_hour'] * 60:
							
							under_time =  ((basis['working_hour'] * 60) - working_hour)
													
							under_time = leave_vs_deduction(under_time, paid_hour)							

					elif record['flexi_type'] != "NO BIOMETRIC":	
						no_of_lates = time_diff_late(first_in, basis['sched_in'])
						no_of_lates = leave_vs_deduction(no_of_lates, paid_hour)
						under_time = time_diff_undertime(last_out, basis['sched_out'])
						under_time = leave_vs_deduction(under_time, paid_hour)		

					regular_ot = get_ot_details(first_in, last_out, basis['sched_in'], basis['sched_out'], ot_hrs,False)

				else:
					ot_result = get_ot_details(first_in, last_out, basis['sched_in'], basis['sched_out'], ot_hrs,True) 
					if ot_result > 8:
						sp_basic = 8
						sp_ot = ot_result - 8
					else:
						sp_basic = ot_result

				
			elif offset_rec:
				if record['flexi_type'] == "SV/SSV":
					working_hour = time_diff_undertime(last_out, first_in)
					if working_hour >=360:
						working_hour -= 60						
					if working_hour >= basis['working_hour'] * 60:
						no_of_lates = 0
						under_time = 0
				elif record['flexi_type'] != "NO BIOMETRIC":			
					no_of_lates = time_diff_late(first_in, offset_basis['sched_in'])
					no_of_lates = leave_vs_deduction(no_of_lates, paid_hour)
					under_time = time_diff_undertime(last_out, offset_basis['sched_out'])
					under_time = leave_vs_deduction(under_time, paid_hour)				
				
				regular_ot = get_ot_details(first_in, last_out, offset_basis['sched_in'], offset_basis['sched_out'], ot_hrs,False)

			if no_of_lates  > 0:
				total_lates += no_of_lates
				freq_lates  += 1
			if under_time > 0:
				total_undertime += under_time
				freq_undertime + 1
			
			dtr_rec = {
				'index': record['index'],
				'SN': record['SN'],
				'employee_id': record['employee_id'],
				'name': f"{record['last_name']}, {record['first_name']} {record['middle_name']}. {record['suffix']}",
				'department': record['department'],
				'section': record['section'],
				'area': record['area'],
				'location': record['location'],
				'date_hired': record['date_hired'],
				'schedule_type': record['schedule_type'],
				'date_now': date_now[:5],
				'offset_to': offset_to[5:].replace('-','/'),
				'day_name': basis['day_name'],
				'day_remarks': day_remarks,
				'week_num': basis['week_num'],
				'working_hour': basis['working_hour'],
				'sched_time': f"{basis['sched_in']}-{basis['sched_out']}",
				'sched_in': basis['sched_in'],
				'sched_out': basis['sched_out'],
				'no_of_lates':no_of_lates,
				'first_in':first_in,
				'last_out':last_out,
				'under_time':under_time,
				'regular_ot':regular_ot,
				'sp_basic':sp_basic,
				'sp_ot':sp_ot,
				'leave_start':date_eff_leave[5:].replace('-','/'),
				'logs_start':date_eff_logs[5:].replace('-','/'),
				'ob_start':date_eff_ob[5:].replace('-','/'),
				'ot_start':date_eff_ot[5:].replace('-','/'),
				'wfh_start':date_eff_wfh[5:].replace('-','/'),
				'offset_start':date_eff_offset[5:].replace('-','/'),
				'leave_index':leave_index,
				'logs_index':logs_index,
				'ob_index':ob_index,
				'ot_index':ot_index,
				'wfh_index':wfh_index,
				'offset_index':offset_index,
			}
			set_data.append(dtr_rec)

			start_date += delta

			if basis['working_hour']: 
				basic += 1
		if record['user_type'] == "Administrator":
			continue
		basic = round(basic,2)
		ot_adj = adjustment_ot(index,date_effective)
		reg_ot += ot_adj['reg_ot']
		rd_basic += ot_adj['rd_basic']
		rd_ot += ot_adj['rd_ot']
		rd_rh_basic += ot_adj['rd_rh_basic']
		rd_rh_ot += ot_adj['rd_rh_ot']
		rh_basic += ot_adj['rh_basic']
		rh_ot += ot_adj['rh_ot']
		sh_rd_basic += ot_adj['sh_rd_basic']
		sh_rd_ot += ot_adj['sh_rd_ot']
		sh_basic += ot_adj['sh_basic']
		sh_ot += ot_adj['sh_ot']		
		payroll_dict = {
			"employee_id": dtr_rec["employee_id"].zfill(6),
			"SN":dtr_rec["SN"],
			"name": dtr_rec['name'],
			"department":dtr_rec["department"],
			"date_hired":dtr_rec["date_hired"],
			"date_separated": "",
			"basic": basic,
			"reg_ot": reg_ot,
			"absent": absent,
			"rd_basic": rd_basic,
			"rd_ot": rd_ot,
			"rh_basic": rh_basic,
			"rh_ot": rh_ot,
			"rd_rh_basic": rd_rh_basic,
			"rd_rh_ot": rd_rh_ot,
			"sh_basic": sh_basic,
			"sh_ot": sh_ot,
			"sh_rd_basic": sh_rd_basic,
			"sh_rd_ot": sh_rd_ot,
			"index":dtr_rec['index']
		}
				
		payroll_data.append(payroll_dict)
		dict_accu = {
			"name": dtr_rec['name'],
			"total_lates":total_lates,
			"freq_lates": freq_lates,
			"proper": proper,
			"improper": improper,
			"total_ul": total_ul,
			"freq_undertime" : freq_undertime,
			"total_undertime": total_undertime,
			"index":dtr_rec['index'],
			"employee_id": dtr_rec["employee_id"].zfill(6),
			"SN":dtr_rec["SN"],

		}
		acc_data.append(dict_accu)
	dict_list['accu'] = acc_data

	dict_list['dtr'] = set_data
	dict_list['payroll'] = payroll_data			

	if content == "dtr" and session['user_type'] == "Administrator":
		xl = create_excel_file(payroll_data)
		dict_list['link'] = xl

	elif content == "monthly" and session['user_type'] == "Administrator":
		xlx = create_excel_file_x(acc_data)
		dict_list['link2'] = xlx


	return(dict_list)

def selected_employee(data):
	cursor = list_of_employee(data)
	set_data = []
	for x in cursor:	
		x.update(get_employee_list({'index':x['index'],'meta.is_deleted':False}))
		set_data.append(x)


	return(set_data)	