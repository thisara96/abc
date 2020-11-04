from firebase import firebase
import pandas as pd
from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler
import atexit
from flask import Flask, request, jsonify
import time


firebase = firebase.FirebaseApplication('https://esp-app-10.firebaseio.com/', None)

def last_date():
    result = firebase.get('/Sensor', '')
    for i in result:
        last_date = i
 
    return last_date

def last_val(last_date, ):
    result = firebase.get('/Sensor/{}'.format(last_date), '')
    return result[-1]

def get_data():
    result = firebase.get('/SensorData', '')
    list_dict = []
    #iterating through days
    print(result)
    for i in result:
        last_date = i
    for i in result:
        for j in result[i]:
            if isinstance(result[i], list):
                if j != None:
                    list_dict.append(j)
            elif isinstance(result[i], dict):
                list_dict.append(result[i][j])
    
    #convert the data into a dataframe

    data = pd.DataFrame(list_dict)
    #changing the datatype of the column D to days
    data['D'] = pd.to_datetime(data['D'])

    df = data.copy()
    #get minute by minute data by removing the seconds value
    df['D'] = data['D'].dt.strftime('%d-%m-%Y %H:%M')
    df['D'] = pd.to_datetime(df['D'])

    return df

#last_date_ = last_date()

#result = firebase.get('/SensorData', '')

#print(result)

print(get_data())
#print(len(get_data()))