from firebase import firebase
import pandas as pd
from datetime import datetime
import time


firebase = firebase.FirebaseApplication('https://esp-app-10.firebaseio.com/', None)

list_R = [
    'Room 01','Room 01', 'Room 01', 'Room 01', 'Room 01', 'Room 01', 'Room 01', 'Room 01', 'Room 01', 
    'Room 01','Room 01', 'Room 01', 'Room 01', 'Room 01', 'Room 01', 'Room 01', 'Room 01', 'Room 01',
    'Room 01','Room 01', 'Room 01', 'Room 01', 'Room 01', 'Room 01', 'Room 01', 'Room 01', 'Room 01',
    'Room 01','Room 01', 'Room 01', 'Room 01', 'Room 01', 'Room 01', 'Room 01', 'Room 01', 'Room 01',
    'Room 01','Room 01', 'Room 01', 'Room 01', 'Room 01', 'Room 01', 'Room 01', 'Room 01', 'Room 01',
    'Room 01','Room 01', 'Room 01', 'Room 01', 'Room 01', 'Room 01', 'Room 01', 'Room 01', 'Room 01',
    'Room 01','Room 01', 'Room 01', 'Room 01', 'Room 01', 'Room 01', 'Room 01', 'Room 01', 'Room 01',
    'Room 01','Room 01', 'Room 01', 'Room 01', 'Room 01', 'Room 01', 'Room 01', 'Room 01', 'Room 01',
    'Room 01','Room 01', 'Room 01', 'Room 01', 'Room 01', 'Room 01', 'Room 01', 'Room 01', 'Room 01',
    'Room 01', 'Living Room','Living Room','Living Room','Living Room', 'Living Room','Living Room',
    'Living Room','Living Room', 'Room 02', 'Room 02', 'Room 02', 'Room 02', 'Room 02', 'Room 02',
    'Room 02', 'Living Room', 'Living Room', 'Dining Room', 'OUT', 'OUT', 'OUT', 'OUT', 'OUT', 'OUT',
    'OUT', 'OUT','OUT', 'OUT','OUT', 'OUT','OUT', 'OUT', 'Room 01', 'Room 01', 'Room 01', 'Room 01', 
    'Room 01', 'Room 01', 'Room 01', 'Room 02', 'Room 02', 'Room 02', 'Room 02', 'Washroom', 'Washroom'
    ]

def write_db(count, list_data):
    """
    function to add data in a list format
    """
    now = datetime.now()
    dt_string = now.strftime("%d/%m/%Y %H:%M:%S")
    i = count % 2
    R = list_R[i]
    data = {
        'D' : dt_string,
        'R' : list_R[i]
    }
    print(list_data)
    list_data.append(data)
    result = firebase.put('/Sensor', '09_19', list_data)

def write_db_dict(count):
    """
    function to add data in a dictionary format
    """
    now = datetime.now()
    day = str(now.day)
    month = str(now.month)
    if len(day) == 1 :
        day = "0" + day
    dt_string = now.strftime("%d/%m/%Y %H:%M:%S")
    date_path = month + "_" + day

    print(dt_string)
    i = count % len(list_R)
    R = list_R[i]
    data = {
        'D' : dt_string,
        'R' : list_R[i]
    }
    print(data)
    result = firebase.put('/SensorData/{}'.format(date_path), str(count), data)

    #return list_data


count = 10
list_data = []
while(True):
    write_db_dict(count)
    count += 1
    time.sleep(60)
