CREATE DATABASE if not exists diabetes;
#Twanda-Lee Briscoe
use diabetes;

CREATE USER 'diabetes'@'localhost';
GRANT ALL PRIVILEGES ON diabetes.* TO 'diabetes'@localhost;

CREATE TABLE BloodSugarLevels(
    bslID INT PRIMARY KEY NOT NULL AUTO_INCREMENT,
    dateAndTime DATETIME, 
    patientid INT 
);

CREATE TABLE Patient (
    pid INT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(50),
    username VARCHAR(50),
    password VARCHAR(50),
    phonenumber VARCHAR(50), 
    gender VARCHAR(50)
);

CREATE TABLE Caregiver (
    cid INT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(50),
    username VARCHAR(50),
    password VARCHAR(50),
    phonenumber VARCHAR(50), 
    gender VARCHAR(50),
    
);

CREATE TABLE Credentials (
    crid INT PRIMARY KEY AUTO_INCREMENT,
    cid INT PRIMARY KEY AUTO_INCREMENT,
    caregiver VARCHAR(50),
    filename NOT NULL VARCHAR(50)

);