from flask import Flask, render_template, request, url_for, redirect, session, Blueprint



app = Flask(__name__)
app.config["SECRET_KEY"] = "averysecretkey"

from app.controller import *
from app.reports_controller import *
from app.reference_controller import *
from app.display_controller import *
from app.insert_controller import *
from app.templates.utilities.controller import *
from app.view import *

