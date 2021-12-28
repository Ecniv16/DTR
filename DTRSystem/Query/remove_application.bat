cd C:\Program Files\MongoDB\Server\4.4\bin
mongo.exe Monitoring --eval "db.utilities_leave_application.remove({});"
mongo.exe Monitoring --eval "db.utilities_leave_detail.remove({});"
mongo.exe Monitoring --eval "db.leave_attachment.remove({});"
mongo.exe Monitoring --eval "db.reference_employee_leave_credits.remove({});"
pause