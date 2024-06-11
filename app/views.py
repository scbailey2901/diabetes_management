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
from app.models import Patients, Caregivers, BloodSugarLevels, Credentials, HealthRecord
from flask_migrate import Migrate
import bcrypt
    
from functools import wraps
import jwt
# from flask_mysqldb import MySQL
import psycopg2


@app.route('/api/v1/csrf-token', methods=['GET'])
def get_csrf():
    return jsonify({'csrf_token': generate_csrf()})


ACTIVE = {}

def requires_auth(f):
  @wraps(f)
  def decorated(*args, **kwargs):
    auth = request.headers.get('Authorization', None) # or request.cookies.get('token', None)

    if not auth:
      return jsonify({'code': 'authorization_header_missing', 'description': 'Authorization header is expected'}), 401

    parts = auth.split()

    if parts[0].lower() != 'bearer':
      return jsonify({'code': 'invalid_header', 'description': 'Authorization header must start with Bearer'}), 401
    elif len(parts) == 1:
      return jsonify({'code': 'invalid_header', 'description': 'Token not found'}), 401
    elif len(parts) > 2:
      return jsonify({'code': 'invalid_header', 'description': 'Authorization header must be Bearer + \s + token'}), 401

    token = parts[1]
    try:
        payload = jwt.decode(token, app.config['SECRET_KEY'], algorithms=["HS256"])

    except jwt.ExpiredSignatureError:
        return jsonify({'code': 'token_expired', 'description': 'token is expired'}), 401
    except jwt.DecodeError:
        return jsonify({'code': 'token_invalid_signature', 'description': 'Token signature is invalid'}), 401

    g.current_user = user = payload
    return f(*args, **kwargs)

  return decorated

@login_manager.user_loader
def load_patient(id):
    user = db.session.execute(db.select(Patients).filter_by(pid=id)).scalar()
    if user is not None:
        ACTIVE[id] = user
    return user

@login_manager.user_loader
def load_caregiver(id):
    user = db.session.execute(db.select(Caregivers).filter_by(cid=id)).scalar()
    if user is not None:
        ACTIVE[id] = user
    return user
###
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


@app.route('/register', methods=['POST', 'GET'])
def register():
    if request.method =="POST":
        try: 
            content = request.json
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
            
            gender = content['gender'] #get gender
            caregiver = None
            consentForData = content['consentForData']
            if usertype == 'Patient':
                if Patients.query.filter_by(username = username).first():#check if their username has been taken already
                    return make_response({'error': 'Username already exists'}, 400)
                
                if Patients.query.filter_by(name = name).first(): #check the user exists
                    return make_response({'error': 'User is already registered.'}, 400) # redirect them to login screen
                else:
                    weight = int(content['weight']) # get weight
                    height = int(content['height'])
                    if content['isSmoker'] == "Yes":
                        isSmoker = True
                    
                    if content['isDrinker'].lower() =="Yes":
                        isDrinker = True
                        
                    if content['hasHighBP'] =="Yes":
                        hasHighBP = True
                        
                    if content['hasHighChol'] =="Yes":
                        hasHighChol = True
                    
                    if content['hasHeartDisease'] == "Yes":
                        hasHeartDisease = True
                        
                    if content['hadHeartAttack'] == "Yes":
                        hadHeartAttack = True
                        
                    if content['hasTroubleWalking'].lower() == "Yes": 
                        hasTroubleWalking = True
                        
                    if content['hadStroke'] == "Yes":
                        hadStroke =True
                        
                    weightUnits = content['weightUnits']
                    heightUnits = content['heightUnits']
                    # bloodSugarlevels = []
                    # bloodPressurelevels = []
                    patient = Patients(age,dob,email,consentForData, name, username, password,phonenumber, gender, caregiver)
                    db.session.add(patient)
                    db.session.commit()
                    patient= Patients.query.filter_by(name=name).first()
                    healthrecord = HealthRecord(weight,weightUnits, height, heightUnits, isSmoker, isDrinker, hasHighBP, hasHighChol, hasHeartDisease, hadHeartAttack, hadStroke, hasTroubleWalking, [], [], patient.get_id())
                    db.session.add(healthrecord)
                    db.session.commit()
                    return make_response({'success': 'User created successfully'},201)
            elif usertype == "Doctor" or usertype =="Nurse":
                if Caregivers.query.filter_by(username = username).first():#check if their username has been taken already
                    return make_response({'error': 'Username already exists'}, 400)
                
                if Caregivers.query.filter_by(name = name).first(): #check the user exists
                    return make_response({'error': 'User is already registered.'}, 400) # redirect them to login screen
                else:
                    if (isAllowedFile(content['filename'])):
                        filename = secure_filename(content['filename'])
                        filename.save(os.path.join(app.config['UPLOAD_FOLDER'], filename)) #need to check if this will work when actual file is uploaded
                        caregiver = Caregivers(name, username, age, dob, email, password, phonenumber, gender, consentForData)
                        db.session.add(caregiver)
                        db.session.commit()
                        caregiver= Caregivers.query.filter_by(name=name).first()
                        credentials = Credentials(filename, caregiver.get_id(), caregiver.get_name())
                        db.session.add(credentials)
                        db.session.commit()
                        return make_response({'success': 'User has been successfully registered. Please give us 3 days to validate your credentials.'},201)
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

@app.route("/recordBloodSugar/<pid>", methods=['POST']) # patient personally adds their recordBloodSugar Levels
def recordBloodSugar(pid):
    if request.method =="POST":
        try: 
            content = request.json
            bloodSugarLevel = content['bloodSugarLevel']
            unit = content['unit']
            dateAndTimeRecorded = content['dateAndTimeRecorded']
            dateAndTimeRecorded = datetime.strptime(dateAndTimeRecorded, "%m/%d/%Y %H:%M").date()
            notes = content['notes']
            patient= Patients.query.filter_by(pid=pid).first() is not None
            if patient: 
                hrid = Patients.query.filter_by(pid=pid).first().get_hrid()
                bloodsugarlevel = BloodSugarLevels(int(bloodSugarLevel), unit, dateAndTimeRecorded, hrid, notes)
                db.session.add(bloodsugarlevel)
                db.session.commit() #Modify this to allow it to update the Health record
                return make_response({'success': 'Blood Sugar Level Recorded Successfully'},201)
        except Exception as e:
            db.session.rollback()
            print(e)
            return make_response({'error': 'An error has occurred'},400)
     
@app.route("/recordBloodPressure/<pid>", methods=['POST']) # patient personally adds their recordBloodSugar Levels
def recordBloodPressure(pid):
    if request.method =="POST":
        try: 
            content = request.json
            bloodPressureLevel = content['bloodPressureLevel']
            unit = content['unit']
            dateAndTimeRecorded = content['dateAndTimeRecorded']
            dateAndTimeRecorded = datetime.strptime(dateAndTimeRecorded, "%m/%d/%Y %H:%M").date()
            notes = content['notes']
            patient= Patients.query.filter_by(pid=pid).first() is not None
            if patient: 
                hrid = Patients.query.filter_by(pid=pid).first().get_hrid()
                bloodpressurelevel = BloodPressureLevels(int(bloodPressureLevel), unit, dateAndTimeRecorded, hrid, notes)
                db.session.add(bloodpressurelevel)
                db.session.commit() #Modify this to allow it to update the Health record
                return make_response({'success': 'Blood Pressure Level Recorded Successfully'},201)
        except Exception as e:
            db.session.rollback()
            print(e)
            return make_response({'error': 'An error has occurred'},400)
     


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