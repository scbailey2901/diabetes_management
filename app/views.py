import os
from app import app, socketio

from flask import render_template,make_response, redirect, request, url_for, flash, send_from_directory, Flask
# from apscheduler.schedulers.background import BackgroundScheduler 
from flask_apscheduler import APScheduler 
from apscheduler.schedulers.background import BackgroundScheduler
from flask import current_app
from flask_socketio import SocketIO
from flask_socketio import emit
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
from app.models import Patients, Caregivers, BloodSugarLevels, Credentials, HealthRecord, CaregiverType, Gender, CredentialType, AlertType, Alert, Medication, MedicationAudit, MealDiary, MealEntry, MealType, Nutrients, FoodOrDrink, DiabetesType, RecTime, MedicationTime
from flask_migrate import Migrate

    
from functools import wraps
# import jwt
# from flask_mysqldb import MySQL
import psycopg2


load_dotenv()



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
            patient = Patients.query.filter_by(email = email).first()
            if patient and check_password_hash(patient.password, password):
                login_user(patient)
                return make_response({"success": "User logged in successfully."},200)
                
            caregiver = Caregivers.query.filter_by(email = email).first()
            if caregiver and check_password_hash(caregiver.password, password):
                login_user(caregiver)
                return make_response({"success": "User logged in successfully."},200)
            
            return make_response({'error': 'Login failed. Please check your credentials to ensure they are correct.'},400)
        except Exception as e:
            db.session.rollback()
            print(e)
            return make_response({'error': 'An error occurred during login.'},400)

@app.route('/logout', methods = ['POST','GET'])
@login_required
def logout():
    logout_user()
    return make_response({'success': "User has been successfully logged out."},200)

@app.route('/register', methods=['POST', 'GET'])
def register():
    if request.method =="POST":
        try: 
            content = request.get_json()
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
                # password = bcrypt.hashpw(content['password'].encode('utf-8'), bcrypt.gensalt(rounds=15)).decode('utf-8')
                password = content['password']
            else: 
                db.session.rollback()
                return make_response({'error': 'Password should have at least one uppercase letter, one symbol, one numeral and one lowercase letter.'},400)
            #Validate the email address
            eregex = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,7}\b'
            if(re.fullmatch(eregex, content["email"])):
                email = content['email']
            else: 
                db.session.rollback()
                return make_response({'error': 'Please enter a valid email address.'},400)
            
            #Validate phone number
            pregex = r"^\+1\([0-9]{3}\)[0-9]{3}-[0-9]{4}$"
            validphone = re.search(pregex, content['phonenumber'])
            if validphone: 
                phonenumber = content['phonenumber']
            else: 
                db.session.rollback()
                return make_response({'error': 'Please enter a valid phone number'}, 400)
            
            gender = Gender.FEMALE if content['gender'].lower() == "female" else Gender.MALE #get gender. Add non-binary too just in case      
            consentForData = content['consentForData'].lower()
            if usertype == 'Patient':
                caregiver = None
                if Patients.query.filter_by(username = username).first() is not None:#check if their username has been taken already
                    db.session.rollback()
                    return make_response({'error': 'Username already exists'}, 400)
                
                if Patients.query.filter_by(name = name).first() is not None: #check the user exists
                    db.session.rollback()
                    return make_response({'error': 'User is already registered.'}, 400) # redirect them to login screen
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
                    patient = Patients(age,dob,email,consentForData, name, username, password,phonenumber, gender)
                    db.session.add(patient)
                    db.session.commit()
                    patient= Patients.query.filter_by(name=name).first()
                    healthrecord = HealthRecord(age, weight,weightUnits, height, heightUnits, diabetesType,isSmoker, isDrinker, hasHighBP, hasHighChol, hasHeartDisease, hadHeartAttack, hadStroke, hasTroubleWalking, [], [], patient.get_id())
                    db.session.add(healthrecord)
                    db.session.commit()
                    return make_response({'success': 'User created successfully'},201)
            elif usertype == "Doctor" or usertype =="Nurse":
                caregivertype = CaregiverType.DOCTOR if usertype == "Doctor" else CaregiverType.NURSE
                
                if Caregivers.query.filter_by(username = username).first():#check if their username has been taken already
                    db.session.rollback()
                    return make_response({'error': 'Username already exists'}, 400)
                
                if Caregivers.query.filter_by(name = name).first(): #check the user exists
                    db.session.rollback()
                    return make_response({'error': 'User is already registered.'}, 400) # redirect them to login screen
                else:
                    files = request.files.getlist("file") 
                    if usertype =="Doctor" and len(files)<2:
                        db.session.rollback()
                        return make_response({'error': 'Please upload a copy of both your MBBS degree certificate and your Medical License'}, 400)
                    else: 
                        caregiver= Caregivers.query.filter_by(name=name).first() is None
                        
                        caregiver = Caregivers(name, username,caregivertype , age, dob, email, password, phonenumber, gender, consentForData)
                        db.session.add(caregiver)
                        db.session.commit()
                        for file in files:
                            if file != None and file.filename!= None: 
                                if (isAllowedFile(file.filename)):
                                    filename = secure_filename(file.filename)
                                    credentialtype = CredentialType.MBBS_DEGREE if content['credentialtype'] == "Medical Degree Certificate" else CredentialType.MEDICAL_LICENSE if content['credentialtype']=="Medical License" else CredentialType.NURSING_DEGREE
                                    file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename)) #need to check if this will work when actual file is uploaded
                                    credentials = Credentials(filename, caregivertype,caregiver.get_id())
                                db.session.add(credentials)
                                db.session.commit()
                                return make_response({'success': 'User has been successfully registered. Please give us 3 days to validate your credentials.'},201)
            elif usertype == "Family Member":
                if usertype =="Family Member":
                    caregivertype = CaregiverType.FAMILY
                    if Caregivers.query.filter_by(username = username).first():#check if their username has been taken already
                        db.session.rollback()
                        return make_response({'error': 'Username already exists'}, 400)
                
                    if Caregivers.query.filter_by(name = name).first(): #check the user exists
                        db.session.rollback()
                        return make_response({'error': 'User is already registered.'}, 400) # redirect them to login screen
                    else:
                        caregiver = Caregivers(name, username,caregivertype , age, dob, email, password, phonenumber, gender, consentForData)
                        db.session.add(caregiver)
                        db.session.commit()
        except Exception as e:
            db.session.rollback()
            print(e)
            return make_response({'error': 'An error has occurred'},400)

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
                    bloodsugarlevel = BloodSugarLevels(int(bloodSugarLevel), unit, dateAndTimeRecorded, pid, hrid, notes, creator)
                    db.session.add(bloodsugarlevel)
                    db.session.commit() #Modify this to allow it to update the Health record
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

@socketio.on('connect')
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

@app.route("/createMedicationReminder/<pid>", methods=['POST'])
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
                        for i in range(1, recommendedFrequency+1):
                            timekey = 'time' + str(i)
                            time = datetime.strptime(content[(timekey)], '%I:%M %p').time() if content[(timekey)] != None else "Time value missing"
                            if time != "Time value missing":
                                medTime = MedicationTime(time,medication.mid)
                                db.session.add(medTime)
                                db.session.commit()
                                medication=Medication.query.filter_by(name=name).first()
                                alrt=Alert("Hi "+patient.username+"! It's "+ content[(timekey)]+ ". Time to take your "+ medication.name + " medication.", AlertType.MEDICATION, time, pid, medication.mid)
                                db.session.add(alrt)
                                db.session.commit()
                                # job_id = f"medScheduler_{alrt.aid}"
                                # scheduler.add_job(scheduleAlert, trigger = "interval", seconds=30, id = job_id + str(i), args=[alrt] )
                            else:
                                db.session.rollback()
                                return make_response({'error': 'Time value missing'},400)
                        
                        alerts= db.session.query(Alert).filter_by(mid=medication.mid).all()
                        for alert in alerts:
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
     
@app.route("/editMedicationReminder/<mid>", methods=['PUT', 'GET', 'DELETE'])
@login_required
@patient_or_caregiver_required
def editMedicationReminder(mid):
    if request.method =="PUT":
        try:
            content = request.get_json()
            medication = Medication.query.filter_by(mid=mid).first()
            if medication != None:
                alerts= Alert.query.filter_by(mid=mid)
                patient = Patients.query.filter_by(pid=medication.pid).first()
                medication.name = content['name'] if content['name'] != None else medication.name
                medication.unit = content['unit'] if content['unit'] != None else medication.unit
                medication.recommendedFrequency = content['recommendedFrequency'] if content['recommendedFrequency'] != None else medication.recommendedFrequency
                medication.amount = int(content['amount']) if content['amount']  != None else medication.amount
                medication.inventory = int(content['inventory']) if content['inventory'] != None else medication.inventory
                for alert in alerts:
                    db.session.delete(alert)
                    
                for i in range(medication.recommendedFrequency):
                    timekey = 'time' + str(i)
                    time = datetime.strptime(content[(timekey)], '%I:%M %p') if content[(timekey)] != None else medication.time
                    medTime = MedicationTime(time,medication.mid)
                    db.session.add(medTime)
                    db.session.commit()
                    alrt=Alert("Hi "+patient.username+"! It's "+ content['time']+ ". Time to take your "+ medication.name + " medication.", AlertType.MEDICATION, time, medication.pid, medication.mid)
                    db.session.add(alrt)
                    db.session.commit()
                medAudit = MedicationAudit(mid, current_user.name)
                db.session.add(medAudit)
                db.commit()
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
                        times  = [datetime.strftime(time, '%I:%M %p') for time in med.reminderTimes]
                        meds = {"id":med.mid, "medicationName": med.name, "units": med.unit, "recommendedFrequency": med.recommendedFrequency,"receommendedTime": med.recommendedTime ,"times":times , "dosage": med.dosage, "amountInInventory": med.inventory, "patientID":med.pid, "patientName": patient.name, "creator": med.creator, "created_at": med.created_at, "last_updated_by": med.updated_by }
                        medicationlist.append(meds)
                    return jsonify(status = "success", medicationlist = medicationlist), 200
                return make_response({'error': 'Medication reminder does not exist.'}, 400)
            return make_response({'error': 'Patient does not exist.'},400)
    except Exception as e: 
            db.session.rollback()
            print(e)
            return make_response({'error': 'An error has occurred.'},400)    


        
@app.route("/deleteMedicationReminders/<mid>", methods=['GET','DELETE'])
@login_required
@patient_or_caregiver_required
def deleteMedicationReminder(mid):
    try:
        if request.method == "DELETE":
            medication = Medication.query.filter_by(mid=mid).first()
            if medication != None:
                alerts= Alert.query.filter_by(mid=mid)
                times = MedicationTime.query.filter_by(mid=mid)
                db.session.delete(medication)
                for alert in alerts:
                    db.session.delete(alert)
                db.commit() 
                
                for time in times:
                    db.session.delete(time)
                db.commit()
                if Medication.query.filter_by(mid=mid).first() == None and Alert.query.filter_by(mid=mid) == 'None':
                    return make_response({'success': 'The medication reminder has been deleted successfully.'},400)
                else:
                    return make_response({'error': 'An error occurred  during the attempt to delete this medication reminder.'},400)

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
                query = servingSize+ " "+ portiontype + " " + meal 
                response = requests.get(api_url + query, headers={'X-Api-Key': 'UdjAYE21RFKdvFnrUhM25g==xL6FYYElHVpuQrAJ'})
                if response.status_code == requests.codes.ok:
                    print(response.text)
                    nutrients_data = response.json().get('items', [])[0]
                    sugar_in_g = nutrients_data['sugar_g']
                    protein_in_g = nutrients_data['protein_in_g']
                    sodium_in_mg = nutrients_data['sodium_in_mg']
                    calories = nutrients_data['calories']
                    fat_total_g = nutrients_data['fat_total_g']
                    fat_saturated_g = nutrients_data['fat_saturated_g']
                    potassium_mg = nutrients_data['potassium_mg']
                    cholesterol_mg = nutrients_data['cholesterol_mg']
                    carbohydrates_total_g = nutrients_data['carbohydrates_total_g']
                    nutrients = Nutrients(sugar_in_g, protein_in_g,sodium_in_mg, calories,fat_total_g,fat_saturated_g, potassium_mg, cholesterol_mg, carbohydrates_total_g )
                    db.session.add(nutrients)
                    db.session.commit()
                    mealentry= MealEntry(portiontype,servingSize,date_and_time,mealtype,mealOrDrink,meal,pid,nutrients.nid)
                    db.session.add(mealentry)
                    db.session.commit()
                    mealDiary = MealDiary(pid)
                    db.session.add(mealDiary)
                    db.session.commit()
                else: 
                    return make_response({'error': response.text},response.status_code)
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
   

# @app.route("/editMealEntry/<pid>", methods = ['PUT'])
# @login_required
# @patient_or_caregiver_required
# def createMealEntry(pid):    
#     if request.method =="PUT":
#         try:
            
#         except Exception as e: 
#             db.session.rollback()
#             print(e)
#             return make_response({'error': 'An error has occurred.'},400)     
 

@app.route("/getAllMealEntries/<pid>", methods = ['GET'])
@login_required
@patient_or_caregiver_required
def getMealEntries(pid):    
    if request.method =="GET":
        try:
            if request.method =="GET":
                patient= Patients.query.filter_by(pid=pid).first()
                mealDiary = MealDiary.query.filter_by(pid=pid).first()
                if patient != None and mealDiary != None:
                    allmealentries = MealEntry.query.filter_by(mealdiaryid=mealDiary.mdid).all()
                    if allmealentries != None:
                        meallist=[]
                        for meal in allmealentries:
                            nutrients = Nutrients.query.filter_by(nid=meal.nutrients_id)
                            mealent = {"portiontype": meal.portiontype, "servingSize": meal.servingSize, "date_and_time":meal.date_and_time, "mealtype": meal.mealtype, "mealOrDrink": meal.mealOrDrink, "meal": meal.meal, "patient_id": meal.pid,"nutrients_id":meal.nutrients_id,"sugar_in_g":nutrients.sugar_in_g,"protein_in_g": nutrients.protein_in_g, "sodium_in_mg": nutrients.sodium_in_mg, "calories":nutrients.calories, "fat_total_g": nutrients.fat_total_g, "fat_saturated_g": nutrients.fat_saturated_g, "potassium_mg": nutrients.potassium_mg, "cholesterol_mg": nutrients.cholesterol_mg,"carbohydrates_total_g": nutrients.carbohydrates_total_g}
                            meallist.append(mealent)
                elif patient == None:
                    return make_response({'error': 'Patient does not exist'},400)
                elif mealDiary == None:
                    return make_response({'error': 'Meal Diary does exist for this user'},400)
        except Exception as e: 
            db.session.rollback()
            print(e)
            return make_response({'error': 'An error has occurred.'},400)    




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
