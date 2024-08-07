import os
from app import app, db

from flask import render_template,make_response, redirect, request, url_for, flash, send_from_directory, Flask
# from apscheduler.schedulers.background import BackgroundScheduler 
from flask_apscheduler import APScheduler 
from apscheduler.schedulers.background import BackgroundScheduler
# import pandas as pd
# import matplotlib.pyplot as mlt
from flask import current_app
# from flask_socketio import SocketIO
# from flask_socketio import emit
# import nltk
# import medspacy #do pip install medspacy
# from flask_cors import CORS, cross_origin
# from twilio.rest import Client
# import schedule
import pickle
from flask import g
import requests
from flask import jsonify, send_file,  flash, session, abort
import os
import json
from datetime import datetime, timedelta, date, time
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy.orm import joinedload
from app.models import *
from flask_login import login_user, logout_user, current_user, login_required, LoginManager
from app import login_manager
from flask_wtf.csrf import generate_csrf
from werkzeug.utils import secure_filename
from dotenv import load_dotenv
import re
from app.models import Patients, Caregivers, BloodSugarLevels, Credentials, HealthRecord, CaregiverType, Gender, CredentialType, AlertType, Alert, Medication, MedicationAudit, MealDiary, MealEntry, MealType, Nutrients, FoodOrDrink, DiabetesType, RecTime, MedicationTime, Symptom, SymptomType
from flask_migrate import Migrate

    
from functools import wraps
# import jwt
# from flask_mysqldb import MySQL
import psycopg2


load_dotenv()

# nlp = medspacy.load()

@app.route('/api/v1/csrf-token', methods=['GET'])
def get_csrf():
    return jsonify({'csrf_token': generate_csrf()})


# ACTIVE = {}
# def send_reminders(phone_number):

#  responseData = sms.send_message(
#  {
#      "from": "Vonage APIs",
#      "to": phone_number,
#      "text": "Drink a glass of water now!",
#  }
#  )

#  if responseData["messages"][0]["status"] == "0":
#      print("Message sent successfully.")
#  else:
#      print(f"Message failed with error: {responseData['messages'][0]['error-text']}")

# def requires_auth(f):
#   @wraps(f)
#   def decorated(*args, **kwargs):
#     auth = request.headers.get('Authorization', None) # or request.cookies.get('token', None)

#     if not auth:
#       return jsonify({'code': 'authorization_header_missing', 'description': 'Authorization header is expected'}), 401

#     parts = auth.split()

#     if parts[0].lower() != 'bearer':
#       return jsonify({'code': 'invalid_header', 'description': 'Authorization header must start with Bearer'}), 401
#     elif len(parts) == 1:
#       return jsonify({'code': 'invalid_header', 'description': 'Token not found'}), 401
#     elif len(parts) > 2:
#       return jsonify({'code': 'invalid_header', 'description': 'Authorization header must be Bearer + \s + token'}), 401

#     token = parts[1]
#     try:
#         payload = jwt.decode(token, app.config['SECRET_KEY'], algorithms=["HS256"])

#     except jwt.ExpiredSignatureError:
#         return jsonify({'code': 'token_expired', 'description': 'token is expired'}), 401
#     except jwt.DecodeError:
#         return jsonify({'code': 'token_invalid_signature', 'description': 'Token signature is invalid'}), 401

#     g.current_user = user = payload
#     return f(*args, **kwargs)

#   return decorated

def patient_or_caregiver_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        patient_id = kwargs.get('pid')
        patient = Patients.query.get(patient_id)
        if not patient:
            return jsonify({'error': 'Patient not found'}), 404

        if current_user.is_authenticated:
            if current_user == patient or current_user in patient.caregivers:
                return f(*args, **kwargs)
        
        return jsonify({'error': 'Unauthorized access'}), 403
    
    return decorated_function

@login_manager.user_loader
def load_user(id):
    patient = Patients.query.filter_by(pid=id).first()
    if patient:
        return patient
    
    caregiver = Caregivers.query.filter_by(cid=id).first()
    if caregiver: 
        return caregiver
    
    return None

##
#generating a jwt token
###
# @app.route("/api/v1/generate-token")
# def generate_token():
#     timestamp = datetime.now()
#     payload = {
#         "sub": 1,
#         "iat": timestamp,
#         "exp": timestamp + timedelta(hours=24)
#     }
#     token = jwt.encode(payload, app.config['SECRET_KEY'], algorithm='HS256')
#     return token


@app.route("/test", methods=['GET'])
def test():
    return make_response({"success": "testinggggg."},200)

@app.route("/login", methods=['POST','GET'])
def login():
    if request.method =="POST":
        try:
            content = request.get_json()
            email = content['email']
            password = content['password']
            if email != None and password != None:
                patient = Patients.query.filter_by(email = email).first()
                if patient and check_password_hash(patient.password, password):
                    login_user(patient)
                    return jsonify({"success": "User logged in successfully."}),200
                    
                caregiver = Caregivers.query.filter_by(email = email).first()
                if caregiver and check_password_hash(caregiver.password, password):
                    login_user(caregiver)
                    return jsonify({"success": "User logged in successfully."}),200
                return jsonify({'error': 'Please check your credentials to ensure they are correct.'}),400
            elif email == None and password != None:
                return jsonify({"error": "Please enter the email address associated with your account."}),400
            elif email != None and password == None:
                return jsonify({"error": "Please enter the password associated with your account."}),400
            elif email == None and password == None:
                return jsonify({"error": "Please enter your email address and password in order to to login."}),400  
        except Exception as e:
            db.session.rollback()
            print(e)
            return make_response({'error': 'An error occurred during login.'},400)

@app.route('/logout', methods = ['POST','GET'])
@login_required
def logout():
    logout_user()
    return jsonify({'success': "User has been successfully logged out."}),200

@app.route('/register', methods=['POST', 'GET'])
def register():
    if request.method =="POST":
        try: 
            content = request.get_json()
            # content = request.form
            usertype = content['usertype'] # get user type
            name = content['name'] # get user full name
            username = content['username'] # get username
            dob = content['dob'] 
            dob = datetime.strptime(dob, "%m/%d/%Y").date() # convert string dob to date
            age = int((date.today() - dob).days / 365.2425) # calculate age
            #validate password
            reg = "^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*#?&])[A-Za-z\d@$!#%*?&]{6,20}$"
            pat = re.compile(reg)                
            mat = re.search(pat, content['password'])
            if mat:
                password = content['password']
            else: 
                db.session.rollback()
                return jsonify({'error': 'Password should have at least one uppercase letter, one symbol, one numeral and one lowercase letter.'}),400
            #Validate the email address
            eregex = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,7}\b'
            if(re.fullmatch(eregex, content["email"])):
                email = content['email']
            else: 
                db.session.rollback()
                return jsonify({'error': 'Please enter a valid email address.'}),400
            
            #Validate phone number
            pregex = r"^\+1\([0-9]{3}\)[0-9]{3}-[0-9]{4}$"
            validphone = re.search(pregex, content['phonenumber'])
            if validphone: 
                if Patients.query.filter_by(phonenumber=content['phonenumber']).all() ==[]:
                    phonenumber = content['phonenumber']
                else:
                    return jsonify({'error': 'This phone number is already associated with an account.'}),400
            else: 
                db.session.rollback()
                return jsonify({'error': 'Please enter a valid phone number'}),400
            
            gender = Gender.FEMALE if content['gender'].lower() == "female" else Gender.MALE #get gender. Add non-binary too just in case      
            consentForData = content['consentForData'].lower()
            if usertype == 'Patient':
                caregiver = None
                if Patients.query.filter_by(username = username).first() is not None:#check if their username has been taken already
                    db.session.rollback()
                    return jsonify({'error': 'Username already exists'}), 400
                
                if Patients.query.filter_by(name = name).first() is not None: #check the user exists
                    db.session.rollback()
                    return jsonify({'error': 'User is already registered.'}),400 # redirect them to login screen
                else:
                    weight = int(content['weight']) # get weight
                    height = float(content['height'])
                    isSmoker = content['isSmoker'].lower() == "yes"
                    isDrinker = content['isDrinker'].lower() =="yes"
                    hasHighBP = content['hasHighBP'].lower() =="yes"
                    hasHighChol = content['hasHighChol'].lower() =="yes"
                    hasHeartDisease = content['hasHeartDisease'].lower() == "yes"
                    hadHeartAttack = content['hadHeartAttack'].lower() == "yes"
                    hasTroubleWalking = content['hasTroubleWalking'].lower() == "yes"
                    hadStroke =content['hadStroke'].lower() == "yes" 
                    weightUnits = content['weightUnits']
                    heightUnits = content['heightUnits']
                    diabetesType= DiabetesType.TYPEONE if content['diabetesType'].lower() == "type one" else DiabetesType.TYPETWO
                    # bloodSugarlevels = []
                    # bloodPressurelevels = []
                    if age and dob and email and consentForData and name and username and password and phonenumber and gender:
                        patient = Patients(age,dob,email,consentForData, name, username, password,phonenumber, gender)
                        db.session.add(patient)
                        db.session.commit()
                        patient= Patients.query.filter_by(name=name).first()
                    else:
                        return jsonify({'error': 'Please enter all your credentials in order to'}),400
                        
                    healthrecord = HealthRecord(age, weight,weightUnits, height, heightUnits, diabetesType,isSmoker, isDrinker, hasHighBP, hasHighChol, hasHeartDisease, hadHeartAttack, hadStroke, hasTroubleWalking, [], [], patient.get_id())
                    db.session.add(healthrecord)
                    db.session.commit()
                    return jsonify({'success': 'User created successfully'}),201
            elif usertype == "Family Member" or usertype == "Doctor" or usertype == "Nurse":
                if usertype =="Family Member":
                    caregivertype = CaregiverType.FAMILY
                    if Caregivers.query.filter_by(username = username).first():#check if their username has been taken already
                        db.session.rollback()
                        return jsonify({'error': 'Username already exists'}),400
                
                    if Caregivers.query.filter_by(name = name).first(): #check the user exists
                        db.session.rollback()
                        return jsonify({'error': 'User is already registered.'}), 400 # redirect them to login screen
                    else:
                        caregiver = Caregivers(name, username,caregivertype , age, dob, email, password, phonenumber, gender, consentForData)
                        db.session.add(caregiver)
                        db.session.commit()
                        return jsonify({'success': 'User has been successfully registered.'}), 200
                elif usertype =="Doctor":
                    caregivertype = CaregiverType.DOCTOR
                    if Caregivers.query.filter_by(username = username).first():#check if their username has been taken already
                        db.session.rollback()
                        return jsonify({'error': 'Username already exists'}), 400
                
                    if Caregivers.query.filter_by(name = name).first(): #check the user exists
                        db.session.rollback()
                        return jsonify({'error': 'User is already registered.'}), 400 # redirect them to login screen
                    else:
                        caregiver = Caregivers(name, username,caregivertype , age, dob, email, password, phonenumber, gender, consentForData)
                        db.session.add(caregiver)
                        db.session.commit()
                        return jsonify({'success': 'User has been successfully registered.'}), 200
                elif usertype =="Nurse":
                    caregivertype = CaregiverType.NURSE
                    if Caregivers.query.filter_by(username = username).first():#check if their username has been taken already
                        db.session.rollback()
                        return jsonify({'error': 'Username already exists'}),400
                
                    if Caregivers.query.filter_by(name = name).first(): #check the user exists
                        db.session.rollback()
                        return jsonify({'error': 'User is already registered.'}), 400 # redirect them to login screen
                    else:
                        caregiver = Caregivers(name, username,caregivertype , age, dob, email, password, phonenumber, gender, consentForData)
                        db.session.add(caregiver)
                        db.session.commit()
                        return jsonify({'success': 'User has been successfully registered.'}),200
        except Exception as e:
            db.session.rollback()
            print(e)
            return make_response({'error': 'An error has occurred'},400)


            # elif usertype.lower == "doctor" or usertype.lower() =="nurse":
            #     caregivertype = CaregiverType.DOCTOR if usertype == "Doctor" else CaregiverType.NURSE
            #     files = request.files.getlist("file") 
            #     # files = content['file'].data
            #     # if Caregivers.query.filter_by(username = username).first():#check if their username has been taken already
            #     #     db.session.rollback()
            #     #     return make_response({'error': 'Username already exists'}, 400)
                
            #     if Caregivers.query.filter_by(name = name).first(): #check the user exists
            #         db.session.rollback()
            #         return make_response({'error': 'User is already registered.'}, 400) # redirect them to login screen
            #     caregiver = Caregivers(name, username,caregivertype , age, dob, email, password, phonenumber, gender, consentForData)
            #     db.session.add(caregiver)
            #     db.session.commit()
            
            #     if usertype == "Doctor" and len(files) < 2:
            #         db.session.rollback()
            #         return make_response({'error': 'Please upload both your MBBS degree certificate and your Medical License.'}, 400)

            #     db.session.commit()
            #     return make_response({'success': f'User has been successfully registered. Please allow 3 days for validation.'}, 201)

# @app.route('uploadFiles/<cid>', methods=['POST'])
# def upload(cid):
#     if request.method =="POST":
#         try:
#             for upload in request.files.getlist('file'):
#                 print(upload)
#                 print("{} is the file name".format(upload.filename))
#                 filename = upload.filename
#                 if isAllowedFile(filename):
#                     print("File supported.")
#                 else:
#                     return make_response({'error': 'Files uploaded are not supported'})
#                 image.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
#         except Exception as e:
#             db.session.rollback()
#             print(e)
#             return make_response({'error': 'An error has occurred'},400)

            

@app.route("/recordBloodSugar/<pid>", methods=['POST','GET']) # patient personally adds their recordBloodSugar Levels
@login_required
@patient_or_caregiver_required
def recordBloodSugar(pid):
    if request.method =="POST":
        try: 
            content = request.get_json()
            bloodSugarLevel = int(content['bloodSugarLevel'])
            unit = content['unit']
            dateAndTimeRecorded = content['dateAndTimeRecorded']
            dateAndTimeRecorded = datetime.strptime(dateAndTimeRecorded, "%m/%d/%Y %H:%M").date()
            notes = content['notes']
            creator = current_user.name
            print(creator)
            patient= Patients.query.filter_by(pid=pid).first()
            isCreatorReal = (Patients.query.filter_by(name=creator).first() is not None) or (Caregivers.query.filter_by(name=creator).first() is not None) 
            if isCreatorReal:
                if patient: 
                    hrid =HealthRecord.query.filter_by(patient_id=pid).first().hrid
                    if content['confirm'].lower()=="yes":
                        bloodsugarlevel = BloodSugarLevels(int(bloodSugarLevel), unit, dateAndTimeRecorded, pid, hrid, notes, creator)
                        db.session.add(bloodsugarlevel)
                        db.session.commit() #Modify this to allow it to update the Health record
                        # if 
                        return make_response({'success': 'Blood Sugar Level Recorded Successfully'},201)      
                db.session.rollback()
                return make_response({'error': 'Patient does not exist'},400)
            db.session.rollback()
            return make_response({'error': 'The user attempting to create the blood pressure record does not exist.'},400)
        except Exception as e:
            db.session.rollback()
            print(e)
            return make_response({'error': 'An error has occurred'},400)


     
@app.route("/recordBloodPressure/<pid>", methods=['POST', 'GET']) # patient personally adds their recordBloodSugar Levels
@login_required
@patient_or_caregiver_required
def recordBloodPressure(pid):
    if request.method =="POST":
        try: 
            content = request.get_json()
            bloodPressureLevel = content['bloodPressureLevel']
            unit = content['unit']
            dateAndTimeRecorded = content['dateAndTimeRecorded']
            dateAndTimeRecorded = datetime.strptime(dateAndTimeRecorded, "%m/%d/%Y %H:%M").date()
            notes = content['notes']
            creator = current_user.name
            patient= Patients.query.filter_by(pid=pid).first()
            isCreatorReal = (Patients.query.filter_by(name=creator).first() is not None) or (Caregivers.query.filter_by(name=creator).first() is not None) 
            if isCreatorReal:
                if patient: 
                    hrid = HealthRecord.query.filter_by(patient_id=pid).first().hrid
                    print(hrid)
                    if content['confirm'].lower() == "yes":
                        bloodpressurelevel = BloodPressureLevels(int(bloodPressureLevel), unit, dateAndTimeRecorded,creator,pid, hrid, notes)
                        db.session.add(bloodpressurelevel)
                        db.session.commit() #Modify this to allow it to update the Health record
                        return make_response({'success': 'Blood Pressure Level Recorded Successfully'},201)
                db.session.rollback()
                return make_response({'error': 'Patient does not exist'},400)
            return make_response({'error': 'The user attempting to create the blood pressure record does not exist.'},400)
        except Exception as e: 
            db.session.rollback()
            print(e)
            return make_response({'error': 'An error has occurred'},400)

# @socketio.on('connect')
def scheduleAlert(alrt):
    with app.app_context():
        alert = db.session.query(Alert).filter_by(aid=alrt.aid).first()
        if alert != None:
            current_time = datetime.now().time().strftime("%I:%M %p")
            alert_time = alert.time.strftime("%I:%M %p")
            if current_time == alert_time:
                print(alrt.msg)
                # emit('server_response', {'data': alrt.msg}) #uncomment when react app has been set up. see bottom for possible react stuff 
                return make_response({"success": alrt.msg})
            else:
                print("Not yet")


@app.route("/createMedicationReminder/<pid>", methods=['POST']) #creates a medication
@login_required
@patient_or_caregiver_required
def createMedicationReminder(pid):
    if request.method =="POST":
        try:
            content = request.get_json()
            name = content['name']
            unit = content['unit']
            recommendedFrequency = int(content['recommendedFrequency']) 
            recTime =RecTime.BEFOREMEAL if content['recTime'].lower() =="before meals" else RecTime.AFTERMEAL
            inventory = content['inventory']
            amount= int(content['amount'])
            creator = current_user.name
            print(creator)
            patient= Patients.query.filter_by(pid=pid).first() is not None
            isCreatorReal = (Patients.query.filter_by(name=creator).first() is not None) or (Caregivers.query.filter_by(name=creator).first() is not None) 
            if isCreatorReal:
                if patient:
                    patient =Patients.query.filter_by(pid=pid).first()
                    if Medication.query.filter_by(name=name).first() == None:
                        medication = Medication(name, unit, recommendedFrequency,recTime,amount,inventory, pid, creator, creator)
                        db.session.add(medication)
                        db.session.commit() 
                        medication2=Medication.query.filter_by(name=name).first()
                        print(medication2)
                        for i in range(1, recommendedFrequency+1):
                            timekey = 'time' + str(i)
                            time = datetime.strptime(content[(timekey)], '%I:%M %p').time() if content[(timekey)] != None else "Time value missing"
                            if time != "Time value missing":
                                medTime = MedicationTime(time,medication2.mid)
                                db.session.add(medTime)
                                db.session.commit()
                                if content['confirm'].lower() == "yes":
                                    print(medication2)
                                    alrt=Alert("Hi "+patient.username+"! It's "+ content[(timekey)]+ ". Time to take your "+ medication2.name + " medication.", AlertType.MEDICATION, time, pid, medication2.mid)
                                    db.session.add(alrt)
                                    db.session.commit()
                                else:
                                    medication=Medication.query.filter_by(name=name).first()
                                    db.session.delete(alrt)
                                    db.session.delete(medication)
                                # job_id = f"medScheduler_{alrt.aid}"
                                # scheduler.add_job(scheduleAlert, trigger = "interval", seconds=30, id = job_id + str(i), args=[alrt] )
                            else:
                                db.session.rollback()
                                return make_response({'error': 'Time value missing'},400)
                        
                        
                        alerts= db.session.query(Alert).filter_by(mid=medication.mid).all()
                        for alert in alerts:
                            if content['confirm'].lower() == "yes":
                                job_id = f"medScheduler_{alert.aid}"
                                scheduler = APScheduler(scheduler=BackgroundScheduler())
                                if scheduler.get_job(job_id):
                                    scheduler.remove_job(job_id)
                                    print(job_id)
                                scheduler.add_job(func=scheduleAlert, trigger = "interval", seconds=30, args=[alert], id =job_id)
                                scheduler.start()
                                
                        return make_response({'success': 'Medication reminder has been created successfully'},200)
                    else:
                        ans = Medication.query.filter_by(name=name).first()
                        print(ans)
                        return make_response({'error': 'Medication Reminder already exist. Would you like to edit your existing medication instead?'},400)  
                return make_response({'error': 'Patient does not exist'},400)
            return make_response({'error': 'The user attempting to create the medication reminder does not exist.'},400)
        except Exception as e: 
            db.session.rollback()
            print(e)
            return make_response({'error': 'An error has occurred'},400)
     
@app.route("/editMedicationReminder/<pid>/<mid>", methods=['PUT', 'GET', 'DELETE'])
@login_required
@patient_or_caregiver_required
def editMedicationReminder(pid,mid):
    if request.method =="PUT":
        try:
            content = request.get_json()
            medication = Medication.query.filter_by(mid=mid).first()
            if medication != None:
                alerts= Alert.query.filter_by(mid=mid)
                patient = Patients.query.filter_by(pid=pid).first()
                medication.name = content['name'] if content['name'] != None else medication.name
                medication.unit = content['unit'] if content['unit'] != None else medication.unit
                medication.recommendedFrequency = content['recommendedFrequency'] if content['recommendedFrequency'] != None else medication.recommendedFrequency
                medication.amount = int(content['amount']) if content['amount']  != None else medication.amount
                medication.inventory = int(content['inventory']) if content['inventory'] != None else medication.inventory
                for alert in alerts:
                    db.session.delete(alert)
                    
                for i in range(1,medication.recommendedFrequency+1):
                    timekey = 'time' + str(i)
                    time = datetime.strptime(content[(timekey)], '%I:%M %p').time() if content[(timekey)] != None else "Time value missing"
                    if time != "Time value missing":                    
                       medTime = MedicationTime(time,medication.mid)
                       db.session.add(medTime)
                       db.session.commit()
                       if content['confirm'].lower() == "yes":
                            medication=Medication.query.filter_by(name=medication.name).first()
                            alrt=Alert("Hi "+patient.username+"! It's "+ content[(timekey)]+ ". Time to take your "+ medication.name + " medication.", AlertType.MEDICATION, time, pid, medication.mid)
                            db.session.add(alrt)
                            db.session.commit()
                    else:
                            db.session.rollback()
                            return make_response({'error': 'Time value missing'},400)
                
                alerts= db.session.query(Alert).filter_by(mid=medication.mid).all()
                for alert in alerts:
                    if content['confirm'].lower() == "yes":
                        job_id = f"medScheduler_{alert.aid}"
                        scheduler = APScheduler(scheduler=BackgroundScheduler())
                        if scheduler.get_job(job_id):
                            scheduler.remove_job(job_id)
                            print(job_id)
                        scheduler.add_job(func=scheduleAlert, trigger = "interval", seconds=30, args=[alert], id =job_id)
                        scheduler.start()       
                    
                medAudit = MedicationAudit(mid, current_user.name)
                db.session.add(medAudit)
                db.session.commit()
                return make_response({'success': 'Medication reminder has been updated successfully'},200)
            return make_response({'error': 'Medication reminder does not exist.'},400)
        except Exception as e: 
            db.session.rollback()
            print(e)
            return make_response({'error': 'An error has occurred'},400)

@app.route("/viewMedicationReminders/<pid>", methods=['GET'])
@login_required
@patient_or_caregiver_required
def viewMedicationReminder(pid):
    try:
        if request.method =="GET":
            patient= Patients.query.filter_by(pid=pid).first()
            if patient != None:
                medications = Medication.query.filter_by(pid=pid).all()
                if medications != None:
                    medicationlist=[]
                    for med in medications:
                        times  = [t.time.strftime( '%I:%M %p') for t in med.reminderTimes]
                        if med.last_updated_by == None:
                            lastt= "Has not been updated."
                        else:
                            lastt = med.last_updated_by
                            
                        meds = {"id":med.mid, "medicationName": med.name, "units": med.unit, "recommendedFrequency": med.recommendedFrequency,"recommendedTime": med.recommendedTime.value ,"times":times ,"dosage":med.amount, "amountInInventory": med.inventory, "patientID":med.pid, "patientName": patient.name, "creator": med.creator, "created_at": med.created_at, "last_updated_by": lastt }
                        medicationlist.append(meds)
                    return jsonify(status = "success", medicationlist = medicationlist), 200
                return make_response({'error': 'Medication reminder does not exist.'}, 400)
            return make_response({'error': 'Patient does not exist.'},400)
    except Exception as e: 
            db.session.rollback()
            print(e)
            return make_response({'error': 'An error has occurred.'},400)    


@app.route("/viewMedicationReminder/<pid>/<mid>/", methods=['GET'])
@login_required
@patient_or_caregiver_required
def viewAMedicationReminder(pid,mid):
    try:
        if request.method =="GET":
            medication= Medication.query.filter_by(mid=mid).first()
            patient = Patients.query.filter_by(pid=pid).first()
            print(patient.name)
            if medication:
                if patient.name == current_user.name or current_user in patient.caregivers:
                    times  = [t.time.strftime( '%I:%M %p') for t in medication.reminderTimes]
                    if medication.last_updated_by == None:
                        lastt= "Has not been updated."
                    else:
                        lastt = medication.last_updated_by
                                
                    med = {"id":medication.mid, "medicationName": medication.name, "units": medication.unit, "recommendedFrequency": medication.recommendedFrequency,"recommendedTime": medication.recommendedTime.value ,"times":times ,"dosage":medication.amount, "amountInInventory": medication.inventory, "patientID":pid, "patientName": patient.name, "creator": medication.creator, "created_at": medication.created_at, "last_updated_by": lastt }
                    return jsonify(status = "success", medication = med), 200
                return make_response({'error': 'Patient does not exist.'},400)
            return make_response({'error': 'Medication reminder does not exist.'}, 400)
    except Exception as e: 
            db.session.rollback()
            print(e)
            return make_response({'error': 'An error has occurred.'},400) 
        
@app.route("/deleteMedicationReminder/<pid>/<mid>/", methods=['GET','DELETE'])
@login_required
@patient_or_caregiver_required
def deleteMedicationReminder(pid,mid):
    try:
        if request.method == "DELETE":
            medication = Medication.query.filter_by(mid=mid).first()
            patient = Patients.query.filter_by(pid=pid).first()
            if patient.name == current_user.name or current_user in patient.caregivers:
                if medication != None:
                    alerts= Alert.query.filter_by(mid=mid).all()
                    times = MedicationTime.query.filter_by(mid=mid).all()
                    db.session.delete(medication)
                    for alert in alerts:
                        db.session.delete(alert)
                    db.session.commit() 
                
                    for time in times:
                        db.session.delete(time)
                    db.session.commit()
                    if Medication.query.filter_by(mid=mid).first() == None and Alert.query.filter_by(mid=mid).all() == []:
                        return make_response({'success': 'The medication reminder has been deleted successfully.'},200)
                    else:
                        return make_response({'error': 'An error occurred during the attempt to delete this medication reminder.'},400)
                else:
                    return make_response({'error': 'Medication Reminder does not exist.'},400)
            else:
                    return make_response({'error': 'User is not authorized to delete this medication reminder.'},400)
    except Exception as e: 
            db.session.rollback()
            print(e)
            return make_response({'error': 'An error has occurred.'},400)

@app.route("/createMealEntry/<pid>", methods = ['POST'])
@login_required
@patient_or_caregiver_required
def createMealEntry(pid):
     if request.method =="POST":
        try:
            content = request.get_json()
            portiontype = content["portiontype"]
            servingSize = content['servingSize']
            date_and_time = content['date_and_time']
            date_and_time = datetime.strptime(date_and_time, "%m/%d/%Y %I:%M %p").date()
            if content['mealtype'].lower() == "beverage":
                mealtype = MealType.BEVERAGE 
            elif content['mealtype'].lower() == "breakfast":
                mealtype = MealType.BREAKFAST
            elif content['mealtype'].lower() == "lunch":
                mealtype = MealType.LUNCH
            elif content['mealtype'].lower() == "brunch":
                mealtype = MealType.BRUNCH
            elif content['mealtype'].lower() == "snack":
                mealtype = MealType.SNACK
            elif content['mealtype'].lower() == "dessert":
                mealtype = MealType.DESSERT

            if content['mealOrDrink'].lower() == "food":
                mealOrDrink = FoodOrDrink.Food
            elif content['mealOrDrink'].lower() == "drink":
                mealOrDrink = FoodOrDrink.DRINK
            else:
                mealOrDrink = FoodOrDrink.FOODANDDRINK
            
            meal = content['meal']
            creator = current_user.name
            print(creator)
            patient= Patients.query.filter_by(pid=pid).first() is not None
            isCreatorReal = (Patients.query.filter_by(name=creator).first() is not None) or (Caregivers.query.filter_by(name=creator).first() is not None) 
            if isCreatorReal and patient:
                patient =Patients.query.filter_by(pid=pid).first()
                api_url = 'https://api.calorieninjas.com/v1/nutrition?query='
                query = str(servingSize)+ " "+ portiontype + " " + meal 
                try:
                    response = requests.get(api_url + query, headers={'X-Api-Key': 'UdjAYE21RFKdvFnrUhM25g==xL6FYYElHVpuQrAJ'})
                    if response.status_code == requests.codes.ok:
                        nutrients_data = response.json().get('items', [])
                        if nutrients_data: 
                            for i in nutrients_data:
                                sugar_in_g = i['sugar_g']
                                protein_in_g = i['protein_g']
                                sodium_in_mg = i['sodium_mg']
                                calories = i['calories']
                                fat_total_g = i['fat_total_g']
                                fat_saturated_g = i['fat_saturated_g']
                                potassium_mg = i['potassium_mg']
                                cholesterol_mg = i['cholesterol_mg']
                                carbohydrates_total_g = i['carbohydrates_total_g']
                    else: 
                        return make_response({'error': response.text},response.status_code)
                    
                    if content['confirm'].lower()=="yes":
                        mealentry= MealEntry(portiontype,servingSize,date_and_time,mealtype,mealOrDrink,meal,pid)
                        db.session.add(mealentry)
                        db.session.commit()
                            
                        mealEntry = MealEntry.query.filter_by(meal=meal).first()
                        nutrients = Nutrients(sugar_in_g, protein_in_g,sodium_in_mg, calories,fat_total_g,fat_saturated_g, potassium_mg, cholesterol_mg, carbohydrates_total_g,mealEntry.meid)
                        db.session.add(nutrients)
                        db.session.commit()
                        
                        mealDiary = MealDiary(pid)
                        db.session.add(mealDiary)
                        db.session.commit()

                        mealdiary = MealDiary.query.filter_by(pid=pid).first()
                        mealdiary.allMeals.append(mealEntry)
                        return make_response({'success': 'The meal entry has been created successfully.'},200)
                except Exception as e: 
                    db.session.rollback()
                    print(e)
                    return make_response({'error': 'An error has occurred.'},400)
            elif isCreatorReal is None:
                db.session.rollback()
                return make_response({'error': 'The user attempting to create the medication reminder does not exist.'},400)
            elif patient is None:
                db.session.rollback()
                return make_response({'error': 'Patient does not exist'},400)
        except Exception as e: 
            db.session.rollback()
            print(e)
            return make_response({'error': 'An error has occurred.'},400)
   

@app.route("/editMealEntry/<pid>/<meid>", methods = ['PUT'])
@login_required
@patient_or_caregiver_required
def editMealEntry(pid,meid):    
    if request.method =="PUT":
        try:
            content = request.get_json()
            mealEntry = MealEntry.query.filter_by(meid=meid).first()
            patient = Patients.query.filter_by(pid=pid).first()
            if patient.name == current_user.name or current_user in patient.caregivers:
                mealEntry.portiontype = content['portiontype'] if content['portiontype'] != None else mealEntry.portiontype
                mealEntry.servingSize = content['servingSize'] if content['servingSize'] != None else mealEntry.servingSize
                mealEntry.meal = content['meal'] if content['meal'] != None else mealEntry.meal
                if content['mealtype'] != None:
                    if content['mealtype'].lower() == "beverage":
                        mealEntry.mealtype = MealType.BEVERAGE 
                    elif content['mealtype'].lower() == "breakfast":
                        mealEntry.mealtype = MealType.BREAKFAST
                    elif content['mealtype'].lower() == "lunch":
                        mealEntry.mealtype = MealType.LUNCH
                    elif content['mealtype'].lower() == "brunch":
                        mealEntry.mealtype = MealType.BRUNCH
                    elif content['mealtype'].lower() == "snack":
                        mealEntry.mealtype = MealType.SNACK
                    elif content['mealtype'].lower() == "dessert":
                        mealEntry.mealtype = MealType.DESSERT
                    
                if content['mealOrDrink'] != None:
                    if content['mealOrDrink'].lower() == "food":
                        mealEntry.mealOrDrink = FoodOrDrink.Food
                    elif content['mealOrDrink'].lower() == "drink":
                        mealEntry.mealOrDrink = FoodOrDrink.DRINK
                    else:
                        mealEntry.mealOrDrink = FoodOrDrink.FOODANDDRINK

                for nutrient in mealEntry.nutrients:
                    api_url = 'https://api.calorieninjas.com/v1/nutrition?query='
                    query = str(mealEntry.servingSize)+ " "+ mealEntry.portiontype + " " + mealEntry.meal 
                    try:
                        response = requests.get(api_url + query, headers={'X-Api-Key': 'UdjAYE21RFKdvFnrUhM25g==xL6FYYElHVpuQrAJ'})
                        if response.status_code == requests.codes.ok:
                            nutrients_data = response.json().get('items', [])
                            if content['confirm'].lower()=="yes":
                                if nutrients_data: 
                                    for i in nutrients_data:
                                        nutrient.sugar_in_g = i['sugar_g']
                                        nutrient.protein_in_g = i['protein_g']
                                        nutrient.sodium_in_mg = i['sodium_mg']
                                        nutrient.calories = i['calories']
                                        nutrient.fat_total_g = i['fat_total_g']
                                        nutrient.fat_saturated_g = i['fat_saturated_g']
                                        nutrient.potassium_mg = i['potassium_mg']
                                        nutrient.cholesterol_mg = i['cholesterol_mg']
                                        nutrient.carbohydrates_total_g = i['carbohydrates_total_g']
                        else: 
                            return make_response({'error': response.text},response.status_code)
                    except Exception as e: 
                        db.session.rollback()
                        print(e)
                        return make_response({'error': 'An error has occurred.'},400)
                medAudit = MealEntryAudit(meid, current_user.name)
                db.session.add(medAudit)
                db.session.commit()
                return make_response({'success': 'Meal Entry has been updated successfully'},200)
            return make_response({'error': 'User is not authorised to edit this meal entry.'},400)    
                        
        except Exception as e: 
            db.session.rollback()
            print(e)
            return make_response({'error': 'An error has occurred.'},400)     
 
@app.route("/getAllMealEntries/<pid>", methods = ['GET'])
@login_required
@patient_or_caregiver_required
def getMealEntries(pid):    
    if request.method =="GET":
        try:
            if request.method =="GET":
                patient= Patients.query.filter_by(pid=pid).first()
                mealDiary = MealEntry.query.filter_by(pid=pid).all()
                if patient is not None and mealDiary is not None:
                    meallist=[]
                    for meal in mealDiary:
                        if meal.mealtype == None:
                            mealtype = "None"
                        elif meal.mealtype == MealType.BEVERAGE:
                            mealtype = "beverage"
                        elif meal.mealtype == MealType.BREAKFAST:
                            mealtype = "breakfast"
                        elif meal.mealtype == MealType.LUNCH:
                            mealtype = "lunch"
                        elif meal.mealtype == MealType.BRUNCH:
                            mealtype = "brunch"
                        elif meal.mealtype == MealType.SNACK :
                            mealtype = "snack"
                        elif meal.mealtype == MealType.DESSERT :
                            mealtype = "dessert"
                        
                        if meal.mealOrDrink == None:
                            mealOrDrink ="None"
                        elif meal.mealOrDrink == FoodOrDrink.Food:
                            mealOrDrink = "Food"
                        elif meal.mealOrDrink == FoodOrDrink.DRINK:
                            mealOrDrink = "Drink"
                        else:
                            mealOrDrink = "Food and Drink"
                        nutrients = Nutrients.query.filter_by(meid=meal.meid).all()
                        for i in nutrients:
                            mealent = {"portiontype": meal.portiontype, "servingSize": meal.servingSize, "date_and_time":meal.date_and_time, "mealtype": mealtype, "mealOrDrink": mealOrDrink, "meal": meal.meal, "patient_id": meal.pid,"nutrients_id":i.nid,"sugar_in_g":i.sugar_in_g,"protein_in_g": i.protein_in_g, "sodium_in_mg": i.sodium_in_mg, "calories":i.calories, "fat_total_g": i.fat_total_g, "fat_saturated_g": i.fat_saturated_g, "potassium_mg": i.potassium_mg, "cholesterol_mg": i.cholesterol_mg,"carbohydrates_total_g": i.carbohydrates_total_g}
                            meallist.append(mealent)
                    return make_response({'mealentries': meallist}, 200)
                elif patient == None:
                    return make_response({'error': 'Patient does not exist'},400)
                elif mealDiary == None:
                    return make_response({'error': 'Meal Diary does exist for this user'},400)
        except Exception as e: 
            db.session.rollback()
            print(e)
            return make_response({'error': 'An error has occurred.'},400)    
        
def convertMealType(meal):
    if meal.mealtype == None:
        mealtype = "None"
    elif meal.mealtype == MealType.BEVERAGE:
        mealtype = "beverage"
    elif meal.mealtype == MealType.BREAKFAST:
        mealtype = "breakfast"
    elif meal.mealtype == MealType.LUNCH:
        mealtype = "lunch"
    elif meal.mealtype == MealType.BRUNCH:
        mealtype = "brunch"
    elif meal.mealtype == MealType.SNACK :
        mealtype = "snack"
    elif meal.mealtype == MealType.DESSERT :
        mealtype = "dessert"
    
    return mealtype

def convertMealOrDrink(meal):                       
    if meal.mealOrDrink == None:
        mealOrDrink ="None"
    elif meal.mealOrDrink == FoodOrDrink.Food:
        mealOrDrink = "Food"
    elif meal.mealOrDrink == FoodOrDrink.DRINK:
        mealOrDrink = "Drink"
    else:
        mealOrDrink = "Food and Drink"   
    
    return mealOrDrink
           
@app.route("/getWeeklyMealEntries/<pid>", methods = ['GET'])
@login_required
@patient_or_caregiver_required
def getWeeklyMealEntries(pid):    
    if request.method =="GET":
        try:
            if request.method =="GET":
                patient= Patients.query.filter_by(pid=pid).first()
                mealDiary = MealEntry.query.filter_by(pid=pid).all()
                if patient is not None and mealDiary is not None:
                    meallist=[]
                    start = date.today() - timedelta(days=date.today().weekday())
                    end = start + timedelta(days=6)
                    for meal in mealDiary:
                        if (start <= meal.date_and_time.date()) and (meal.date_and_time.date() <= end):
                            nutrients = Nutrients.query.filter_by(meid=meal.meid).all()
                            for i in nutrients:
                                mealent = {"portiontype": meal.portiontype, "servingSize": meal.servingSize, "date_and_time":meal.date_and_time, "mealtype": convertMealType(meal), "mealOrDrink": convertMealOrDrink(meal), "meal": meal.meal, "patient_id": meal.pid,"nutrients_id":i.nid,"sugar_in_g":i.sugar_in_g,"protein_in_g": i.protein_in_g, "sodium_in_mg": i.sodium_in_mg, "calories":i.calories, "fat_total_g": i.fat_total_g, "fat_saturated_g": i.fat_saturated_g, "potassium_mg": i.potassium_mg, "cholesterol_mg": i.cholesterol_mg,"carbohydrates_total_g": i.carbohydrates_total_g}
                                meallist.append(mealent)
                    return make_response({'mealentries': meallist}, 200)
                elif patient == None:
                    return make_response({'error': 'Patient does not exist'},400)
                elif mealDiary == None:
                    return make_response({'error': 'Meal Diary does exist for this user'},400)
        except Exception as e: 
            db.session.rollback()
            print(e)
            return make_response({'error': 'An error has occurred.'},400)    

@app.route("/getDailyMealEntries/<pid>", methods = ['GET'])
@login_required
@patient_or_caregiver_required
def getDailyMealEntries(pid):    
    if request.method =="GET":
        try:
            if request.method =="GET":
                patient= Patients.query.filter_by(pid=pid).first()
                mealDiary = MealDiary.query.filter_by(pid=pid).first()
                if patient != None and mealDiary != None:
                    if mealDiary.allMeals != None:
                        meallist=[]
                        for meal in mealDiary.allMeals:
                            if meal.date_and_time.date() == date.today():
                                nutrients = Nutrients.query.filter_by(nid=meal.nutrients_id).first()
                                mealent = {"portiontype": meal.portiontype, "servingSize": meal.servingSize, "date_and_time":meal.date_and_time, "mealtype": meal.mealtype, "mealOrDrink": meal.mealOrDrink, "meal": meal.meal, "patient_id": meal.pid,"nutrients_id":meal.nutrients_id,"sugar_in_g":nutrients.sugar_in_g,"protein_in_g": nutrients.protein_in_g, "sodium_in_mg": nutrients.sodium_in_mg, "calories":nutrients.calories, "fat_total_g": nutrients.fat_total_g, "fat_saturated_g": nutrients.fat_saturated_g, "potassium_mg": nutrients.potassium_mg, "cholesterol_mg": nutrients.cholesterol_mg,"carbohydrates_total_g": nutrients.carbohydrates_total_g}
                                meallist.append(mealent)
                        return make_response({'mealentries': meallist}, 200)
                elif patient == None:
                    return make_response({'error': 'Patient does not exist'},400)
                elif mealDiary == None:
                    return make_response({'error': 'Meal Diary does exist for this user'},400)
        except Exception as e: 
            db.session.rollback()
            print(e)
            return make_response({'error': 'An error has occurred.'},400)    
        
@app.route('/getMonthlyMealEntries/<pid>', methods = ['GET'])
@login_required
@patient_or_caregiver_required
def getMonthlyMealEntries(pid):    
    if request.method =="GET":
        try:
            if request.method =="GET":
                patient= Patients.query.filter_by(pid=pid).first()
                mealDiary = MealDiary.query.filter_by(pid=pid).first()
                if patient != None and mealDiary != None:
                    if mealDiary.allMeals != None:
                        meallist=[]
                        today = date.today()
                        start_month = today.replace(days=1)
                        if today.month ==12:
                            end_month = today.replace(month = 12, days = 31)
                        else:
                            end_onth = today.replace(month=today.month+1, day= 1) - timedelta(days = 1)
                            
                        for meal in mealDiary.allMeals:
                            if start_month <= meal.date_and_time.date() and meal.date_and_time.date() <= end_month:
                                nutrients = Nutrients.query.filter_by(nid=meal.nutrients_id).first()
                                mealent = {"portiontype": meal.portiontype, "servingSize": meal.servingSize, "date_and_time":meal.date_and_time, "mealtype": meal.mealtype, "mealOrDrink": meal.mealOrDrink, "meal": meal.meal, "patient_id": meal.pid,"nutrients_id":meal.nutrients_id,"sugar_in_g":nutrients.sugar_in_g,"protein_in_g": nutrients.protein_in_g, "sodium_in_mg": nutrients.sodium_in_mg, "calories":nutrients.calories, "fat_total_g": nutrients.fat_total_g, "fat_saturated_g": nutrients.fat_saturated_g, "potassium_mg": nutrients.potassium_mg, "cholesterol_mg": nutrients.cholesterol_mg,"carbohydrates_total_g": nutrients.carbohydrates_total_g}
                                meallist.append(mealent)
                        return make_response({'mealentries': meallist}, 200)
                elif patient == None:
                    return make_response({'error': 'Patient does not exist'},400)
                elif mealDiary == None:
                    return make_response({'error': 'Meal Diary does exist for this user'},400)
        except Exception as e: 
            db.session.rollback()
            print(e)
            return make_response({'error': 'An error has occurred.'},400)    

        

@app.route("/getDailyBreakfastEntries/<pid>", methods = ['GET'])
@login_required
@patient_or_caregiver_required
def getDailyBreakfastEntries(pid):    
    if request.method =="GET":
        try:
            if request.method =="GET":
                patient= Patients.query.filter_by(pid=pid).first()
                mealDiary = MealDiary.query.filter_by(pid=pid).first()
                if patient != None and mealDiary != None:
                    # allbreakfasts = 
                    if mealDiary.allMeals != None:
                        meallist=[]
                        for meal in mealDiary.allMeals:    
                            print(mealDiary)
                            if (meal.mealtype == MealType.BREAKFAST) and (meal.date_and_time.date() == date.today()):                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                       
                                nutrients = Nutrients.query.filter_by(nid=meal.nutrients_id).first()
                                print(nutrients)
                                mealent = {"portiontype": meal.portiontype, "servingSize": meal.servingSize, "date_and_time":meal.date_and_time, "mealtype": meal.mealtype, "mealOrDrink": meal.mealOrDrink, "meal": meal.meal, "patient_id": meal.pid,"nutrients_id":meal.nutrients_id,"sugar_in_g":nutrients.sugar_in_g,"protein_in_g": nutrients.protein_in_g, "sodium_in_mg": nutrients.sodium_in_mg, "calories":nutrients.calories, "fat_total_g": nutrients.fat_total_g, "fat_saturated_g": nutrients.fat_saturated_g, "potassium_mg": nutrients.potassium_mg, "cholesterol_mg": nutrients.cholesterol_mg,"carbohydrates_total_g": nutrients.carbohydrates_total_g}
                                meallist.append(mealent)
                        return make_response({'mealentries': meallist}, 200)
                    else:
                        return make_response({'error': "Meal Diary is empty."}, 400)
                elif patient == None:
                    db.session.rollback()
                    return make_response({'error': 'Patient does not exist'},400)
                elif mealDiary == None:
                    db.session.rollback()
                    return make_response({'error': 'Meal Diary does exist for this user'},400)
        except Exception as e: 
            db.session.rollback()
            print(e)
            return make_response({'error': 'An error has occurred.'},400)    

@app.route("/getDailyLunchEntries/<pid>", methods = ['GET'])
@login_required
@patient_or_caregiver_required
def getDailyLunchEntries(pid):    
    if request.method =="GET":
        try:
            if request.method =="GET":
                patient= Patients.query.filter_by(pid=pid).first()
                mealDiary = MealDiary.query.filter_by(pid=pid).first()
                if patient != None and mealDiary != None:
                    # allbreakfasts = 
                    if mealDiary.allMeals != None:
                        meallist=[]
                        for meal in mealDiary.allMeals:    
                            if (meal.mealtype == MealType.LUNCH) and (meal.date_and_time.date() == date.today()):                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                       
                                nutrients = Nutrients.query.filter_by(nid=meal.nutrients_id).first()
                                mealent = {"portiontype": meal.portiontype, "servingSize": meal.servingSize, "date_and_time":meal.date_and_time, "mealtype": meal.mealtype, "mealOrDrink": meal.mealOrDrink, "meal": meal.meal, "patient_id": meal.pid,"nutrients_id":meal.nutrients_id,"sugar_in_g":nutrients.sugar_in_g,"protein_in_g": nutrients.protein_in_g, "sodium_in_mg": nutrients.sodium_in_mg, "calories":nutrients.calories, "fat_total_g": nutrients.fat_total_g, "fat_saturated_g": nutrients.fat_saturated_g, "potassium_mg": nutrients.potassium_mg, "cholesterol_mg": nutrients.cholesterol_mg,"carbohydrates_total_g": nutrients.carbohydrates_total_g}
                                meallist.append(mealent)
                        return make_response({'mealentries': meallist}, 200)
                elif patient == None:
                    db.session.rollback()
                    return make_response({'error': 'Patient does not exist'},400)
                elif mealDiary == None:
                    db.session.rollback()
                    return make_response({'error': 'Meal Diary does exist for this user'},400)
        except Exception as e: 
            db.session.rollback()
            print(e)
            return make_response({'error': 'An error has occurred.'},400)
        
@app.route("/getDailySnackEntries/<pid>", methods = ['GET'])
@login_required
@patient_or_caregiver_required
def getDailySnackEntries(pid):    
    if request.method =="GET":
        try:
            if request.method =="GET":
                patient= Patients.query.filter_by(pid=pid).first()
                mealDiary = MealDiary.query.filter_by(pid=pid).first()
                if patient != None and mealDiary != None:
                    # allbreakfasts = 
                    if mealDiary.allMeals != None:
                        meallist=[]
                        for meal in mealDiary.allMeals:    
                            if (meal.mealtype == MealType.SNACK) and (meal.date_and_time.date() == date.today()):                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                       
                                nutrients = Nutrients.query.filter_by(nid=meal.nutrients_id).first()
                                mealent = {"portiontype": meal.portiontype, "servingSize": meal.servingSize, "date_and_time":meal.date_and_time, "mealtype": meal.mealtype, "mealOrDrink": meal.mealOrDrink, "meal": meal.meal, "patient_id": meal.pid,"nutrients_id":meal.nutrients_id,"sugar_in_g":nutrients.sugar_in_g,"protein_in_g": nutrients.protein_in_g, "sodium_in_mg": nutrients.sodium_in_mg, "calories":nutrients.calories, "fat_total_g": nutrients.fat_total_g, "fat_saturated_g": nutrients.fat_saturated_g, "potassium_mg": nutrients.potassium_mg, "cholesterol_mg": nutrients.cholesterol_mg,"carbohydrates_total_g": nutrients.carbohydrates_total_g}
                                meallist.append(mealent)
                        return make_response({'mealentries': meallist}, 200)
                elif patient == None:
                    db.session.rollback()
                    return make_response({'error': 'Patient does not exist'},400)
                elif mealDiary == None:
                    db.session.rollback()
                    return make_response({'error': 'Meal Diary does exist for this user'},400)
        except Exception as e: 
            db.session.rollback()
            print(e)
            return make_response({'error': 'An error has occurred.'},400)
        
@app.route("/getDailyBrunchEntries/<pid>", methods = ['GET'])
@login_required
@patient_or_caregiver_required
def getDailyBrunchEntries(pid):    
    if request.method =="GET":
        try:
            if request.method =="GET":
                patient= Patients.query.filter_by(pid=pid).first()
                mealDiary = MealDiary.query.filter_by(pid=pid).first()
                if patient != None and mealDiary != None:
                    # allbreakfasts = 
                    if mealDiary.allMeals != None:
                        meallist=[]
                        for meal in mealDiary.allMeals:    
                            if (meal.mealtype == MealType.BRUNCH) and (meal.date_and_time.date() == date.today()):                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                       
                                nutrients = Nutrients.query.filter_by(nid=meal.nutrients_id).first()
                                mealent = {"portiontype": meal.portiontype, "servingSize": meal.servingSize, "date_and_time":meal.date_and_time, "mealtype": meal.mealtype, "mealOrDrink": meal.mealOrDrink, "meal": meal.meal, "patient_id": meal.pid,"nutrients_id":meal.nutrients_id,"sugar_in_g":nutrients.sugar_in_g,"protein_in_g": nutrients.protein_in_g, "sodium_in_mg": nutrients.sodium_in_mg, "calories":nutrients.calories, "fat_total_g": nutrients.fat_total_g, "fat_saturated_g": nutrients.fat_saturated_g, "potassium_mg": nutrients.potassium_mg, "cholesterol_mg": nutrients.cholesterol_mg,"carbohydrates_total_g": nutrients.carbohydrates_total_g}
                                meallist.append(mealent)
                        return make_response({'mealentries': meallist}, 200)
                elif patient == None:
                    db.session.rollback()
                    return make_response({'error': 'Patient does not exist'},400)
                elif mealDiary == None:
                    db.session.rollback()
                    return make_response({'error': 'Meal Diary does exist for this user'},400)
        except Exception as e: 
            db.session.rollback()
            print(e)
            return make_response({'error': 'An error has occurred.'},400)
        
@app.route("/getDailyDessertEntries/<pid>", methods = ['GET'])
@login_required
@patient_or_caregiver_required
def getDailyDessertEntries(pid):    
    if request.method =="GET":
        try:
            if request.method =="GET":
                patient= Patients.query.filter_by(pid=pid).first()
                mealDiary = MealDiary.query.filter_by(pid=pid).first()
                if patient != None and mealDiary != None:
                    # allbreakfasts = 
                    if mealDiary.allMeals != None:
                        meallist=[]
                        for meal in mealDiary.allMeals:    
                            if (meal.mealtype == MealType.DESSERT) and (meal.date_and_time.date() == date.today()):                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                       
                                nutrients = Nutrients.query.filter_by(nid=meal.nutrients_id).first()
                                mealent = {"portiontype": meal.portiontype, "servingSize": meal.servingSize, "date_and_time":meal.date_and_time, "mealtype": meal.mealtype, "mealOrDrink": meal.mealOrDrink, "meal": meal.meal, "patient_id": meal.pid,"nutrients_id":meal.nutrients_id,"sugar_in_g":nutrients.sugar_in_g,"protein_in_g": nutrients.protein_in_g, "sodium_in_mg": nutrients.sodium_in_mg, "calories":nutrients.calories, "fat_total_g": nutrients.fat_total_g, "fat_saturated_g": nutrients.fat_saturated_g, "potassium_mg": nutrients.potassium_mg, "cholesterol_mg": nutrients.cholesterol_mg,"carbohydrates_total_g": nutrients.carbohydrates_total_g}
                                meallist.append(mealent)
                        return make_response({'mealentries': meallist}, 200)
                elif patient == None:
                    db.session.rollback()
                    return make_response({'error': 'Patient does not exist'},400)
                elif mealDiary == None:
                    db.session.rollback()
                    return make_response({'error': 'Meal Diary does exist for this user'},400)
        except Exception as e: 
            db.session.rollback()
            print(e)
            return make_response({'error': 'An error has occurred.'},400)

@app.route("/getDailyBeverageEntries/<pid>", methods = ['GET'])
@login_required
@patient_or_caregiver_required
def getDailyBeverageEntries(pid):    
    if request.method =="GET":
        try:
            if request.method =="GET":
                patient= Patients.query.filter_by(pid=pid).first()
                mealDiary = MealDiary.query.filter_by(pid=pid).first()
                if patient != None and mealDiary != None:
                    # allbreakfasts = 
                    if mealDiary.allMeals != None:
                        meallist=[]
                        for meal in mealDiary.allMeals:    
                            if (meal.mealtype == MealType.BEVERAGE) and (meal.date_and_time.date() == date.today()):                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                       
                                nutrients = Nutrients.query.filter_by(nid=meal.nutrients_id).first()
                                mealent = {"portiontype": meal.portiontype, "servingSize": meal.servingSize, "date_and_time":meal.date_and_time, "mealtype": meal.mealtype, "mealOrDrink": meal.mealOrDrink, "meal": meal.meal, "patient_id": meal.pid,"nutrients_id":meal.nutrients_id,"sugar_in_g":nutrients.sugar_in_g,"protein_in_g": nutrients.protein_in_g, "sodium_in_mg": nutrients.sodium_in_mg, "calories":nutrients.calories, "fat_total_g": nutrients.fat_total_g, "fat_saturated_g": nutrients.fat_saturated_g, "potassium_mg": nutrients.potassium_mg, "cholesterol_mg": nutrients.cholesterol_mg,"carbohydrates_total_g": nutrients.carbohydrates_total_g}
                                meallist.append(mealent)
                        return make_response({'mealentries': meallist}, 200)
                elif patient == None:
                    db.session.rollback()
                    return make_response({'error': 'Patient does not exist'},400)
                elif mealDiary == None:
                    db.session.rollback()
                    return make_response({'error': 'Meal Diary does exist for this user'},400)
        except Exception as e:  
            db.session.rollback()
            print(e)
            return make_response({'error': 'An error has occurred.'},400)

@app.route("/getAllBeveragesEntries/<pid>", methods = ['GET'])
@login_required
@patient_or_caregiver_required
def getBeverageEntries(pid):    
    if request.method =="GET":
        try:
            if request.method =="GET":
                patient= Patients.query.filter_by(pid=pid).first()
                mealDiary = MealDiary.query.filter_by(pid=pid).first()
                if patient != None and mealDiary != None:
                    # allbreakfasts = 
                    if mealDiary.allMeals != None:
                        meallist=[]
                        for meal in mealDiary.allMeals:    
                            if meal.mealtype == MealType.BEVERAGE:                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                            
                                nutrients = Nutrients.query.filter_by(nid=meal.nutrients_id).first()
                                mealent = {"portiontype": meal.portiontype, "servingSize": meal.servingSize, "date_and_time":meal.date_and_time, "mealtype": meal.mealtype, "mealOrDrink": meal.mealOrDrink, "meal": meal.meal, "patient_id": meal.pid,"nutrients_id":meal.nutrients_id,"sugar_in_g":nutrients.sugar_in_g,"protein_in_g": nutrients.protein_in_g, "sodium_in_mg": nutrients.sodium_in_mg, "calories":nutrients.calories, "fat_total_g": nutrients.fat_total_g, "fat_saturated_g": nutrients.fat_saturated_g, "potassium_mg": nutrients.potassium_mg, "cholesterol_mg": nutrients.cholesterol_mg,"carbohydrates_total_g": nutrients.carbohydrates_total_g}
                                meallist.append(mealent)
                        return make_response({'mealentries': meallist}, 200)
                elif patient == None:
                    db.session.rollback()
                    return make_response({'error': 'Patient does not exist'},400)
                elif mealDiary == None:
                    db.session.rollback()
                    return make_response({'error': 'Meal Diary does exist for this user'},400)
        except Exception as e: 
            db.session.rollback()
            print(e)
            return make_response({'error': 'An error has occurred.'},400)    

@app.route("/getAllLunchEntries/<pid>", methods = ['GET'])
@login_required
@patient_or_caregiver_required
def getLunchEntries(pid):    
    if request.method =="GET":
        try:
            if request.method =="GET":
                patient= Patients.query.filter_by(pid=pid).first()
                mealDiary = MealDiary.query.filter_by(pid=pid).first()
                if patient != None and mealDiary != None:
                    # allbreakfasts = 
                    if mealDiary.allMeals != None:
                        meallist=[]
                        for meal in mealDiary.allMeals:    
                            if meal.mealtype == MealType.LUNCH:                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                            
                                nutrients = Nutrients.query.filter_by(nid=meal.nutrients_id).first()
                                mealent = {"portiontype": meal.portiontype, "servingSize": meal.servingSize, "date_and_time":meal.date_and_time, "mealtype": meal.mealtype, "mealOrDrink": meal.mealOrDrink, "meal": meal.meal, "patient_id": meal.pid,"nutrients_id":meal.nutrients_id,"sugar_in_g":nutrients.sugar_in_g,"protein_in_g": nutrients.protein_in_g, "sodium_in_mg": nutrients.sodium_in_mg, "calories":nutrients.calories, "fat_total_g": nutrients.fat_total_g, "fat_saturated_g": nutrients.fat_saturated_g, "potassium_mg": nutrients.potassium_mg, "cholesterol_mg": nutrients.cholesterol_mg,"carbohydrates_total_g": nutrients.carbohydrates_total_g}
                                meallist.append(mealent)
                        return make_response({'mealentries': meallist}, 200)
                elif patient == None:
                    db.session.rollback()
                    return make_response({'error': 'Patient does not exist'},400)
                elif mealDiary == None:
                    db.session.rollback()
                    return make_response({'error': 'Meal Diary does exist for this user'},400)
        except Exception as e: 
            db.session.rollback()
            print(e)
            return make_response({'error': 'An error has occurred.'},400)    

@app.route("/getAllDinnerEntries/<pid>", methods = ['GET'])
@login_required
@patient_or_caregiver_required
def getDinnerEntries(pid):    
    if request.method =="GET":
        try:
            if request.method =="GET":
                patient= Patients.query.filter_by(pid=pid).first()
                mealDiary = MealDiary.query.filter_by(pid=pid).first()
                if patient != None and mealDiary != None:
                    # allbreakfasts = 
                    if mealDiary.allMeals != None:
                        meallist=[]
                        for meal in mealDiary.allMeals:    
                            if meal.mealtype == MealType.DINNER:                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                            
                                nutrients = Nutrients.query.filter_by(nid=meal.nutrients_id).first()
                                mealent = {"portiontype": meal.portiontype, "servingSize": meal.servingSize, "date_and_time":meal.date_and_time, "mealtype": meal.mealtype, "mealOrDrink": meal.mealOrDrink, "meal": meal.meal, "patient_id": meal.pid,"nutrients_id":meal.nutrients_id,"sugar_in_g":nutrients.sugar_in_g,"protein_in_g": nutrients.protein_in_g, "sodium_in_mg": nutrients.sodium_in_mg, "calories":nutrients.calories, "fat_total_g": nutrients.fat_total_g, "fat_saturated_g": nutrients.fat_saturated_g, "potassium_mg": nutrients.potassium_mg, "cholesterol_mg": nutrients.cholesterol_mg,"carbohydrates_total_g": nutrients.carbohydrates_total_g}
                                meallist.append(mealent)
                        return make_response({'mealentries': meallist}, 200)
                elif patient == None:
                    db.session.rollback()
                    return make_response({'error': 'Patient does not exist'},400)
                elif mealDiary == None:
                    db.session.rollback()
                    return make_response({'error': 'Meal Diary does exist for this user'},400)
        except Exception as e: 
            db.session.rollback()
            print(e)
            return make_response({'error': 'An error has occurred.'},400)    

@app.route("/getAllBrunchEntries/<pid>", methods = ['GET'])
@login_required
@patient_or_caregiver_required
def getBrunchEntries(pid):    
    if request.method =="GET":
        try:
            if request.method =="GET":
                patient= Patients.query.filter_by(pid=pid).first()
                mealDiary = MealDiary.query.filter_by(pid=pid).first()
                if patient != None and mealDiary != None:
                    # allbreakfasts = 
                    if mealDiary.allMeals != None:
                        meallist=[]
                        for meal in mealDiary.allMeals:    
                            if meal.mealtype == MealType.BRUNCH:                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                            
                                nutrients = Nutrients.query.filter_by(nid=meal.nutrients_id).first()
                                mealent = {"portiontype": meal.portiontype, "servingSize": meal.servingSize, "date_and_time":meal.date_and_time, "mealtype": meal.mealtype, "mealOrDrink": meal.mealOrDrink, "meal": meal.meal, "patient_id": meal.pid,"nutrients_id":meal.nutrients_id,"sugar_in_g":nutrients.sugar_in_g,"protein_in_g": nutrients.protein_in_g, "sodium_in_mg": nutrients.sodium_in_mg, "calories":nutrients.calories, "fat_total_g": nutrients.fat_total_g, "fat_saturated_g": nutrients.fat_saturated_g, "potassium_mg": nutrients.potassium_mg, "cholesterol_mg": nutrients.cholesterol_mg,"carbohydrates_total_g": nutrients.carbohydrates_total_g}
                                meallist.append(mealent)
                        return make_response({'mealentries': meallist}, 200)
                elif patient == None:
                    db.session.rollback()
                    return make_response({'error': 'Patient does not exist'},400)
                elif mealDiary == None:
                    db.session.rollback()
                    return make_response({'error': 'Meal Diary does exist for this user'},400)
        except Exception as e: 
            db.session.rollback()
            print(e)
            return make_response({'error': 'An error has occurred.'},400)    

@app.route("/getAllSnackEntries/<pid>", methods = ['GET'])
@login_required
@patient_or_caregiver_required
def getSnackEntries(pid):    
    if request.method =="GET":
        try:
            if request.method =="GET":
                patient= Patients.query.filter_by(pid=pid).first()
                mealDiary = MealDiary.query.filter_by(pid=pid).first()
                if patient != None and mealDiary != None:
                    # allbreakfasts = 
                    if mealDiary.allMeals != None:
                        meallist=[]
                        for meal in mealDiary.allMeals:    
                            if meal.mealtype == MealType.SNACK:                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                            
                                nutrients = Nutrients.query.filter_by(nid=meal.nutrients_id).first()
                                mealent = {"portiontype": meal.portiontype, "servingSize": meal.servingSize, "date_and_time":meal.date_and_time, "mealtype": meal.mealtype, "mealOrDrink": meal.mealOrDrink, "meal": meal.meal, "patient_id": meal.pid,"nutrients_id":meal.nutrients_id,"sugar_in_g":nutrients.sugar_in_g,"protein_in_g": nutrients.protein_in_g, "sodium_in_mg": nutrients.sodium_in_mg, "calories":nutrients.calories, "fat_total_g": nutrients.fat_total_g, "fat_saturated_g": nutrients.fat_saturated_g, "potassium_mg": nutrients.potassium_mg, "cholesterol_mg": nutrients.cholesterol_mg,"carbohydrates_total_g": nutrients.carbohydrates_total_g}
                                meallist.append(mealent)
                        return make_response({'mealentries': meallist}, 200)
                elif patient == None:
                    db.session.rollback()
                    return make_response({'error': 'Patient does not exist'},400)
                elif mealDiary == None:
                    db.session.rollback()
                    return make_response({'error': 'Meal Diary does exist for this user'},400)
        except Exception as e: 
            db.session.rollback()
            print(e)
            return make_response({'error': 'An error has occurred.'},400)   
        
@app.route("/getAllDessertEntries/<pid>", methods = ['GET']) #VIEW
@login_required
@patient_or_caregiver_required
def getDessertEntries(pid):    
    if request.method =="GET":
        try:
            if request.method =="GET":
                patient= Patients.query.filter_by(pid=pid).first()
                mealDiary = MealDiary.query.filter_by(pid=pid).first()
                if patient != None and mealDiary != None:
                    # allbreakfasts = 
                    if mealDiary.allMeals != None:
                        meallist=[]
                        for meal in mealDiary.allMeals:    
                            if meal.mealtype == MealType.DESSERT:                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                            
                                nutrients = Nutrients.query.filter_by(nid=meal.nutrients_id).first()
                                mealent = {"portiontype": meal.portiontype, "servingSize": meal.servingSize, "date_and_time":meal.date_and_time, "mealtype": meal.mealtype, "mealOrDrink": meal.mealOrDrink, "meal": meal.meal, "patient_id": meal.pid,"nutrients_id":meal.nutrients_id,"sugar_in_g":nutrients.sugar_in_g,"protein_in_g": nutrients.protein_in_g, "sodium_in_mg": nutrients.sodium_in_mg, "calories":nutrients.calories, "fat_total_g": nutrients.fat_total_g, "fat_saturated_g": nutrients.fat_saturated_g, "potassium_mg": nutrients.potassium_mg, "cholesterol_mg": nutrients.cholesterol_mg,"carbohydrates_total_g": nutrients.carbohydrates_total_g}
                                meallist.append(mealent)
                        return make_response({'mealentries': meallist}, 200)
                elif patient == None:
                    db.session.rollback()
                    return make_response({'error': 'Patient does not exist'},400)
                elif mealDiary == None:
                    db.session.rollback()
                    return make_response({'error': 'Meal Diary does exist for this user'},400)
        except Exception as e: 
            db.session.rollback()
            print(e)
            return make_response({'error': 'An error has occurred.'},400)  
           


@app.route("/recordSymptoms/<pid>", methods=['POST','GET']) # patient personally adds their recordBloodSugar Levels
@login_required
@patient_or_caregiver_required
def recordSymptoms(pid):
    if request.method =="POST":
        try: 
            content = request.get_json()
            notes = content['notes']
            date_and_time = content['date_and_time']
            date_and_time = datetime.strptime(date_and_time, "%m/%d/%Y %I:%M %p").date()
            patient= Patients.query.filter_by(pid=pid).first()
            if patient.name == current_user.name or current_user in patient.caregivers: 
                if content['category'] == "mood":
                    symptom_name = "Mood: " + content['severity']
                    if content['severity'].lower() == "depressed":
                        severity = 5
                        symptomType = SymptomType.MOOD
                        symptom=Symptom(symptom_name, symptomType,severity,date_and_time,notes, pid, HealthRecord.query.filter_by(patient_id=pid).first().hrid )
                        db.session.add(symptom)
                        db.session.commit()
                    elif content['severity'].lower() == "sad":
                        severity = 4
                        symptomType = SymptomType.MOOD
                        symptom=Symptom(symptom_name, symptomType,severity,date_and_time,notes, pid, HealthRecord.query.filter_by(patient_id=pid).first().hrid )
                        db.session.add(symptom)
                        db.session.commit()
                    elif content['severity'].lower() == "ok":
                        severity = 3
                        symptomType = SymptomType.MOOD
                        symptom=Symptom(symptom_name, symptomType,severity,date_and_time,notes, pid, HealthRecord.query.filter_by(patient_id=pid).first().hrid )
                        db.session.add(symptom)
                        db.session.commit() 
                    elif content['severity'].lower() == "good":
                        severity = 2
                        symptomType = SymptomType.MOOD  
                        symptom=Symptom(symptom_name, symptomType,severity,date_and_time,notes, pid, HealthRecord.query.filter_by(patient_id=pid).first().hrid )
                        db.session.add(symptom)
                        db.session.commit()
                    elif content['severity'].lower() == "excellent":
                        severity = 1
                        symptomType = SymptomType.MOOD  
                        symptom=Symptom(symptom_name, symptomType,severity,date_and_time,notes, pid, HealthRecord.query.filter_by(patient_id=pid).first().hrid )
                        db.session.add(symptom)
                        db.session.commit()
                elif content['category'].lower() == "sleep":
                    symptom_name = content['severity'] +"Sleep"
                    if content['severity'].lower() == "terrible":
                        severity = 5
                        symptomType = SymptomType.SLEEP
                        symptom=Symptom(symptom_name, symptomType,severity,date_and_time,notes, pid, HealthRecord.query.filter_by(patient_id=pid).first().hrid )
                        db.session.add(symptom)
                        db.session.commit()
                    elif content['severity'].lower() == "bad":
                        severity = 4
                        symptomType = SymptomType.SLEEP
                        symptom=Symptom(symptom_name, symptomType,severity,date_and_time,notes, pid, HealthRecord.query.filter_by(patient_id=pid).first().hrid )
                        db.session.add(symptom)
                        db.session.commit()
                    elif content['severity'].lower() == "ok":
                        severity = 3
                        symptomType = SymptomType.SLEEP
                        symptom=Symptom(symptom_name, symptomType,severity,date_and_time,notes, pid, HealthRecord.query.filter_by(patient_id=pid).first().hrid )
                        db.session.add(symptom)
                        db.session.commit()
                    elif content['severity'].lower() == "good":
                        severity = 2
                        symptomType = SymptomType.SLEEP
                        symptom=Symptom(symptom_name, symptomType,severity,date_and_time,notes, pid, HealthRecord.query.filter_by(patient_id=pid).first().hrid )
                        db.session.add(symptom)
                        db.session.commit()
                    elif content['severity'].lower() == "excellent":
                        severity = 1
                        symptomType = SymptomType.SLEEP
                        symptom=Symptom(symptom_name, symptomType,severity,date_and_time,notes, pid, HealthRecord.query.filter_by(patient_id=pid).first().hrid )
                        db.session.add(symptom)
                        db.session.commit()
                elif content['category'].lower() == "appetite":
                    symptom_name = content['severity'] +"Appetite"
                    if content['severity'].lower() == "none":
                        severity = 5
                        symptomType = SymptomType.APPETITE
                        symptom=Symptom(symptom_name, symptomType,severity,date_and_time,notes, pid, HealthRecord.query.filter_by(patient_id=pid).first().hrid )
                        db.session.add(symptom)
                        db.session.commit()
                    elif content['severity'].lower() == "less than normal":
                        severity = 4
                        symptomType = SymptomType.APPETITE
                        symptom=Symptom(symptom_name, symptomType,severity,date_and_time,notes, pid, HealthRecord.query.filter_by(patient_id=pid).first().hrid )
                        db.session.add(symptom)
                        db.session.commit()
                    elif content['severity'].lower() == "normal":
                        severity = 3
                        symptomType = SymptomType.APPETITE
                        symptom=Symptom(symptom_name, symptomType,severity,date_and_time,notes, pid, HealthRecord.query.filter_by(patient_id=pid).first().hrid )
                        db.session.add(symptom)
                        db.session.commit()
                    elif content['severity'].lower() == "more than normal":
                        severity = 2
                        symptomType = SymptomType.APPETITE 
                        symptom=Symptom(symptom_name, symptomType,severity,date_and_time,notes, pid, HealthRecord.query.filter_by(patient_id=pid).first().hrid )
                        db.session.add(symptom)
                        db.session.commit()
                    elif content['severity'].lower() == "excessive":
                        severity = 1
                        symptomType = SymptomType.APPETITE 
                        symptom=Symptom(symptom_name, symptomType,severity,date_and_time,notes, pid, HealthRecord.query.filter_by(patient_id=pid).first().hrid )
                        db.session.add(symptom)
                        db.session.commit()
                elif content['category'].lower() == "other":
                    symptom_name = content['symptom_name'].lower()
                    severity = int(content['severity'])
                    symptomType = SymptomType.OTHER
                #     symptoms = nlp(symptom_name) # handle this some other way b
                #     vals = [{"text":i.text, "label": i.label} for i in symptoms.ent]
                #     for j in vals: 
                #         if j['label'] == "SYMPTOM":
                #             symptom_name = j['text']
                    symptom=Symptom(symptom_name, symptomType,severity,date_and_time,notes, pid, HealthRecord.query.filter_by(patient_id=pid).first().hrid )
                    db.session.add(symptom)
                    db.session.commit()
                
                return make_response({'success': 'Symptom has been created successfully'},200)
            return make_response({'error': 'User is not authorised to edit this meal entry.'},400)
        except Exception as e: 
            db.session.rollback()
            print(e)
            return make_response({'error': 'An error has occurred.'},400)  

@app.route("/deleteSymptom/<pid>/<sid>", methods=['GET','DELETE'])
@login_required
@patient_or_caregiver_required
def deleteSymptom(pid,sid):
    try:
        if request.method == "DELETE":
            symptom = Symptom.query.filter_by(sid=sid).first()
            patient = Patients.query.filter_by(pid=pid).first()
            if patient.name == current_user.name or current_user in patient.caregivers:
                if symptom != None:
                    # hr=HealthRecord.query.filter_by(hrid = patient.hrid) 
                    db.session.delete(symptom)
                    db.session.commit()
                    if Symptom.query.filter_by(sid=sid).first() == None:
                        return make_response({'success': 'The symptom has been deleted successfully.'},200)
                        # print(hr.symptoms)
                    else:
                        return make_response({'error': 'An error occurred during the attempt to delete this symptom.'},400)
            else:
                return make_response({'error': 'User is not authorized to delete this medication reminder.'},400)

            # hr=HealthRecord.query.filter_by(hrid = symptom.hrid)    
            # for i in hr.symptoms:
            #     print(i)
            #     if i.sid == sid:
            #         hr.symptoms.remove(i)
            #         db.session.commit()
    except Exception as e: 
            db.session.rollback()
            print(e)
            return make_response({'error': 'An error has occurred.'},400)

@app.route("/searchCaregiver/<pid>", methods=['GET', "POST"])
@login_required
@patient_or_caregiver_required
def searchCaregiver(pid):
    if request.method =="POST":
        try:
            content = request.get_json()
            search = content['search']
            patient = Patients.query.filter_by(pid=pid).first()
            if patient.name == current_user.name or current_user in patient.caregivers:
                if Caregivers.query.filter_by(name = search).all() != None:
                    caregiver = Caregivers.query.filter_by(name = search).first()
                    caregiver = {"caregiver_id" : caregiver.cid, "name": caregiver.name, "username":caregiver.username,"type": caregiver.type.value}
                    return make_response({"caregiver":caregiver})
                elif Caregivers.query.filter_by(username = search).first():
                    caregiver = Caregivers.query.filter_by(username = search).first()
                    caregiver = {"caregiver_id" : caregiver.cid, "name": caregiver.name, "username":caregiver.username,"type": caregiver.type.value}
                    return make_response({"caregiver" : caregiver})
                elif Patients.query.filter_by(username = search).first() or Patients.query.filter_by(name = search).first():
                    return make_response({'error': 'User is not a registered Caregiver.'},400)
                else: 
                    return make_response({'error': 'Caregiver was not found'},404)
        except Exception as e: 
            db.session.rollback()
            print(e)
            return make_response({'error': 'An error has occurred.'},400)    

@app.route("/addCaregiver/<pid>/<cid>", methods=['POST'])
@login_required
@patient_or_caregiver_required
def addCaregiver(pid,cid):
    if request.method =="POST":
        try:
            content = request.get_json()
            patient = Patients.query.filter_by(pid=pid).first()
            if patient.name == current_user.name or current_user in patient.caregivers:
                if Caregivers.query.filter_by(cid = cid).first() != None:
                    caregiver = Caregivers.query.filter_by(cid = cid).first()
                    patient.caregivers.append(caregiver)
                    db.session.commit()
                    return make_response({'success': 'Caregiver was added successfully.'},200)
                elif Patients.query.filter_by(cid = cid).first() or Patients.query.filter_by(cid = cid).first():
                    return make_response({'error': 'User is not a registered Caregiver.'},400)
                else: 
                    return make_response({'error': 'Caregiver was not found'},404)
            else:
                    return make_response({'error': 'User is not authorized to add a caregiver for '+ patient.name },400)
        except Exception as e: 
            db.session.rollback()
            print(e)
            return make_response({'error': 'An error has occurred.'},400)

@app.route("/removeCaregiver/<pid>/<cid>", methods=['DELETE'])
@login_required
@patient_or_caregiver_required
def removeCaregiver(pid,cid):
    if request.method =="DELETE":
        try:
            caregiver = Caregivers.query.filter_by(cid = cid).first()
            if caregiver != None:
                patient = Patients.query.filter_by(pid=pid).first()
                if  patient != None and caregiver in patient.caregivers:
                    patient.caregivers.remove(caregiver)
                    db.session.commit()
                    caregiver = Caregivers.query.filter_by(cid = cid).first()
                    return make_response({"success": "Caregiver has been removed successfully"})
                return make_response({'error': 'You are not authorised to remmove the caregiver.'},400)
            return make_response({'error': 'Caregiver not found'},404)    
        except Exception as e: 
            db.session.rollback()
            print(e)
            return make_response({'error': 'An error has occurred.'},400) 
        


@app.route("/dailyNutritionalReport/<pid>/<month>/<day>/<year>", methods=['GET'])
@login_required
@patient_or_caregiver_required
def dailyNutritionalReport(pid, month, day, year):
    try:
        date_str = f"{month}/{day}/{year}"
        report_date = datetime.strptime(date_str, '%m/%d/%Y').date()
        patient = Patients.query.filter_by(pid=pid).first()
        if not patient:
            return make_response({'error': 'Patient not found'}, 404)

        meal_entries = MealEntry.query.filter_by(pid=pid, date_and_time=report_date).all()
        if not meal_entries:
            return make_response({'error': 'No meal entries found for this date'}, 404)

        report = []
        total_nutrients = {
            "sugar_in_g": 0,
            "protein_in_g": 0,
            "sodium_in_mg": 0,
            "calories": 0,
            "fat_total_g": 0,
            "fat_saturated_g": 0,
            "potassium_mg": 0,
            "cholesterol_mg": 0,
            "carbohydrates_total_g": 0
        }

        for meal in meal_entries:
            nutrients = Nutrients.query.filter_by(meid=meal.meid).all()
            nutrients_list = [{
                "nutrients_id": nutrient.nid,
                "sugar_in_g": nutrient.sugar_in_g,
                "protein_in_g": nutrient.protein_in_g,
                "sodium_in_mg": nutrient.sodium_in_mg,
                "calories": nutrient.calories,
                "fat_total_g": nutrient.fat_total_g,
                "fat_saturated_g": nutrient.fat_saturated_g,
                "potassium_mg": nutrient.potassium_mg,
                "cholesterol_mg": nutrient.cholesterol_mg,
                "carbohydrates_total_g": nutrient.carbohydrates_total_g
            } for nutrient in nutrients]

            for nutrient in nutrients:
                total_nutrients["sugar_in_g"] += nutrient.sugar_in_g
                total_nutrients["protein_in_g"] += nutrient.protein_in_g
                total_nutrients["sodium_in_mg"] += nutrient.sodium_in_mg
                total_nutrients["calories"] += nutrient.calories
                total_nutrients["fat_total_g"] += nutrient.fat_total_g
                total_nutrients["fat_saturated_g"] += nutrient.fat_saturated_g
                total_nutrients["potassium_mg"] += nutrient.potassium_mg
                total_nutrients["cholesterol_mg"] += nutrient.cholesterol_mg
                total_nutrients["carbohydrates_total_g"] += nutrient.carbohydrates_total_g

            meal_entry = {
                "portiontype": meal.portiontype,
                "servingSize": meal.servingSize,
                "date_and_time": meal.date_and_time.strftime('%Y-%m-%d %H:%M:%S'),
                "mealtype": meal.mealtype.name,
                "mealOrDrink": meal.mealOrDrink.name,
                "meal": meal.meal,
                "patient_id": meal.pid,
                "nutrients": nutrients_list
            }
            report.append(meal_entry)

        return jsonify({"report": report, "total_nutrients": total_nutrients}), 200
    except Exception as e:
        print(e)
        return make_response({'error': 'An error has occurred.'}, 500)

@app.route("/weeklyNutritionalReport/<pid>/<start_month>/<start_day>/<start_year>", methods=['GET'])
@login_required
@patient_or_caregiver_required
def weeklyNutritionalReport(pid, start_month, start_day, start_year):
    try:
        start_date_str = f"{start_month}/{start_day}/{start_year}"
        start_date = datetime.strptime(start_date_str, '%m/%d/%Y').date()
        
        # Calculate end date (7 days from start date)
        end_date = start_date + timedelta(days=6)

        patient = Patients.query.filter_by(pid=pid).first()
        if not patient:
            return make_response({'error': 'Patient not found'}, 404)

        # Query meal entries within the date range
        meal_entries = MealEntry.query.filter(
            MealEntry.pid == pid,
            MealEntry.date_and_time >= start_date,
            MealEntry.date_and_time <= end_date
        ).all()

        if not meal_entries:
            return make_response({'error': 'No meal entries found for this week'}, 404)

        report = []
        total_nutrients = {
            "sugar_in_g": 0,
            "protein_in_g": 0,
            "sodium_in_mg": 0,
            "calories": 0,
            "fat_total_g": 0,
            "fat_saturated_g": 0,
            "potassium_mg": 0,
            "cholesterol_mg": 0,
            "carbohydrates_total_g": 0
        }

        for meal in meal_entries:
            nutrients = Nutrients.query.filter_by(meid=meal.meid).all()
            nutrients_list = [{
                "nutrients_id": nutrient.nid,
                "sugar_in_g": nutrient.sugar_in_g,
                "protein_in_g": nutrient.protein_in_g,
                "sodium_in_mg": nutrient.sodium_in_mg,
                "calories": nutrient.calories,
                "fat_total_g": nutrient.fat_total_g,
                "fat_saturated_g": nutrient.fat_saturated_g,
                "potassium_mg": nutrient.potassium_mg,
                "cholesterol_mg": nutrient.cholesterol_mg,
                "carbohydrates_total_g": nutrient.carbohydrates_total_g
            } for nutrient in nutrients]

            for nutrient in nutrients:
                total_nutrients["sugar_in_g"] += nutrient.sugar_in_g
                total_nutrients["protein_in_g"] += nutrient.protein_in_g
                total_nutrients["sodium_in_mg"] += nutrient.sodium_in_mg
                total_nutrients["calories"] += nutrient.calories
                total_nutrients["fat_total_g"] += nutrient.fat_total_g
                total_nutrients["fat_saturated_g"] += nutrient.fat_saturated_g
                total_nutrients["potassium_mg"] += nutrient.potassium_mg
                total_nutrients["cholesterol_mg"] += nutrient.cholesterol_mg
                total_nutrients["carbohydrates_total_g"] += nutrient.carbohydrates_total_g

            meal_entry = {
                "portiontype": meal.portiontype,
                "servingSize": meal.servingSize,
                "date_and_time": meal.date_and_time.strftime('%Y-%m-%d %H:%M:%S'),
                "mealtype": meal.mealtype.name,
                "mealOrDrink": meal.mealOrDrink.name,
                "meal": meal.meal,
                "patient_id": meal.pid,
                "nutrients": nutrients_list
            }
            report.append(meal_entry)

        return jsonify({"report": report, "total_nutrients": total_nutrients}), 200

    except Exception as e:
        print(e)
        return make_response({'error': 'An error has occurred.'}, 500)

# @app.route('/generateReports/<pid>', methods=['GET'])
# @login_required
# @patient_or_caregiver_required
# def generateReports(pid):
#     if request.method == "GET":
#         try
#         except Exception as e: 
#             db.session.rollback()
#             print(e)
#             return make_response({'error': 'An error has occurred.'},400) 
        


# @app.route('/authorize')
# def authorize():
#     fitbit_auth_url = 'https://www.fitbit.com/oauth2/authorize'
#     response_type = 'code'
#     scope = 'activity'
#     return redirect(f'{fitbit_auth_url}?response_type={response_type}&client_id={CLIENT_ID}&redirect_uri={REDIRECT_URI}&scope={scope}')
    

@app.route('/<file_name>.txt')
def send_text_file(file_name):
    """Send your static text file."""
    file_dot_text = file_name + '.txt'
    return app.send_static_file(file_dot_text)



def isAllowedFile(filename):
#Checks if a file is a photo
# if f.endswith(".jpg") or f.endswith(".png") or f.endswith(".jpg"):
    return filename.lower().endswith('.jpg') or filename.lower().endswith('.jpeg') or filename.lower().endswith('.png') or filename.lower().endswith('.pdf') or filename.lower().endswith('.doc') or filename.lower().endswith('.docx')



@app.after_request
def add_header(response):
    """
    Add headers to both force latest IE rendering engine or Chrome Frame,
    and also tell the browser not to cache the rendered page. If we wanted
    to we could change max-age to 600 seconds which would be 10 minutes.
    """
    response.headers['X-UA-Compatible'] = 'IE=Edge,chrome=1'
    response.headers['Cache-Control'] = 'public, max-age=0'
    return response





# import React, { useEffect } from 'react';
# import socketIOClient from 'socket.io-client';

# const ENDPOINT = 'http://localhost:5000';  // Adjust the endpoint to your Flask-SocketIO server

# const App = () => {
#   useEffect(() => {
#     const socket = socketIOClient(ENDPOINT);

#     // Event handler for 'server_response' event from Flask
#     socket.on('server_response', data => {
#       console.log('Received server response:', data);
#       // Handle the received data in your React component
#     });

#     // Clean up socket connection on component unmount
#     return () => socket.disconnect();
#   }, []);

#   return (
#     <div>
#       <h1>SocketIO Example</h1>
#       {/* Your React component content */}
#     </div>
#   );
# };

# export default App;
