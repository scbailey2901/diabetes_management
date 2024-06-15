from . import db
from datetime import datetime
from werkzeug.security import generate_password_hash
from enum import Enum

patient_caregiver = db.Table(
    'patient_caregiver',
    db.Column('patient_id', db.Integer, db.ForeignKey('patients.pid')),
    db.Column('caregiver_id', db.Integer, db.ForeignKey('caregivers.cid'), nullable=True)
)

class CaregiverType(Enum):
    NURSE = "nurse"
    DOCTOR = "doctor"
    FAMILY = "family"
    
class Gender(Enum):
    MALE = "male"
    FEMALE = "female"

class CredentialType(Enum):
    MBBS_DEGREE="MBBS Degree Certificate"
    NURSING_DEGREE="Nursing Degree Certificate"
    MEDICAL_LICENSE="Medical License"

class AlertType(Enum):
    MEDICATION = "medication"
    BP_TOO_LOW = "bp is too low"
    BP_TOO_HIGH = "bp is too low"
    AT_RISK_OF_EMERGENCY = "at risk of diabetic emergency"
    EAT_MEAL = "Remember to eat"
    TOO_MUCH_SALT = "You are consuming too much sodium"
    TOO_MUCH_SUGAR = "You are consuming too much sugar/carbs"
    

class Patients(db.Model):
    __tablename__ = 'patients'
    pid = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(200), unique=False, nullable=False)
    age = db.Column(db.Integer)
    dob = db.Column(db.DateTime)
    email = db.Column(db.String(256))
    username = db.Column(db.String(200), unique=True)
    password = db.Column(db.String(256), nullable=False)
    phonenumber = db.Column(db.String(15))
    gender = db.Column(db.Enum(Gender), nullable=False)
    consentForData = db.Column(db.String(20))
    joined_on = db.Column(db.DateTime, default=datetime.now())
    caregivers = db.relationship('Caregivers', secondary=patient_caregiver, back_populates='patients')
    hrid = db.Column(db.Integer, db.ForeignKey('healthrecord.hrid'))

    def __init__(self, age, dob, email,consentForData, name, username, password, phonenumber, gender):
        self.name = name
        self.username = username
        self.age = age
        self.dob = dob
        self.email = email
        self.password = generate_password_hash(password, method="pbkdf2:sha256")
        self.phonenumber = phonenumber
        self.consentForData = consentForData
        self.gender = gender
        # self.hrid = hrid
        

    def is_authenticated(self):
        return True

    def is_active(self):
        return True

    def is_anonymous(self):
        return False

    def get_id(self):
        return str(self.pid)

    def get_hrid(self):
        return str(self.hrid)
    
    def __repr__(self):
        return f"Patient(name='{self.name}', username='{self.username}', password='{self.password}', phonenumber='{self.phonenumber}', gender='{self.gender}', joined_on='{self.joined_on}')"

    def to_json(self):
        return {
            "pid": self.pid,
            "name": self.name,
            "username": self.username,
            "password": self.password,
            "phoneNumber": self.phonenumber,
            "gender": self.gender,
            "joinedOn": self.joined_on,
            "hrid": self.hrid
        }

class HealthRecord(db.Model): #add activity level
    __tablename__ = 'healthrecord'
    hrid= db.Column(db.Integer, primary_key=True, autoincrement=True)
    weight = db.Column(db.Integer)
    weightUnits = db.Column(db.String(50))
    height = db.Column(db.Integer)
    heightUnits = db.Column(db.String(50))
    isSmoker = db.Column(db.Boolean, default = False)
    isDrinker = db.Column(db.Boolean, default = False)
    hasHighBP = db.Column(db.Boolean, default = False)
    hasHighChol = db.Column(db.Boolean, default = False)
    hasHeartDisease = db.Column(db.Boolean, default = False)
    hadHeartAttack = db.Column(db.Boolean, default = False)
    hadStroke = db.Column(db.Boolean, default = False)
    hasTroubleWalking = db.Column(db.Boolean, default = False)
    bloodSugarlevels = db.relationship('BloodSugarLevels', backref='healthrecord')
    bloodPressurelevels = db.relationship('BloodPressureLevels', backref='healthrecord')
    patient_id = db.Column(db.Integer, db.ForeignKey('patient.pid'))
    
    def __init__(self, age, weight,weightUnits, height, heightUnits,isSmoker, isDrinker, hasHighBP, hasHighChol, hasHeartDisease, hadHeartAttack, hadStroke,hasTroubleWalking,bloodSugarlevels,bloodPressurelevels,patient_id ):
        self.age = age
        self.weight = weight
        self.weightUnits = weightUnits
        self.heightUnits = heightUnits
        self.height = height
        self.isSmoker = isSmoker
        self.isDrinker = isDrinker
        self.hasHighBP = hasHighBP
        self.hasHighChol = hasHighChol
        self.hasHeartDisease = hasHeartDisease
        self.hadHeartAttack = hadHeartAttack
        self.hadStroke = hadStroke
        self.hasTroubleWalking = hasTroubleWalking
        self.bloodSugarlevels = bloodSugarlevels
        self.bloodPressurelevels = bloodPressurelevels
        self.patient_id = patient_id
    
class Caregivers(db.Model):
    __tablename__ = 'caregivers'
    cid = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(256))
    username = db.Column(db.String(200), unique = True)
    type = db.Column(db.Enum(CaregiverType))
    age = db.Column(db.Integer)
    dob = db.Column(db.DateTime)
    email = db.Column(db.String(256))
    password = db.Column(db.String(200))
    phonenumber = db.Column(db.String(15))
    gender = db.Column(db.Enum(Gender))
    consentForData = db.Column(db.String(20))
    joined_on = db.Column(db.DateTime, default=datetime.now())
    patients = db.relationship('Patients', secondary=patient_caregiver, back_populates='caregivers')
    credentials = db.relationship('Credentials', backref='caregivers')

    def __init__(self, name, username,type,age, dob,email, password, phonenumber, gender, consentForData):
        self.name = name
        self.username = username
        self.type = type
        self.age = age
        self.dob = dob
        self.email = email
        self.password = generate_password_hash(password, method="pbkdf2:sha256")
        self.phonenumber = phonenumber
        self.gender = gender
        self.consentForData = consentForData

    def is_authenticated(self):
        return True

    def is_active(self):
        return True

    def is_anonymous(self):
        return False

    def get_id(self):
        return str(self.cid)

    def __repr__(self):
        return f"Caregiver(cid={self.cid}, name='{self.name}', username='{self.username}', password='{self.password}', phonenumber='{self.phonenumber}', gender='{self.gender}', joined_on='{self.joined_on}')"

    def to_json(self):
        return {
            "cid": self.cid,
            "name": self.name,
            "username": self.username,
            "password": self.password,
            "phoneNumber": self.phonenumber,
            "gender": self.gender,
            "joinedOn": self.joined_on
        }

class Credentials(db.Model):
    __tablename__ = 'credentials'
    crid = db.Column(db.Integer, primary_key=True, autoincrement=True)
    filename = db.Column(db.String(200))
    credentialtype = db.Column(db.Enum(CredentialType))
    caregiver_id = db.Column(db.Integer, db.ForeignKey('caregivers.cid'))
    caregiver_name = db.Column(db.String(256), db.ForeignKey('caregivers.name'))

    def file_path(self):
        if self.filename:
            return f'uploads/{self.filename}'
        else:
            return None

    def __init__(self, filename, credentialtype, caregiver_id, caregiver_name):
        self.filename = filename
        self.credentialtype = credentialtype
        self.caregiver_id = caregiver_id
        self.caregiver_name = caregiver_name

    def __repr__(self):
        return f"Credentials(crid={self.crid}, filename='{self.filename}', caregiver_id={self.caregiver_id}, caregiver_name='{self.caregiver_name}')"

    def to_json(self):
        return {
            "crid": self.crid,
            "filename": self.filename,
            "caregiverId": self.caregiver_id,
            "caregiverName": self.caregiver_name
        }
    
    def get_id(self):
        return str(self.crid)
    
    def get_name(self):
        return str(self.name)

class BloodSugarLevels(db.Model):
    __tablename__ = 'bloodsugarlevels'
    bslID = db.Column(db.Integer, primary_key=True, autoincrement=True)
    bloodSugarLevel = db.Column(db.Integer)
    unit = db.Column(db.String)
    dateAndTimeRecorded = db.Column(db.DateTime)
    creator = db.Column(db.String(256))
    created_at = db.Column(db.DateTime, default=datetime.now)
    patient_id = db.Column(db.Integer, db.ForeignKey('patients.pid'))
    hrid = db.Column(db.Integer, db.ForeignKey('healthrecord.hrid'))
    notes = db.Column(db.String(256))

    def __init__(self, bloodSugarLevel, unit, dateAndTimeRecorded,  patient_id, hrid, notes, creator):
        self.bloodSugarLevel = bloodSugarLevel
        self.unit = unit
        self.dateAndTimeRecorded = dateAndTimeRecorded
        self.patient_id = patient_id
        self.hrid = hrid
        self.notes = notes
        self.creator = creator
        
    def get_id(self):
        return str(self.bslid)
    
    def __repr__(self):
        return f"BloodSugarLevel(bloodSugarLevel='{self.bloodSugarLevel} {self.unit}', dateAndTimeRecorded='{self.dateAndTimeRecorded}', created_at='{self.created_at}')"

    def to_json(self):
        return {
            "bslId": self.bslID,
            "bloodSugarLevel": self.bloodSugarLevel,
            "unit": self.unit,
            "dateAndTimeRecorded": self.dateAndTimeRecorded,
            "createdAt": self.created_at,
            "patientId": self.patient_id,
            "healthrecordid": self.hrid
        }

class BloodPressureLevels(db.Model):
    __tablename__ = 'bloodpressurelevels'
    bplID = db.Column(db.Integer, primary_key=True, autoincrement=True)
    bloodPressureLevel = db.Column(db.Integer)
    unit = db.Column(db.String)
    dateAndTimeRecorded = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.now)
    patient_id = db.Column(db.Integer, db.ForeignKey('patients.pid'))
    creator = db.Column(db.String(256))
    hrid = db.Column(db.Integer, db.ForeignKey('healthrecord.hrid'))
    notes = db.Column(db.String(256))

    def __init__(self, bloodPressureLevel, unit, dateAndTimeRecorded, creator, patient_id, hrid, notes):
        self.bloodSugarLevel = bloodPressureLevel
        self.unit = unit
        self.dateAndTimeRecorded = dateAndTimeRecorded
        self.creator = creator
        self.patient_id = patient_id
        self.hrid = hrid
        self.notes= notes
        
    def get_id(self):
        return str(self.bplID)

    def __repr__(self):
        return f"BloodPressureLevel(id={self.bplID}, bloodPressureLevel='{self.bloodPressureLevel} {self.unit}', dateAndTimeRecorded='{self.dateAndTimeRecorded}', created_at='{self.created_at}')"

    def to_json(self):
        return {
            "bplId": self.bplID,
            "bloodPressureLevel": self.bloodPressureLevel,
            "unit": self.unit,
            "dateAndTimeRecorded": self.dateAndTimeRecorded,
            "createdAt": self.created_at,
            "patientId": self.patient_id,
            "healthrecordid": self.hrid
        }
        
class Medication(db.Model):
    __tablename__ = 'medication'
    mid = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(256))
    unit = db.Column(db.String(256))
    recommendedFrequency = db.Column(db.Integer)
    dosage = db.Column(db.Integer)
    inventory = db.Column(db.Integer)
    pid = db.Column(db.Integer, db.ForeignKey('patients.pid'))
    creator = db.Column(db.String(256))
    created_at = db.Column(db.DateTime, default=datetime.now)
    lastupdated_by = db.Column(db.String(256), nullable = True)
    alerts = db.relationship('Alert', backref='medication')
    audits = db.relationship('Audit', backref='medication', lazy='dynamic')
    
    def __init__(self, name, unit, recommendedFrequency, dosage, inventory, pid, creator, last_updated_by):
        self.name = name
        self.unit = unit
        self.recommendedFrequency = recommendedFrequency
        self.dosage = dosage
        self.inventory = inventory
        self.pid = pid
        self.creator = creator
        self.last_updated_by = last_updated_by
    
    def get_id(self):
        return str(self.mid)  

class MedicationAudit(db.Model):
    __tablename__ = "medicationaudit"
    auid= db.Column(db.Integer, primary_key=True, autoincrement=True)
    mid = db.Column(db.Integer, db.ForeignKey('medication.mid'))
    updated_at = db.Column(db.DateTime, default=datetime.now)
    updated_by = db.Column(db.String(256))
    
    def __init__(self, mid, updated_by):
        self.mid = mid
        self.updated_by = updated_by

       
class Alert(db.Model):
    __tablename__ = "alert"
    aid = db.Column(db.Integer, primary_key=True, autoincrement=True)
    msg = db.Column(db.String(256))
    type = db.Column(db.Enum(AlertType))
    date_time = db.Column(db.DateTime)
    pid = db.Column(db.Integer, db.ForeignKey('patients.pid'))
    mid = db.Column(db.Integer, db.ForeignKey('medication.mid'), nullable = True)
    
    def __init__(self, msg, type, date_time, pid, mid):
        self.msg = msg
        self.type = type
        self.datetime = date_time
        self.pid = pid
        self.mid = mid