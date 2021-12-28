import os
import pathlib
import requests
from flask import Flask, session, abort, redirect, request,render_template,flash
from google.oauth2 import id_token
from google_auth_oauthlib.flow import Flow
from pip._vendor import cachecontrol
import google.auth.transport.requests
from collections.abc import Mapping
from app import *
from pprint import pprint
from functools import wraps
import ast
import json
from bson import ObjectId
from datetime import datetime as dt
import urllib.request
from app.functions import *
from app.variables import *
from app.custom_decorator import *
from app.insert_controller import *
from app.collection_controller import *
from app.view_controller import *
from app.email_controller import *
import webbrowser
# Variable Declaration Start
app = Flask("Google Login App")
app.secret_key = "CodeSpecialist.com"

os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"

GOOGLE_CLIENT_ID = "488348668222-sd6evh7ooajgun5e061vfed88t3lkhcc.apps.googleusercontent.com"
client_secrets_file = os.path.join(pathlib.Path(__file__).parent, "client_secret.json")

flow = Flow.from_client_secrets_file(
    client_secrets_file=client_secrets_file,
    scopes=["https://www.googleapis.com/auth/userinfo.profile", "https://www.googleapis.com/auth/userinfo.email", "openid"],
    redirect_uri="http://localhost:8969/callback"
)

app = Flask(__name__, template_folder='templates',
            static_url_path='/static')
# Variable Declaration End

# Display Views for Reference Start
def view_getter(content):
    dict_list = {}
    if content == "employee":
        dict_list['employee'] ={
            "area":display_reference('area'),
            "company":display_reference('company'),
            "department":display_reference('department'),
            "holiday":display_reference('holiday'),
            "location":display_reference('location'),
            "schedule_type":display_reference('schedule_type'),
            "section": display_reference('section'),
            "user_type": display_reference('user_type'),
            "flexi": display_reference('flexi'),
            "employee": display_reference_employee()
        }  
    elif content == "location":
        dict_list['location'] = {
            "area":display_reference('area'),
            "location":display_reference('location'),
        }   
    elif content =="section":     
        dict_list['section'] = {
            "department":display_reference('department'),
            "section":display_reference('section'),
        }
    elif content =="holiday":     
        dict_list['holiday'] = {
            "area":display_reference('area'),
            "holiday":display_reference('holiday'),
        }
    elif content == "sched_location_info":
        dict_list[content] = {
            content:display_reference_employee_record(),
            "area":display_reference('area'),
            "location":display_reference('location'),
            "schedule_type":display_reference('schedule_type'),
                   
        }
    elif content == "designation_info":
        dict_list[content] = {
            content:display_reference_employee_record(),
            "company":display_reference('company'),
            "department":display_reference('department'),
            "section":display_reference('section'),
                   
        }
    elif content == "superiors":
        dict_list[content] = {
            content:get_employee_detail(5),

        }
    elif content == "email_address":
        dict_list[content] = {
            content:get_employee_detail(6),

        }
    elif content == "leave_credit":
        dict_list[content] = {
            content:get_employee_leave_credit(),                   
        }                                    
    else:           
        dict_list[content] = {
            content:display_reference(content),
        }   

    return(dict_list[content])
# Display Views for Reference End

# View Grouping : Login Related
@app.route("/login")
def login():
    authorization_url, state = flow.authorization_url()
    session["state"] = state
    return redirect(authorization_url)

@app.route("/callback")
def callback():
    flow.fetch_token(authorization_response=request.url)

    if not session["state"] == request.args["state"]:
        abort(500)  # State does not match!

    credentials = flow.credentials
    request_session = requests.session()
    cached_session = cachecontrol.CacheControl(request_session)
    token_request = google.auth.transport.requests.Request(session=cached_session)

    id_info = id_token.verify_oauth2_token(
        id_token=credentials._id_token,
        request=token_request,
        audience=GOOGLE_CLIENT_ID
    )

    session["google_id"] = id_info.get("sub")
    session["name"] = id_info.get("name")
    session["email"] = id_info.get("email")
    x = find_email(id_info.get("email"))
    if x == 0:
        flash("This email is not link to any DTR System account!")
        return redirect(url_for('login_page'))

    google_login(session["email"])
    return redirect(url_for('index'))

@app.route('/email_registration', methods=['POST','GET']) # Register Email Sending Verification Code
def email_registration():   
    if request.method == "POST":
        if request.form['action']== "Send Code":
            data = link_email(request.form)
            form = {
                'email':request.form['email'],
                'user':request.form['user'],
                'password': request.form['password']
            }
            flash("Verification Code Sent to your Email.")
            return render_template("users/email_register.html",form=form)
        else:
            data = register_email(request.form)
            if data == "1":
                flash("Your Account Has Been Verified")
                return redirect(url_for('index')) 
            else:
                flash("Incorrect Verification Code")
                form = {
                    'email':request.form['email'],
                    'user':request.form['user'],
                    'password': request.form['password']
                }
            return render_template("users/email_register.html",form=form)                  

    return render_template("users/email_register.html")

@app.route("/logout") # Sign out 
def sign_out():
    session.clear()
    return redirect(url_for('index'))

@app.route('/', methods=['POST','GET'])

def login_page(): # Login Page
    data = "data"
    remarks = ""
    session['curr_path'] = "LOGIN"
    if request.method == "POST":
        data = end_user_login(request.form)

        if data =="":
            flash('Invalid Username or Password')
            return redirect(url_for('login_page'))

        elif data == "No Email address link to this account":
            flash(data)
            form = {
                'user':request.form['user'],
                'password': request.form['password']
            }
            return render_template("users/email_register.html",form=form)
        elif data == "Please Use the updated username and password":
            flash(data)
            return redirect(url_for('login_page'))                      
        else:
            
            return redirect(url_for('index'))
    return render_template("users/login.html",data=data)
# Login Related Views End

# Main Page Details Start
@app.route('/app/profile', methods=['POST', 'GET'])
@login_is_required
def index():
    session['title'] = 'PROFILE'
    content = {
        'ref':  utilities_display("profile","","")
    }
    if session['user_type'] == 'Administrator':
        content = admin_dashboard()
        return render_template("Profile/admin.html",content=content)
    else: 

        return render_template("Profile/profile.html",content=content)


@app.route('/app/profile/<content>', methods=['POST', 'GET'])
@login_is_required
def profile_sub(content):
    session['title'] = f'PROFILE | {content.replace("_"," ").upper()}'
    ref = utilities_display("profile","","")
    data = ""  
    index = 0
    date_now = dt.now() - timedelta(hours=0, minutes=60)
    d_month = date_now.strftime("%m")
    d_year = date_now.strftime("%Y")
    if request.method == "POST":
        if request.form['action'] == "Generate":
            session['att'] = request.form['cutoff_month'].zfill(2)
            session['att_day'] = request.form['cutoff_day']
            session['att_year'] = request.form['cutoff_year']
            data = reports_view(request.form,"index")
            return render_template(f'Profile/{content}.html',ref = ref,data = data)
        elif "File" in request.form['action']:
            data = utilities_module(request.form,index,f"utilities_{content.replace('_create','')}_application")
            flash(data)
            return redirect(url_for('profile_sub',content=content)) 

        elif request.form['action'] == "Update Info":
            session['profile'] = "profile"
            data = manage_employee_data(request.form)

        elif "Cancel" in request.form['action']:
            data = utilities_module(request.form,index,"utilities_"+ content +"_application")
            return redirect(url_for('profile_sub',content=content)) 
                      
        elif "CHANGE" in request.form['action']:
            data = update_login_details(request.form)
            return redirect(url_for('index')) 

        ref = utilities_display("profile","","")
        session['post_count'] = 1

        return redirect(url_for("profile_sub",content=content))

    else:
        if session['post_count'] > 0:
            session['post_count'] = 0      
        else:
            session['att'] = d_month
            session['att_year'] = int(d_year)       
            session['att_day'] = 1
    
    return render_template(f'Profile/{content}.html',ref = ref,data = data)
# Main Page Details End

# Reference Module View Start
@app.route('/app/reference/<content>', methods=['POST','GET']) #Display Reference
@login_is_required
@admin_only
def reference(content): # Display all type of Reference
    session['title'] = f'REFERENCE | {content.replace("_"," ").upper()}'
    pending = display_pending()
    if content =="leave_credit":
        context = get_employee_leave_credit()
    else:
        context = view_getter(content)
    return render_template("reference/"+content+".html",context=context)

@app.route('/app/reference/<content>/create', methods=['POST','GET'])
@login_is_required
@admin_only
def reference_create(content):
    context = view_getter(content)
    if request.method == "POST":
        if content == "employee":
            message = insert_reference_employee(request.form, content)
            flash(message)
        else:
            message = insert_reference(request.form, content)
            flash(message)

        return redirect(url_for('reference_create',content=content))
            
    return render_template("reference/"+content+"_create.html",context=context)


@app.route('/app/reference/<content>/<index>/<mode>', methods=['POST','GET'])
@login_is_required
@admin_only
def reference_update(content,index:int,mode:str):
    if content =="employee":
        form = display_reference_employee_detail(content, index)
    else:
        form = display_reference_detail(content, index)
    
    context = view_getter(content)
    if mode =="edit":
        if request.method == "POST":
            if content == "employee":
                message = update_reference_employee(request.form, content, index)
                flash(message)
            else:
                message = update_reference(request.form, content,index)
                flash(message)
            return redirect(url_for('reference',content=content))         
    elif mode == "delete":
        if request.method == "POST":
            if content == "employee":
                message = delete_reference(request.form, 'employee_1',index)
            else:
                message = delete_reference(request.form, content,index)
            return redirect(url_for('reference',content=content))          
     
    return render_template(f"reference/{content}_{mode}.html",form=form,context=context)




@app.route('/app/utilities/upload_dtr', methods=['POST', 'GET'])
@clear_session
@admin_only
def upload_module():
    try:
        if session["index"] == "":
            return redirect(url_for('login_page'))      
        data =""
    except:
        return redirect(url_for('login_page'))  

    session['title'] = "UTILITIES | UPLOAD BIOMETRIC DATA"
    session['curr_path'] = "UTILITIES/UPLOAD_DTR"
    if request.method == "POST":
        data = upload_dtr(request.form)
        # return(str(data))
        return render_template("utilities/upload_dtr.html",data=data)
    return render_template("utilities/upload_dtr.html",data=data)

@app.route('/app/reference/employee/<index>/leave_credit/<mode>', methods=['POST','GET'])
@login_is_required
@admin_only
def reference_leave_credit(index,mode):
    session['title'] = 'REFERENCE | LEAVE CREDIT'
    pending = display_pending()
    context = get_employee_leave_credit_detail(index)
    if mode == "edit":
        if request.method == "POST":
            data = insert_reference_leave_credit(request.form,index)
            return redirect(url_for("reference_leave_credit",index=index,mode=mode))
    elif mode == "delete":
        if request.method == "POST":
            data = delete_reference(request.form,'leave_credit',request.form['ref_index'])
            return redirect(url_for("reference_leave_credit",index=index,mode=mode))
    elif mode == "upload":
        data = upload_leave_credit(request.form)
        return redirect(url_for("reference",content='leave_credit'))

    return render_template(f"reference/leave_credit_{mode}.html",context=context)




@app.route('/app/employee_record/<content>', methods=['POST','GET'])
@login_is_required
@admin_only
def employee_record(content):
    session['title'] = f'EMPLOYEE RECORD | {content.replace("_"," ").upper()}'
    context = view_getter(content)
                  
    return render_template("employee_record/"+content+".html",context=context)



@app.route('/app/employee_record/<content>/<ref_index>/delete', methods=['POST','GET'])
@login_is_required
@admin_only
def employee_record_delete(content,ref_index:int):
    if content == "sched_location_info":
        collection = "employee_3"
    else:
        collection = "employee_2"

    form = display_employee_record_detail(collection,ref_index)
    
    context =view_getter(content)
    if request.method == "POST":
        message = delete_reference(request.form, collection,ref_index)
        return redirect(url_for('employee_record',content=content))          
    return render_template("employee_record/"+content+"_delete.html",form=form,context=context)



@app.route('/app/reference/<content>/upload', methods=['POST','GET'])
@login_is_required
@admin_only
def reference_upload(content):

    if request.method == "POST":
        if content == "employee":
            message = upload_reference_employee(request.form, content)
        else:
            message = delete_reference(request.form, content,index)
        return redirect(url_for('reference',content=content))          
    return redirect(url_for('reference',content=content)) 


@app.route('/app/collection_list', methods=['POST','GET'])
@login_is_required

def show_collection():
    collection_list = print_collection()
    return render_template("controller/collection_view.html",collection_list=collection_list)

@app.route('/app/collection_list/drop/<content>', methods=['POST','GET'])
@login_is_required
def drop_collection(content):
    drop_collections(content)
    collection_list = print_collection()
    return render_template("controller/collection_view.html",collection_list=collection_list)




@app.route('/app/reports/<content>', methods=['POST','GET'])
@login_is_required
def report_module(content):
    session['title'] = f'REPORT | {content.replace("_"," ").upper()}'
    date_now = dt.now() - timedelta(hours=0, minutes=60)
    d_month = date_now.strftime("%m")
    if session["index"] == "":
        return redirect(url_for('login_page'))    
    data = "data"
    ref = ""
    if session['user_type'] == "Regular User":
        session['title'] = "403"
        return render_template("base/403.html")
    session['year'] = dt.now().year
    ref = get_reference_data()
    ref.update(view_getter('section'))
    ref.update(view_getter('company'))
    selected_emp={
        'cutoff_month':d_month.zfill(2)
    }

    # return(ref)
    if request.method == "POST":
        if content == "monthly_report":
            data = reports_view(request.form,"monthly")

        else:    
            data = reports_view(request.form,"dtr")


        if request.form['cutoff_day'] == "1":
            start_date = dt.strptime(str(request.form['cutoff_year']) + '-' + request.form['cutoff_month'] + "-01" ,"%Y-%m-%d")
            end_date = dt.strptime(str(request.form['cutoff_year']) + '-' + request.form['cutoff_month'] + "-15" ,"%Y-%m-%d")

        else:
            start_date = dt.strptime(str(request.form['cutoff_year']) + '-' + request.form['cutoff_month'] + "-16" ,"%Y-%m-%d")
            last_day = last_day_of_month(start_date)
            last_day = str(last_day.day)
            end_date = dt.strptime(str(request.form['cutoff_year']) + '-' + request.form['cutoff_month'] + "-" +str(last_day) ,"%Y-%m-%d")


        cutoff = dt.strftime(start_date,"%Y-%m-%d")  + " to " + dt.strftime(end_date,"%Y-%m-%d") 
        selected_emp = {
            "selected_emp":selected_employee(request.form),
            "cutoff_year":request.form['cutoff_year'],
            "cutoff_month":request.form['cutoff_month'],
            "cutoff_day":request.form['cutoff_day'],
            "company":request.form['company'],
            "department":request.form['department'],
            "section":request.form['section'],
            "cutoff":cutoff

        }

        
        # return(str(selected_emp))




        return render_template("reports/"+content+".html",data=data
            ,ref=ref,selected_emp=selected_emp)
            
    return render_template("reports/"+content+".html",ref=ref,selected_emp=selected_emp,data=data)


@app.route('/app/employee_files/<content>/<index>', methods=['POST','GET'])
@login_is_required
def files_module(content,index):
    if session["index"] == "":
        return redirect(url_for('login_page'))    
    data = "data"
    ref = ""
    alert = ""
    session['title'] = "PROFILE | LEAVE FORM"
    session['curr_path'] = "LEAVE FORM"
    pending = display_pending()
    try:
        ref = display_leave_form(index) 
    except:
        session['title'] = "😵😵😵"
        return render_template('base/404.html')


    return render_template("employee_files/"+content+"_form.html",ref=ref)


@app.route('/app/utilities/<content>', methods=['POST','GET'])
@login_is_required
def utilities_view(content):
    session['title'] = f'FOR APPROVAL | {content.replace("_"," ").upper()}'
    if session["index"] == "":
        return redirect(url_for('login_page'))    
    data = "data"
    ref = ""
    alert = ""
    index=""

    session['curr_path'] = ("utilities/" + content).upper()
    ref = utilities_display(content,"",index)
    # return(ref)
    pending = display_pending()
    # return(str(pending))
    if request.method == "POST":

        if request.form["action"] == "Cancel":

            data = utilities_module(request.form,index,"utilities_"+content+"_application")
            
            return redirect(url_for('utilities_view',content=content)) 
        else:
            index = request.form['ref_index']
            data = utilities_module(request.form,index,"utilities_"+content+"_application")
            # return(str(data))
            return redirect(url_for('utilities_view',content=content)) 
            # return redirect(url_for('utilities_view_detail',content="leave",index=data)) 
            
    return render_template("utilities/"+content+".html",ref=ref,data=data)


@app.route('/app/archived/<content>', methods=['POST','GET'])
@login_is_required
def archived_view(content):
    session['title'] = f'ARCHIVED | {content.replace("_"," ").upper()}'
    if session["index"] == "":
        return redirect(url_for('login_page'))    
    data = "data"
    ref = ""
    alert = ""
    index=""
    session['curr_path'] = ("ARCHIVED/" + content).upper()
    ref = utilities_display(content,"archived_",index)
    # return(str(ref))
    if request.method == "POST":
        if request.form["action"] == "Cancel":

            data = utilities_module(request.form,index,"utilities_"+content+"_application")
            
            return redirect(url_for('archived_view',content=content)) 
        else:
            index = request.form['ref_index']
            data = utilities_module(request.form,index,"utilities_"+content+"_application")
            # return(str(data))
            return redirect(url_for('archived_view',content=content)) 
            
    return render_template("archived/"+content+".html",ref=ref,data=data)

@app.route('/app/archived/<content>/<index>', methods=['POST','GET'])
@login_is_required
def archived_detail_view(content,index):
    if session["index"] == "":
        return redirect(url_for('login_page'))    
    data = "data"
    ref = ""
    alert = ""
    session['title'] = f'ARCHIVED | {content.replace("_"," ").upper()}'
    ref = utilities_display(content,"archived_",index)
    # return(str(ref))
    if request.method == "POST":
        if request.form["action"] == "Cancel":

            data = utilities_module(request.form,index,"utilities_"+content+"_application")
            
            return redirect(url_for('archived_view',content=content)) 
        else:
            index = request.form['ref_index']
            data = utilities_module(request.form,index,"utilities_"+content+"_application")
            # return(str(data))
            return redirect(url_for('archived_view',content=content)) 
            
    return render_template("archived/"+content+".html",ref=ref,data=data)




@app.route('/app/reference/<content>/history', methods=['POST','GET'])
@login_is_required
def reference_history(content):
    session['title'] = f'REFERENCE ARCHIVED | {content.replace("_"," ").upper()}'
    pending = display_pending()
    if content == "leave_credit":
        ref = get_reference_data_2()

    else:
        context = {'schedule_type':display_archive_reference(content)}
     
    return render_template("reference/"+content+"_archived.html",context=context)


@app.route('/app/utilities/<content>/<index>', methods=['POST','GET'])
@login_is_required
def utilities_view_detail(content,index):
    if session["index"] == "":
        return redirect(url_for('login_page'))    

    session['title'] = "LEAVE DETAIL"
    session['curr_path'] = "LEAVE DETAIL"
    ref = display_leave_detail(index)
    # return(ref)
    if request.method == "POST":
        data = leaves_module(request.form,index)

        return redirect(url_for('utilities_view',content="leave")) 
            
    return render_template("utilities/"+content+"_detail.html",ref=ref)    



@app.route('/app/reference/employee/details/<content>', methods=['POST','GET'])
@login_is_required
@admin_only
def monitoring(content):
    session['title'] = f"EMPLOYEE | {content.upper()}"
    context = view_getter(content)
    return render_template("monitoring/"+content+".html",context=context)