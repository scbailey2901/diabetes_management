from . import db
from datetime import datetime, time
from werkzeug.security import generate_password_hash
from enum import Enum
import time

patient_caregiver = db.Table(
    'patient_caregiver',
    db.Column('patient_id', db.Integer, db.ForeignKey('patients.pid')),
    db.Column('caregiver_id', db.Integer, db.ForeignKey('caregivers.cid'), nullable=True),
    db.UniqueConstraint('patient_id', 'caregiver_id', name='uix_patient_caregiver')
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

class SymptomType(Enum):
    MOOD = "mood"
    SLEEP = "sleep"
    APPETITE = "apetite"
    ACTIVITY = "activity"
    OTHER= "other"

class MealType(Enum):
    BEVERAGE = "beverage"
    BREAKFAST = "breakfast"
    LUNCH = "lunch"
    DINNER = "dinner"
    BRUNCH = "brunch"
    SNACK ="snack"
    DESSERT = "dessert"
    
class FoodOrDrink(Enum):
    Food = "food"
    DRINK = "drink"
    FOODANDDRINK = "foodanddrink"
    
class DiabetesType(Enum):
    TYPEONE = "typeone"
    TYPETWO = "typetwo"

class RecTime(Enum):
    AFTERMEAL ="aftermeal"
    BEFOREMEAL = "beforemeal"
    

class Patients(db.Model):
    __tablename__ = 'patients'
    pid = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(200), unique=False, nullable=False)
    age = db.Column(db.Integer)
    dob = db.Column(db.DateTime)
    email = db.Column(db.String(256), unique = True)
    username = db.Column(db.String(200), unique=True)
    password = db.Column(db.String(256), nullable=False)
    phonenumber = db.Column(db.String(15), unique = True)
    gender = db.Column(db.Enum(Gender), nullable=False)
    consentForData = db.Column(db.String(20))
    joined_on = db.Column(db.DateTime, default=datetime.now())
    caregivers = db.relationship('Caregivers', secondary=patient_caregiver, back_populates='patients')
    health_records = db.relationship('HealthRecord', backref='patient', lazy=True)
    mealdiary = db.relationship('MealDiary', backref='patient', lazy=True)


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
    height = db.Column(db.Float)
    heightUnits = db.Column(db.String(50))
    diabetesType = db.Column(db.Enum(DiabetesType))
    isSmoker = db.Column(db.Boolean, default = False)
    isDrinker = db.Column(db.Boolean, default = False)
    hasHighBP = db.Column(db.Boolean, default = False)
    hasHighChol = db.Column(db.Boolean, default = False)
    hasHeartDisease = db.Column(db.Boolean, default = False)
    hadHeartAttack = db.Column(db.Boolean, default = False)
    hadStroke = db.Column(db.Boolean, default = False)
    hasTroubleWalking = db.Column(db.Boolean, default = False)
    bloodSugarlevels = db.relationship('BloodSugarLevels', backref='healthrecord', lazy = True)
    bloodPressurelevels = db.relationship('BloodPressureLevels', backref='healthrecord', lazy = True)
    symptoms = db.relationship('Symptom', backref='healthrecord', lazy = True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patients.pid'))
    
    def __init__(self, age, weight,weightUnits, height, heightUnits,diabetesType,isSmoker, isDrinker, hasHighBP, hasHighChol, hasHeartDisease, hadHeartAttack, hadStroke,hasTroubleWalking,bloodSugarlevels,bloodPressurelevels,patient_id ):
        self.age = age
        self.weight = weight
        self.weightUnits = weightUnits
        self.heightUnits = heightUnits
        self.height = height
        self.diabetesType = diabetesType
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
    email = db.Column(db.String(256), unique = True)
    password = db.Column(db.String(200))
    phonenumber = db.Column(db.String(15), unique = True)
    gender = db.Column(db.Enum(Gender))
    consentForData = db.Column(db.String(20))
    joined_on = db.Column(db.DateTime, default=datetime.now())
    patients = db.relationship('Patients', secondary=patient_caregiver, back_populates='caregivers')
    credentials = db.relationship('Credentials', backref='caregivers', lazy = True)

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

    def file_path(self):
        if self.filename:
            return f'uploads/{self.filename}'
        else:
            return None

    def __init__(self, filename, credentialtype, caregiver_id):
        self.filename = filename
        self.credentialtype = credentialtype
        self.caregiver_id = caregiver_id

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
    unit = db.Column(db.String(150))
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
    unit = db.Column(db.String(150))
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
    recommendedTime = db.Column(db.Enum(RecTime))
    amount = db.Column(db.Integer)
    # dosage = db.Column(db.String(150))
    inventory = db.Column(db.Integer)
    pid = db.Column(db.Integer, db.ForeignKey('patients.pid'))
    creator = db.Column(db.String(256))
    created_at = db.Column(db.DateTime, default=datetime.now)
    last_updated_by = db.Column(db.String(256), nullable = True)
    reminderTimes = db.relationship('MedicationTime', backref='medication', lazy =True)
    alerts = db.relationship('Alert', backref='medication', lazy =True)
    audits = db.relationship('MedicationAudit', backref='medication', lazy=True)
    
    def __init__(self, name, unit, recommendedFrequency, recommendedTime, amount, inventory, pid, creator, last_updated_by):
        self.name = name
        self.unit = unit
        self.recommendedFrequency = recommendedFrequency
        self.recommendedTime = recommendedTime
        self.amount = amount
        # self.dosage = dosage
        self.inventory = inventory
        self.pid = pid
        self.creator = creator
        self.last_updated_by = last_updated_by
    
    def get_id(self):
        return str(self.mid)  


class MedicationTime(db.Model):
    __tablename__ = "medtime"
    mtid = db.Column(db.Integer, primary_key=True, autoincrement=True)
    time = db.Column(db.Time)
    mid = db.Column(db.Integer, db.ForeignKey('medication.mid'))
    
    def __init__(self, time, mid):
        self.time = time
        self.mid = mid
    
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
    time = db.Column(db.Time)
    pid = db.Column(db.Integer, db.ForeignKey('patients.pid'))
    mid = db.Column(db.Integer, db.ForeignKey('medication.mid'), nullable = True)
    
    
    def __init__(self, msg, type, time, pid, mid):
        self.msg = msg
        self.type = type
        self.time = time
        self.pid = pid
        self.mid = mid


class MealEntry(db.Model):
    __tablename__ = "mealentry"
    meid= db.Column(db.Integer, primary_key=True, autoincrement=True)
    portiontype = db.Column(db.String(250))
    servingSize = db.Column(db.Integer)
    date_and_time = db.Column(db.DateTime)
    mealtype = db.Column(db.Enum(MealType))
    mealOrDrink = db.Column(db.Enum(FoodOrDrink))
    meal = db.Column(db.String(250))
    pid = db.Column(db.Integer, db.ForeignKey('patients.pid'))
    nutrients = db.relationship('Nutrients', backref='mealentry', lazy=True)
    mealdiaryid = db.Column(db.Integer, db.ForeignKey('mealdiary.mdid'))
    audits = db.relationship('MealEntryAudit', backref='mealentry', lazy=True)
    
    def __init__(self, portiontype, servingSize, date_and_time, mealtype, mealOrDrink, meal, pid):
        self.portiontype = portiontype
        self.servingSize = servingSize
        self.date_and_time = date_and_time
        self.mealtype = mealtype
        self.mealOrDrink = mealOrDrink
        self.meal = meal 
        self.pid = pid
        # self.nutrients_id = nutrients_id
        
class MealEntryAudit(db.Model):
    __tablename__ = "mealentryaudit"
    me_auid= db.Column(db.Integer, primary_key=True, autoincrement=True)
    meid = db.Column(db.Integer, db.ForeignKey('mealentry.meid'))
    updated_at = db.Column(db.DateTime, default=datetime.now)
    updated_by = db.Column(db.String(256))
    
    def __init__(self, mid, updated_by):
        self.mid = mid
        self.updated_by = updated_by

class MealDiary(db.Model):
    __tablename__ = "mealdiary"
    mdid = db.Column(db.Integer, primary_key=True, autoincrement=True)
    pid = db.Column(db.Integer, db.ForeignKey('patients.pid'))
    allMeals = db.relationship("MealEntry", backref="mealdiary", lazy=True)
    
    def __init__(self, pid):
        self.pid = pid
        
    
class Nutrients(db.Model):
    __tablename__ = "nutrients"
    nid = db.Column(db.Integer, primary_key=True, autoincrement=True)
    sugar_in_g = db.Column(db.Float)
    protein_in_g = db.Column(db.Float)
    sodium_in_mg = db.Column(db.Float)
    calories = db.Column(db.Float)
    fat_total_g = db.Column(db.Float)
    fat_saturated_g = db.Column(db.Float)
    potassium_mg = db.Column(db.Float)
    cholesterol_mg = db.Column(db.Float)
    carbohydrates_total_g = db.Column(db.Float)
    meid = db.Column(db.Integer, db.ForeignKey('mealentry.meid'), unique=True)
    
    
    def __init__(self, sugar_in_g, protein_in_g, sodium_in_mg, calories, fat_total_g, fat_saturated_g, potassium_mg, cholesterol_mg, carbohydrates_total_g, meid):
        self.sugar_in_g = sugar_in_g
        self.protein_in_g = protein_in_g
        self.sodium_in_mg = sodium_in_mg
        self.calories = calories
        self.fat_total_g = fat_total_g
        self.fat_saturated_g = fat_saturated_g
        self.potassium_mg = potassium_mg
        self.cholesterol_mg = cholesterol_mg
        self.carbohydrates_total_g = carbohydrates_total_g
        self.meid = meid
        
class Symptom(db.Model):
    __tablename__ = "symptom"
    sid = db.Column(db.Integer, primary_key=True, autoincrement=True)
    severity = db.Column(db.Integer)
    date_and_time = db.Column(db.DateTime)
    symptom_name = db.Column(db.String(250))
    symptomType = db.Column(db.Enum(SymptomType))
    patient_id = db.Column(db.Integer, db.ForeignKey('patients.pid'))
    hrid = db.Column(db.Integer, db.ForeignKey('healthrecord.hrid'))
    
    def __init__(self, symptom_name, symptomType, severity, date_and_time, notes, patient_id, hrid):
        self.symptom_name = symptom_name
        self.symptomType = symptomType
        self.severity = severity
        self.date_and_time = date_and_time
        self.notes = notes
        self.patient_id= patient_id
        self.hrid = hrid