from firebase import firebase
import pandas as pd
from datetime import datetime
import numpy as np
from fbprophet import Prophet
from datetime import date


#initializing firebase
firebase = firebase.FirebaseApplication('https://esp-app-10.firebaseio.com/', None)

def markov_model(data):
    """
    function to create the markov model
    args :
        data : dataframe
    return :
        Transition matrix : dictionary contain transistion matrix
    """
    #initialize empty transition matrix
    Transition_Matrix = {}
    count_dict = {}

    #get unique rooms
    rooms = data['R'].unique()
    #inintialize probabilities of each transition to zero
    for i in rooms :
        Transition_Matrix[i] = {}
        count_dict[i] = 0
        for j in rooms :
            Transition_Matrix[i][j] = 0
    #get the room of the first row
    prev = data['R'].loc[0]

    #going through the dataframe and calculate the transition count
    for i in range(1, len(data)):
        current = data['R'].loc[i]
        Transition_Matrix[prev][current] += 1
        count_dict[prev] += 1
        prev = current

    #update transition probabilities
    for i in Transition_Matrix :
        for j in Transition_Matrix[i] :
            Transition_Matrix[i][j] = Transition_Matrix[i][j] / count_dict[i]
            Transition_Matrix[i][j] = round(Transition_Matrix[i][j], 4)

    return Transition_Matrix


def store_markov_model(matrix):
    """
    function to add the transition matrix to the firebase realtime db
    args :
        matrix : transition matrix
    return :
        none
    """
    result = firebase.put('/', 'Model 03', matrix)


def transition_matrix(data):
    """
    function to store and return the transition matrix
    args :
        data
    return :
        matrix : transition matrix
    """
    #create transition matrix by calling markov_model function
    matrix = markov_model(data)
    #store transition matrix
    store_markov_model(matrix)

    return matrix