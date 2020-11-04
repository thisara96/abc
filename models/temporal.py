from firebase import firebase
import pandas as pd
from datetime import datetime
import numpy as np
from fbprophet import Prophet
from datetime import date
from datetime import timedelta


#initializing firebase
firebase = firebase.FirebaseApplication('https://esp-app-10.firebaseio.com/', None)

def post_data(df, column,path):
    """
    function to add a dataframe to the firebase realtime db
    args :
        df : dataframe that needed to be added
        column : column name of the dataframe(in this context it is room name)
    return : 
        none
    """
    data = df.to_dict()
    result = firebase.put(path, column , data)

def prophet_preprocess(df, column):
    """
    function to preprocess data according to the requirement of th prophet library
    args :
        df : onehot encoded dataframe
        column : column to which the model is made
    return :
        data : preprocessed dataframe
    """
    data = df.copy()
    #change date column to ds and column to which the predictions are made to y
    data = data.rename(columns = {'D':'ds', column: 'y'})

    #set a cap and floor
    data['cap'] = 1
    data['floor'] = 0
    return data

def prophet_model(df):
    """
    function to create a prophet time series model
    args : 
        df : preprocessed dataframe
    return :
        df_future : forecast dataframe 
    """
    #create prophet model
    m = Prophet(changepoint_prior_scale=0.01)
    m.fit(df)
    #making the future dataframe
    future = m.make_future_dataframe(periods=1440, freq='min')
    #setting the cap and the floor
    future['cap'] = 1
    future['floor'] = 0
    #make predictions using the model
    forecast = m.predict(future)
    #get yhat, upper bound and the lowerbound
    df_future = forecast[['ds', 'yhat', 'yhat_lower', 'yhat_upper']]
    return df_future

def prophet_postprocessing(future , df):
    """
    function to post process the the forecast made using prophet model
    args :
        future : forecast dataframe
        df : preprocess dataframe
    return :
        df_nextday : post processed dataframe
    """
    #extract the next day forecast
    df_nextday = future.iloc[len(df) - 1:]

    df_nextday.set_index(['ds'], inplace = True)
    df_nextday = df_nextday.reset_index()

    #setting the upper bound 
    df_nextday.loc[df_nextday['yhat'] >= 1, 'yhat'] = 1
    df_nextday.loc[df_nextday['yhat_upper'] >= 1, 'yhat_upper'] = 1
    df_nextday.loc[df_nextday['yhat_lower'] >= 1, 'yhat_lower'] = 1

    #setting the lower bound
    df_nextday.loc[df_nextday['yhat'] <= 0, 'yhat'] = 0
    df_nextday.loc[df_nextday['yhat_upper'] <= 0, 'yhat_upper'] = 0
    df_nextday.loc[df_nextday['yhat_lower'] <= 0, 'yhat_lower'] = 0

    #rename the coulmns 
    df_nextday = df_nextday.rename(columns = {'ds':'time', 'yhat': 'mean', 'yhat_lower':'lower_bound', 'yhat_upper':'upper_bound'})

    #set the next day prediction as tomorrow's prediction
    #important when contianing missing data 
    df_nextday["minute"] = df_nextday['time'].map(lambda x: x.minute)
    df_nextday["hour"] = df_nextday['time'].map(lambda x: x.hour)
    df_nextday['minutes'] = df_nextday['minute'] + df_nextday['hour'] * 60
    df_nextday['time'] = datetime.combine(date.today() , datetime.min.time()) + pd.TimedeltaIndex(df_nextday['minutes'], unit='m')
    df_nextday.drop(['minutes', 'hour', 'minute'], axis=1, inplace=True)

    return df_nextday


def prophet_model_all_columns(df):
    """
    function to create prophet models for all columns
    args : 
        df : onehot encoded dataframe
    return :
        dict_prophet : dictionary containing prophet predictions for all columns
    """
    data = df.copy()
    #extractiong the last 5000 datapoints 
    #model can be made with all the data but this requires a RAM of atleast 4GB
    data = data[-5000:]

    #delete the existing predictions
    firebase.delete('/', 'Model 01')

    rooms = data['R'].unique()
    #initilizing an empty ditionary
    dict_prophet = {}
    #iterating through rooms and make predictions
    for column in rooms:
        #getting preprocessed dataframe
        df_ = prophet_preprocess(data, column)
        #generate the forecast
        future = prophet_model(df_)
        #get post processed dataframe
        future = prophet_postprocessing(future , df_)

        path = 'Model 01/'
        #post the forecast into firebase realtime db
        post_data(future, column, path)
        future.set_index(['time'], inplace = True)

        dict_prophet[column] = future.copy()

    return dict_prophet

def std(x): 
    """
    function to calculate standard deviation
    args :
        x : numpy array
    return : 
        np.std(x) : numpy array containing standard deviation
    """
    return np.std(x)

def mean_std_model(data):
    """
    function to build mean and standard deviation model
    args : 
        data : onehot encoded dataframe
    return : 
        df : dataframe containing mean and standard deviation
    """
    df = data.copy()
    df["minute"] = df['D'].map(lambda x: x.minute)
    df["hour"] = df['D'].map(lambda x: x.hour)
    #get mean and standard deviation of each columnn
    df_g = df.groupby(['hour','minute']).agg(['mean', std])
    df = df_g.reset_index()
    #set the mean as the predction
    df['minutes'] = df['minute'] + df['hour'] * 60
    df['time'] = datetime.combine(date.today() , datetime.min.time()) + pd.TimedeltaIndex(df['minutes'], unit='m')
    df.drop(['minutes', 'hour', 'minute'], axis=1, inplace=True)

    return df

def get_bounds(data, column):
    """
    function to calculate the upperbound and the lower bound
    args :
        data : dataframe containing mean and standard deviation
        column : column name
    return :
        mean_df : dataframe containing mean and bounds
    """
    df = data.copy()
    df = df.set_index(['time'])
    #convert mean and stanrd deviation into a series
    mean_series = df.loc[:, (column, 'mean')].copy()
    std_series = df.loc[:, (column, 'std')].copy()

    mean_df = pd.DataFrame({'mean': mean_series, 'std': std_series})

    upper_bound = []
    lower_bound = []
    num_rows = mean_df.shape[0]
    #calculate the upperbound and the lowerbound for each row(at each time interval)
    for i in range(num_rows):
        #calculate the upperbound at 95% confidence interval
        upper_bound.append(mean_df.iloc[i]['mean'] + 2 * mean_df.iloc[i]['std'])
        #calculate the lowerbound at 95% confidence interval
        lower_bound.append(mean_df.iloc[i]['mean'] - 2 * mean_df.iloc[i]['std'])
    
    #add upperbound and lowerbound to the dataframe
    mean_df['upper_bound'] = upper_bound
    mean_df['lower_bound'] = lower_bound

    mean_df = mean_df.reset_index()
    mean_df.drop('std', axis=1, inplace=True)
    return mean_df

def mean_std_postprocessing(df):
    """
    function to post process the the forecast made using mean and std model
    args :
        df : forecast from mean and std model
    return :
        df_nextday : post processed dataframe
    """
    df_nextday = df.copy()
    #setting the upper bound 
    df_nextday.loc[df_nextday['mean'] >= 1, 'mean'] = 1
    df_nextday.loc[df_nextday['upper_bound'] >= 1, 'upper_bound'] = 1
    df_nextday.loc[df_nextday['lower_bound'] >= 1, 'lower_bound'] = 1

    #setting the lower bound 
    df_nextday.loc[df_nextday['mean'] <= 0, 'mean'] = 0
    df_nextday.loc[df_nextday['upper_bound'] <= 0, 'upper_bound'] = 0
    df_nextday.loc[df_nextday['lower_bound'] <= 0, 'lower_bound'] = 0

    return df_nextday 



def mean_std_all_columns(df):
    """
    function to create and store forecast from mean std model
    """
    data = df.copy()
    rooms = data['R'].unique()
    #delete the existing prediction
    firebase.delete('/', 'Model 02')
    #get the prediction
    data = mean_std_model(data)

    #initialize an empty dictionary
    dict_mean_std = {}
    for column in rooms:
        #get bounds
        df_ = get_bounds(data, column)
        #post process the prediction
        df_ = mean_std_postprocessing(df_)

        #post the forecast into firebase realtime db
        path = 'Model 02/'
        post_data(df_, column, path)

        df_.set_index(['time'], inplace = True)
        #add forecast to the dictionary
        dict_mean_std[column] = df_.copy()
    
    return dict_mean_std
