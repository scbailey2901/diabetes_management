import os
from app import app
from flask import render_template,make_response, redirect, request, url_for, flash, send_from_directory, Flask
import pickle
from flask import g
from flask import jsonify, send_file,  flash, session, abort
import os
import json
from datetime import datetime, timedelta, date
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy.orm import joinedload
from app.models import *
from flask_login import login_user, logout_user, current_user, login_required, LoginManager
from app import login_manager
from flask_wtf.csrf import generate_csrf
from werkzeug.utils import secure_filename
import re
from app.models import Patients, Caregivers, BloodSugarLevels, Credentials, HealthRecord, CaregiverType, Gender, CredentialType, AlertType, Alert
from flask_migrate import Migrate

    
from functools import wraps
import jwt
# from flask_mysqldb import MySQL
import psycopg2


@app.route('/api/v1/csrf-token', methods=['GET'])
def get_csrf():
    return jsonify({'csrf_token': generate_csrf()})


# ACTIVE = {}

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
    patient = db.session.execute(db.select(Patients).filter_by(pid=id)).scalar()
    if patient:
        return patient
    
    caregiver = db.session.execute(db.select(Caregivers).filter_by(cid=id)).scalar()
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
                return make_response({"success": "User logged in successfully."})
                
            caregiver = Caregivers.query.filter_by(email = email).first()
            if caregiver and check_password_hash(caregiver.password, password):
                login_user(caregiver)
                return make_response({"success": "User logged in successfully."})
            
            return make_response({'error': 'Login failed. Please check your credentials to ensure they are correct.'},400)
        except Exception as e:
            db.session.rollback()
            print(e)
            return make_response({'error': 'An error occurred during login.'},400)

@app.route('/logout', method=['GET'])
@login_required
def logout():
    logout_user()
    return make_response({'success': "User has been successfully logged out."})

@app.route('/register', methods=['POST', 'GET'])
def register():
    if request.method =="POST":
        try: 
            content = request.get_json()
            usertype = content['usertype'] # get user type
            name = content['name'] # get user full name
            username = content['username'] # get username
            dob = content['dob'] 
            dob = datetime.strptime(dob, "%m/%d/%Y %H:%M").date() # convert string dob to date
            age = int((date.today() - dob).days / 365.2425) # calculate age
            #validate password
            reg = "^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*#?&])[A-Za-z\d@$!#%*?&]{6,20}$"
            pat = re.compile(reg)                
            mat = re.search(pat, content['password'])
            if mat:
                # password = bcrypt.hashpw(content['password'].encode('utf-8'), bcrypt.gensalt(rounds=15)).decode('utf-8')
                password = content['password']
            else: 
                return make_response({'error': 'Password should have at least one uppercase letter, one symbol, one numeral and one lowercase letter.'})
            #Validate the email address
            eregex = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,7}\b'
            if(re.fullmatch(eregex, content["email"])):
                email = content['email']
            else: 
                return make_response({'error': 'Please enter a valid email address.'},400)
            
            #Validate phone number
            pregex = r"^[189][0-9]{7}$"
            validphone = re.search(pregex, content['phonenumber'])
            if validphone: 
                phonenumber = content['phonenumber']
            else: 
                return make_response({'error': 'Please enter a valid phone number'}, 400)
            
            gender = Gender.FEMALE if content['gender'].lower() == "female" else Gender.MALE #get gender. Add non-binary too just in case      
            consentForData = content['consentForData']
            if usertype == 'Patient':
                caregiver = None
                if Patients.query.filter_by(username = username).first() is not None:#check if their username has been taken already
                    return make_response({'error': 'Username already exists'}, 400)
                
                if Patients.query.filter_by(name = name).first() is not None: #check the user exists
                    return make_response({'error': 'User is already registered.'}, 400) # redirect them to login screen
                else:
                    weight = int(content['weight']) # get weight
                    height = int(content['height'])
                    isSmoker = content['isSmoker'] == "Yes"
                    isDrinker = content['isDrinker'].lower() =="Yes"
                    hasHighBP = content['hasHighBP'] =="Yes"
                    hasHighChol = content['hasHighChol'] =="Yes"
                    hasHeartDisease = content['hasHeartDisease'] == "Yes"
                    hadHeartAttack = content['hadHeartAttack'] == "Yes"
                    hasTroubleWalking = content['hasTroubleWalking'].lower() == "Yes"
                    hadStroke =content['hadStroke'] == "Yes" 
                    weightUnits = content['weightUnits']
                    heightUnits = content['heightUnits']
                    # bloodSugarlevels = []
                    # bloodPressurelevels = []
                    patient = Patients(age,dob,email,consentForData, name, username, password,phonenumber, gender, caregiver)
                    db.session.add(patient)
                    db.session.commit()
                    patient= Patients.query.filter_by(name=name).first()
                    healthrecord = HealthRecord(age, weight,weightUnits, height, heightUnits, isSmoker, isDrinker, hasHighBP, hasHighChol, hasHeartDisease, hadHeartAttack, hadStroke, hasTroubleWalking, [], [], patient.get_id())
                    db.session.add(healthrecord)
                    db.session.commit()
                    return make_response({'success': 'User created successfully'},201)
            elif usertype == "Doctor" or usertype =="Nurse":
                caregivertype = CaregiverType.DOCTOR if usertype == "Doctor" else CaregiverType.NURSE
                
                if Caregivers.query.filter_by(username = username).first():#check if their username has been taken already
                    return make_response({'error': 'Username already exists'}, 400)
                
                if Caregivers.query.filter_by(name = name).first(): #check the user exists
                    return make_response({'error': 'User is already registered.'}, 400) # redirect them to login screen
                else:
                    files = request.files.getlist("file") 
                    if usertype =="Doctor" and len(files)<2:
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
                                    credentials = Credentials(filename, caregivertype,caregiver.get_id(), caregiver.get_name())
                                db.session.add(credentials)
                                db.session.commit()
                                return make_response({'success': 'User has been successfully registered. Please give us 3 days to validate your credentials.'},201)
            elif usertype == "Family Member":
                if usertype =="Family Member":
                    caregivertype = CaregiverType.FAMILY
                    if Caregivers.query.filter_by(username = username).first():#check if their username has been taken already
                        return make_response({'error': 'Username already exists'}, 400)
                
                    if Caregivers.query.filter_by(name = name).first(): #check the user exists
                        return make_response({'error': 'User is already registered.'}, 400) # redirect them to login screen
                    else:
                        caregiver = Caregivers(name, username,caregivertype , age, dob, email, password, phonenumber, gender, consentForData)
                        db.session.add(caregiver)
                        db.session.commit()
        except Exception as e:
            db.session.rollback()
            print(e)
            return make_response({'error': 'An error has occurred'},400)

    
# def get_current_user(user_id):
#     user = Patients.query.get(user_id)
#     if not user:
#         return jsonify({'error': 'User not found'}), 404
#     return user


# @login_manager.user_loader
# def load_user(user_id):
#     return Patients.query.get(int(user_id))

def logout():
    logout_user()
    return make_response({'success': 'User was logged out successfully.'},400)

@app.route("/recordBloodSugar/<pid>", methods=['POST','GET']) # patient personally adds their recordBloodSugar Levels
@login_required
@patient_or_caregiver_required
def recordBloodSugar(pid):
    if request.method =="POST":
        try: 
            content = request.get_json()
            bloodSugarLevel = content['bloodSugarLevel']
            unit = content['unit']
            dateAndTimeRecorded = content['dateAndTimeRecorded']
            dateAndTimeRecorded = datetime.strptime(dateAndTimeRecorded, "%m/%d/%Y %H:%M").date()
            notes = content['notes']
            creator = content['creator']
            patient= Patients.query.filter_by(pid=pid).first() is not None
            isCreatorReal = (Patients.query.filter_by(name=creator).first() is not None) or (Caregivers.query.filter_by(name=creator).first() is not None) 
            if isCreatorReal:
                if patient: 
                    hrid = Patients.query.filter_by(pid=pid).first().get_hrid()
                    bloodsugarlevel = BloodSugarLevels(int(bloodSugarLevel), unit, dateAndTimeRecorded, pid, hrid, notes, creator)
                    db.session.add(bloodsugarlevel)
                    db.session.commit() #Modify this to allow it to update the Health record
                    return make_response({'success': 'Blood Sugar Level Recorded Successfully'},201)
                return make_response({'error': 'Patient does not exist'},400)
            return make_response({'error': 'The user attempting to create the blood pressure record does not exist.'},400)
        except Exception as e:
            db.session.rollback()
            print(e)
            return make_response({'error': 'An error has occurred'},400)
     
@app.route("/recordBloodPressure/<pid>", methods=['POST']) # patient personally adds their recordBloodSugar Levels
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
            creator = content['creator']
            patient= Patients.query.filter_by(pid=pid).first() is not None
            isCreatorReal = (Patients.query.filter_by(name=creator).first() is not None) or (Caregivers.query.filter_by(name=creator).first() is not None) 
            if isCreatorReal:
                if patient: 
                    hrid = Patients.query.filter_by(pid=pid).first().get_hrid()
                    bloodpressurelevel = BloodPressureLevels(int(bloodPressureLevel), unit, dateAndTimeRecorded,creator,pid, hrid, notes)
                    db.session.add(bloodpressurelevel)
                    db.session.commit() #Modify this to allow it to update the Health record
                    return make_response({'success': 'Blood Pressure Level Recorded Successfully'},201)
                return make_response({'error': 'Patient does not exist'},400)
            return make_response({'error': 'The user attempting to create the blood pressure record does not exist.'},400)
        except Exception as e: 
            db.session.rollback()
            print(e)
            return make_response({'error': 'An error has occurred'},400)
     
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
            dosage = content['dosage']
            inventory = content['inventory']
            creator = content['creator']
            patient= Patients.query.filter_by(pid=pid).first() is not None
            isCreatorReal = (Patients.query.filter_by(name=creator).first() is not None) or (Caregivers.query.filter_by(name=creator).first() is not None) 
            if isCreatorReal:
                if patient:
                    patient =Patients.query.filter_by(pid=pid).first()
                    medication = Medication(name, unit, recommendedFrequency, dosage,inventory, pid, creator, creator)
                    db.session.add(medication)
                    db.session.commit() 
                    for i in range(recommendedFrequency):
                        time = content['time']
                        time = datetime.strptime(time, '%I:%M %p')
                        alrt=Alert("Hi "+patient.username+"! It's "+ content['time']+ ". Time to take your "+ medication.name + " medication.", AlertType.MEDICATION, time, pid, medication.mid)
                        db.session.add(alrt)
                        db.session.commit()
                return make_response({'error': 'Patient does not exist'},400)
            return make_response({'error': 'The user attempting to create the medication reminder does not exist.'},400)
        except Exception as e: 
            db.session.rollback()
            print(e)
            return make_response({'error': 'An error has occurred'},400)
     
@app.route("/editMedicationReminder/<mid>", methods=['PUT', 'GET'])
@login_required
@patient_or_caregiver_required
def editMedicationReminder(mid):
    if request.method =="PUT":
        try:
            content = request.get_json()
            medication = Medication.query.filter_by(mid=mid).first()
            alerts= Alert.query.filter_by(mid=mid)
            medication.name = content['name'] if content['name'] != None else medication.name
            medication.unit = content['unit'] if content['unit'] != None else medication.unit
            medication.recommendedFrequency = content['recommendedFrequency'] if  content['recommendedFrequency'] != None else medication.recommendedFrequency
            medication.dosage = content['dosage'] if content['dosage']  != None else medication.dosage
            medication.inventory = content['inventory'] if content['inventory'] != None else medication.inventory
             
        except Exception as e: 
            db.session.rollback()
            print(e)
            return make_response({'error': 'An error has occurred'},400)
#)
# convert food
# api_url = 'https://api.calorieninjas.com/v1/nutrition?query='
# query = '3lb carrots and a chicken sandwich'
# response = requests.get(api_url + query, headers={'X-Api-Key': 'UdjAYE21RFKdvFnrUhM25g==xL6FYYElHVpuQrAJ'})
# if response.status_code == requests.codes.ok:
#     print(response.text)
# else:
#     print("Error:", response.status_code, response.text)
# username = data.username.data
#             password = data.password.data
#             timestamp= datetime.utcnow()
#             expiry_date= timestamp+timedelta(days=7)
#             user = Users.query.filter_by(username=username).first()
#             print(user)
#             if user is not None and check_password_hash(user.password, password):
#                 payload = {'sub': user.id, "iat":timestamp, "exp": expiry_date}
                
#                 token = jwt.encode(payload, app.config['SECRET_KEY'], algorithm = 'HS256')
#                 if login_user(user):
#                     load_user(user.id)
#                 return jsonify(status='success', message = 'User successfully logged in.', id=user.id, token=token)
#             return jsonify(errors="Invalid username or password")
#         except Exception as e:
#             print(e)
#             return jsonify(errors='An error occurred while processing your request'), 500
#     return jsonify(errors='Invalid request method'), 405



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