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


@app.route('register', methods=['POST', 'GET'])
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
            
            eregex = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,7}\b'
            if(re.fullmatch(eregex, content["email"])):
                email = content['email']
            else: 
                return make_response({'error': 'Please enter a valid email address.'},400)
            
            pregex = r"^[189][0-9]{7}$"
            validphone = re.search(pregex, content['phonenumber'])
            if validphone: 
                phonenumber = content['phonenumber']
            else: 
                return make_response({'error': 'Please enter a valid phone number'}, 400)
            
            gender = content['gender']
            caregiver = None
            consentForData = content['consentForData']
            if usertype == 'Patient':
                if Patients.query.filter_by(username = username).first():
                    return make_response({'error': 'Username already exists'}, 400)
                
                if Patients.query.filter_by(name = name).first():
                    return make_response({'error': 'User is already registered.'}, 400) # redirect them to login screen
                else:
                    weight = int(content['weight'])
                    height = int(content['height'])
                    isSmoker = content['isSmoker']
                    isDrinker = content['isDrinker']
                    hasHighBP = content['hasHighBP']
                    hasHighChol = content['hasHighChol']
                    hasHeartDisease = content['hasHeartDisease']
                    hadHeartAttack = content['hadHeartAttack']
                    hasTroubleWalking = content['hasTroubleWalking']
                    hadStroke = content['hadStroke']
                    bloodSugarlevels = []
                    bloodPressurelevels = []
                    patient = Patients(age,dob,email,consentForData, name, username, password,phonenumber, gender, caregiver)
                    db.session.add(patient)
                    db.session.commit()
                    patient= Patients.query.filter_by(name=name).first()
                    healthrecord = HealthRecord(weight, height, isSmoker, isDrinker, hasHighBP, hasHighChol, hasHeartDisease, hadHeartAttack, hadStroke, hasTroubleWalking, [], [], patient.get_id())
                    db.session.add(healthrecord)
                    db.session.commit()
                    return make_response({'error': 'User created successfully'},201)
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

@app.route("/recordBloodSugar", methods=['POST'])
def registeruser():
    return "test"

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