from firebase import firebase
import pandas as pd
from datetime import datetime
import numpy as np
from fbprophet import Prophet
from datetime import date
import time
from flask import request, Flask
from flask import render_template

import atexit
from apscheduler.schedulers.background import BackgroundScheduler

from models.markov import markov_model, store_markov_model, transition_matrix
from models.temporal import prophet_model_all_columns, mean_std_all_columns

#initializing the Flask app
app = Flask(__name__)

#initializing firebase
firebase = firebase.FirebaseApplication('https://esp-app-10.firebaseio.com/', None)


def onehot_encode(df):
    """
    function to one hot encode the dataframe
    args:
        df : dataframe
    return:
        data : onehot encoded dataframe
    """
    data = df.copy()
    #get unique values 
    rooms = data['R'].unique()
    for each in rooms:
        data[f'{each}'] = data['R'].apply(lambda x: 1 if x == each else 0)

    return data



def get_dataframe():
    """
    function to get the data from firebase realtime db and convert it to a dataframe
    args :
        none
    return :
        df : pandas dataframe
    """
    #getting data from SensorData collection
    result = firebase.get('/SensorData', '')
    list_dict = []
    #iterating through days

    for i in result:
        last_date = i
    for i in result:
        for j in result[i]:
            if isinstance(result[i], list):
                if j != None:
                    list_dict.append(j)
            elif isinstance(result[i], dict):
                if result[i][j] != None :
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

def last_date():
    """
    function to get the last date the data is added
    args :
        none
    return :
        last_date : last date the data is added
    """
    #getting data from SensorData collection
    result = firebase.get('/SensorData', '')
    for i in result:
        last_date = i

    return last_date

def last_val(last_date):
    """
    function to get the last value added to the collection
    args :
        last_date : last date the data is added
    return :
        result[-1] : the last value added to the collection
    """
    #getting data from SensorData collection
    result = firebase.get('/SensorData/{}'.format(last_date), '')
    print(result)
    return result[-1]


def last_val_df(last_date, dict_format = False):
    """
    function to convert the last value into a pandas dataframe
    args :
        last_date : last date the data is added
        dict_format : whether the data in dictionary format or not
    return :
        df : pandas dataframe
    """
    if dict_format :
        last_value = last_val_dict_format(last_date)
    else : 
        last_value = last_val(last_date)
    print(last_value)
    list_val_list = [last_value]
    print(list_val_list)
    data = pd.DataFrame(list_val_list)
    print(data)

    data['D'] = pd.to_datetime(data['D'])

    df = data.copy()

    df['D'] = data['D'].dt.strftime('%d-%m-%Y %H:%M')
    df['D'] = pd.to_datetime(df['D'])

    #df.set_index(['D'], inplace=True)
    return df

def last_val_dict_format(last_date):
    """
    function to get the last value added to the collection if the data is in the dictionary format
    args :
        last_date : last date the data is added
    return :
        result[-1] : the last value added to the collection
    """
    #getting data from SensorData collection
    result = firebase.get('/SensorData/{}'.format(last_date), '')
    keys = result.keys()
    keys = list(map(int, keys))

    result = result[str(keys[-1])]
    return result





#data = get_dataframe()
#initializing global variables
print(".....")
prev_value = None #previous room the user was in
data = None #data collection
df = None #onehot encoded data
dict_prophet = None #prophet prediction
dict_mean_std = None #mean std prediction
matrix = None #transition matrix
count_transition = 0 #number of transition outliers
count_temporal = 0 #number of temporal outliers
df_set = 0 


@app.route('/')
def index():
    global dict_prophet
    global prev_value
    return render_template('index.html', df=dict_prophet, time=prev_value)


def outlier_detection():
    """
    function for oulier detection and automatic generation of predictions
    args :
        none
    return :
        none
    """
    #calling global varibles
    global prev_value
    global data
    global df
    global dict_prophet
    global dict_mean_std
    global matrix
    global count_temporal
    global count_transition
    global df_set


    #getting the last date
    last_date_ = last_date()
    #getting the dataframe respect to the last value
    last_val_ = last_val_df(last_date_, dict_format=True)
    print(dict_prophet)
    print(".....")

    #get the time at which the last value is added
    time_ = last_val_['D'][0]
    print(time_)
    #training the modek at noon or if no predction is available
    if (time_.hour == 0 and time_.minute == 0) or (df_set == 0):
        print('new df is creating')
        #get data
        data = get_dataframe()
        #convert to a onehot encoded dataframe
        df = onehot_encode(data)

        #get prophet mddel prediction
        dict_prophet = prophet_model_all_columns(df)
        #get mean std model predction
        dict_mean_std = mean_std_all_columns(df)
        #get transition matrix
        matrix = transition_matrix(data)

        #initialize the outlier collection 
        result = firebase.put('/Outliers', 'Temporal Outlier', False)
        result = firebase.put('/Outliers', 'Transition Outlier', False)
        result = firebase.delete('/Outliers', 'Transition Outlier Time')
        result = firebase.delete('/Outliers', 'Temporal Outlier Time')

        #making the number of outliers to 0
        count_transition = 0
        count_temporal = 0
        df_set = 1
    #print(dict_mean_std)
    try : 
        #get the prophet predction respect to the room user is at
        df_detect = dict_prophet[last_val_['R'][0]].copy()
        print('try ... detect')
    except :
        #if the room is not avalible then output oulier is detected
        print("Outlier detected")
        #change the temporal and transition outliers to true
        result = firebase.put('/Outliers', 'Temporal Outlier', True)
        result = firebase.put('/Outliers', 'Transition Outlier', True)
        data_trans = {
                'time': last_val_['D'][0],
                'room_prev': prev_value,
                'room_current': last_val_['R'][0]
            }
        #add the outlier detectred time and room to the db
        result = firebase.put('/Outliers/Transition Outlier Time', str(count_transition), data_trans)

        data_temp = {
            'time': last_val_['D'][0],
            'room': last_val_['R'][0]
        }
        #add the outlier detectred time and room to the db
        result = firebase.put('/Outliers/Temporal Outlier Time', str(count_temporal), data_temp)
        #raise number of outlier detected by one
        count_transition += 1
        count_temporal += 1
        return

    try :
        #get the prophet predction respect to the room user is at
        #df_detect = dict_prophet[last_val_['R'][0]].copy()
        #get the predicted value
        val = df_detect.loc[str(last_val_['D'][0])]
        val = val.reset_index()
        #get the upper bound
        val = val['upper_bound'][0]
        print('try ... val')
    except :
        print("Today's data is not added")
        return
        
    print('return ... ')
    print(val)
    #check if the upperbound is less than one if so then there exists can be a outlier
    if val < 1 :
        print('prophet outlier detected')
        #get mean and std predction 
        df_mean_defect = dict_mean_std[last_val_['R'][0]].copy()
        val_mean = df_mean_defect.loc[str(last_val_['D'][0])]
        #check is the upper bound of mean std predction is less than one or not, if both models upperbound is less than one then there is an outlier
        if val_mean['upper_bound'] < 1 :
            print('Outlier detected..... ')
            result = firebase.put('/Outliers', 'Temporal Outlier', True)
            data_temp = {
                'time': last_val_['D'][0],
                'room': last_val_['R'][0]
            }
            #add the outlier detectred time and room to the db
            result = firebase.put('/Outliers/Temporal Outlier Time', str(count_temporal), data_temp)
            count_temporal += 1
        else :
            print('No Outlier detected')
    else :
        print('No Outlier detected')

    #get the current room
    current = last_val_['R'][0]
    if prev_value != None :
        #compare the probability respect to the transition 
        #the value 0.001 is an hyperparameter that should be setup based on data
        if matrix[prev_value][current] < 0.001 :
            print('Transition Outlier detected')
            result = firebase.put('/Outliers', 'Transition Outlier', True)
            data_trans = {
                'time': last_val_['D'][0],
                'room_prev': prev_value,
                'room_current': current
            }
            #add the outlier detectred time and room to the db
            result = firebase.put('/Outliers/Transition Outlier Time', str(count_transition), data_trans)
            count_transition += 1
        else:
            print("No transition outliers")

    prev_value = current


#shedule the oultlier detection function at every minute
scheduler = BackgroundScheduler()
scheduler.add_job(outlier_detection,'interval',minutes=1)
scheduler.start()
# Shutdown your cron thread if the web process is stopped
atexit.register(lambda: scheduler.shutdown(wait=False))


if __name__ == '__main__':
	app.run()