#!/usr/bin/env python
# coding: utf-8

# # REVIEWS
# - `main_legs` and `start_legs` issue 
#     - may need to generate the `start_legs` for every trips due to the shuttle trip issue of start_place
# - Whether any minimum number of trips needed . Issue with shuttle trip 
# 
# 

# ### SET UP AND IMPORTS 

# In[211]:


# SET UP AND IMPORTS 
import pandas as pd 

df = pd.read_excel('dataset/processed/psl.xlsx')
# Adding the Terminal Gap and Duty only for processing 
df['Terminal Gap'] = [0] * len(df)
df['Duty'] = [0] * len(df)

START_PLACE = 'PSL'
#start_legs contain the legs with departure place as start_place
start_legs = df[df['Departure Place'] == START_PLACE].sort_values('Departure Time', ascending=True)
#main_legs contains all other legs 
main_legs = df[df['Departure Place'] != START_PLACE]
MIN_DUTY = 25200 #setting the minimum duty as 7:00 hrs 
# The ideal duty is 7:30 hrs with a 15 min break at the start and end . Then total 8:00 
MAX_DUTY = 30600 # setting the maximum duty as 8:30 hrs
MIN_TERMINAL_GAP = 300
MAX_TERMINAL_GAP = 900


# ### SUPPORTING FUNCTIONS 

# In[229]:


#SUPPORTING FUNCTIONS 
def generateTempSet(leg):
    # Creating a copy of the main legs
    temp_set = df[(df['Departure Place'] == leg['Arrival Place']) & (df['Departure Time'] > leg['Arrival Time act'])]
    temp_set = temp_set.sort_values('Departure Time', ascending=True).reset_index(drop=True)
    temp_set['Terminal Gap'] = temp_set['Departure Time'] - leg['Arrival Time act']
    # Sorting and resetting index
    temp_set['Duty'] = leg['Duty'] + temp_set['Running Time'] + temp_set['Terminal Gap']
    # display(temp_set)
    temp_set = temp_set[
        (temp_set['Terminal Gap'] >= MIN_TERMINAL_GAP) & (temp_set['Terminal Gap'] < MAX_TERMINAL_GAP) #|
        #(temp_set['Duty'] >= MIN_DUTY) & (temp_set['Duty'] <= MAX_DUTY)  
    ]
    return temp_set

generateTempSet(start_legs.iloc[0])

def popTempSet(temp_set) -> pd.DataFrame:
    temp_set.drop(0, inplace= True)
    temp_set.reset_index(inplace=True)
    return temp_set.drop('index',axis= 1)


def displayTrip(stack):
    frame = pd.DataFrame()
    for x in stack:
        frame = pd.concat([frame, (x['current_leg'].to_frame()).T], ignore_index=True)
    frame['Terminal Gap'] = frame['Terminal Gap'].shift(-1)
    duty = frame['Duty'].iloc[len(frame) - 1]
    frame = frame.drop('Duty', axis=1)

    return [frame, duty]

# def seconds_to_time(df, columns):
#     df[columns] = df[columns].apply(lambda x: pd.to_datetime(x, unit='s').dt.strftime('%H:%M:%S'))


# ### ALGORITHM

# In[230]:


# ALGORITHM
def generateTrip(start_leg):
    stack = [{"current_leg": start_leg, "temp_set": pd.DataFrame()}] # contain the legs in the trip 
    temp_set = generateTempSet(start_leg)
    stack.append({"current_leg": temp_set.iloc[0], "temp_set": popTempSet(temp_set)})
    while len(stack) > 1 : # and stack[-1]['current_leg']['Arrival Place'] != START_PLACE
        temp_set = generateTempSet(stack[-1]['current_leg'])
        if temp_set.empty :
            stack.pop()
            while(stack[-1]['temp_set'].empty) :
                    stack.pop()
            stack[-1]['current_leg'] = stack[-1]['temp_set'].iloc[0]
            stack[-1]['temp_set'] = popTempSet(stack[-1]['temp_set'])
            # print("Got null 11")
            # print(stack)
            # display(displayTrip(stack))
            continue
        stack.append({"current_leg": temp_set.iloc[0], "temp_set": popTempSet(temp_set)})
        if (top_leg:=stack[-1]['current_leg'])['Arrival Place'] == START_PLACE:
            if MIN_DUTY > top_leg['Duty']:
                # NEED TO ADDRESS SHUTTLE TRIP ISSUE OF START_PLACE
                while(stack[-1]['temp_set'].empty) :
                    stack.pop()
                stack[-1]['current_leg'] = stack[-1]['temp_set'].iloc[0]
                stack[-1]['temp_set'] = popTempSet(stack[-1]['temp_set'])

            elif top_leg['Duty'] > MAX_DUTY:
                stack.pop()
                while(stack[-1]['temp_set'].empty) :
                    stack.pop()
                stack[-1]['current_leg'] = stack[-1]['temp_set'].iloc[0]
                stack[-1]['temp_set'] = popTempSet(stack[-1]['temp_set'])

            else: # MIN_DUTY <= top_leg['Duty'] <= MAX_DUTY 
                #ideal case 
                break;
    result = displayTrip(stack)
    # display(result[0])
    print(result[0])
generateTrip(start_legs.iloc[0])
    


# ### MAIN PART

# In[164]:


# MAIN



