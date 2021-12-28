from app import *
from app.functions import *
from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive

gauth = GoogleAuth()           
drive = GoogleDrive(gauth)  


def upload_file(data,category,index):
	uploaded_data=request.files['file']
	ext = uploaded_data.filename[uploaded_data.filename.find('.',0) - len(uploaded_data.filename):]
	filename = str(session['SN']) +"_"+category + "_attachment_" +  str(index) + ext
	uploaded_data.save(os.path.join("E:\\Desktop\\Back Up Folder\\DTRSystem",filename))
	file_name = filename

	upload_file_list = [file_name]
	for upload_file in upload_file_list:
		gfile = drive.CreateFile({'parents': [
			{'id': '1ut16EEKc6FYW3uOW1O3KDkrkVIlHb9Ea'}],
			"title": file_name})
		# Read file and set it as the content of this instance.
		gfile.SetContentFile("E:\\Desktop\\Back Up Folder\\DTRSystem\\"+upload_file)
		gfile.Upload() # Upload the file.
		file_list = drive.ListFile({'q': "title contains '309_leave_attachment_1.pdf' and trashed=false"}).GetList()
		x = file_list[0]['id']	
		db['utilities_' + category + '_application'].update_one({"index":int(index)},{"$set":{'basic_info.attachment':x}})



