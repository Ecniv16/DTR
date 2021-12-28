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
from .controllers import login_controller as lc
from bson import ObjectId 
import random

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