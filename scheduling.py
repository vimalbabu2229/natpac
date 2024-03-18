#SET UP AND IMPORTS 
import pandas as pd 
import datetime
import time
import json

df = pd.DataFrame()
START_PLACE = 'PSL'
#start_legs contain the legs with departure place as start_place
start_legs = pd.DataFrame()
# MIN_DUTY = 27000 #setting the minimum duty as 7:00 hrs 
MIN_DUTY = 7 * 3600 #setting the minimum duty as 7:00 hrs + 15min sign in  and 15 min sign out = 07:30 hrs
# The ideal duty is 7:30 hrs with a 15 min break at the start and end . Then total 8:00 
# MAX_DUTY = 30600 # setting the maximum duty as 8:30 hrs
MAX_DUTY = 9 * 3600  # setting the maximum duty as 09:00 hrs + 15min sign in  and 15 min sign out = 09:30 hrs
MAX_SPREAD_OVER = 43200 # setting maximum spread over to 12 hrs 
MIN_TERMINAL_GAP = 300
MAX_TERMINAL_GAP = 900
BREAK = 1800 # break time of 30 min to avoid 5hrs continuous working
IS_BREAK = False # setting the break status as false by default 
MAX_SPLIT = 3600 # Setting the maximum split time as 60 min 
MIN_TEMPSET_SIZE = 2 # define the minimum number of legs in a temp_set
BREAK_LIMIT_DUTY = 18000 # 5hrs of continuous duty  
MIN_LIMIT_DUTY = 12600 # After 3.5 hrs of duty we can try entering the 30 min break

# FOR THE PURPOSE OF MEASURING THE PERFORMANCE 
success = 0 # Not necessary , just to count the number of start legs taken 
trips_count = 0 # count the number of trips 
exe_generateTempSet  = 0
exe_popTempSet  = 0
start_legs

def secToTime(seconds):
    hrs, rem = divmod(seconds, 3600)
    mint, sec = divmod(rem , 60)
    return datetime.time(hour=hrs, minute=mint, second= sec)

# #### Generate Tempset 
# - Below function creates the temset for a particular leg in the stack . It checks for the needed criteria and then creates the set of legs that are possibly gives us a feasible solution 
def generateTempSet(leg, mode = 0) -> pd.DataFrame:
    # mode 0 means normal trips and mode 1 means consider 30 min break also
    # FN LOGIC IS NOT CORRECT , NEED TO CREATE THE TEMP SET ONLY WITH THE CRITERIA
    # SORTING THEM AFTER CREATING THE ENTIRE TEMPSET IS NOT OPTIMAL
    global exe_generateTempSet
    x = time.time()

    # Creating a copy of the main legs.Can be limited with steering duty remaining 
    temp_set_df = df[(df['Departure Place'] == leg['Arrival Place'])
                  & (df['Departure Time'] > leg['Arrival Time'])]
    temp_set_df = temp_set_df.sort_values(
        'Departure Time', ascending=True).reset_index(drop=True)
    temp_set_df['Terminal Gap'] = temp_set_df['Departure Time'] - leg['Arrival Time']
    # Sorting and resetting index
    # '''BELOW LINE MAY BE NOT NECESSARY'''
    # display(temp_set)
    temp_set = pd.DataFrame()
    # THERE ARE CHANCES THAT THE TEMP SET MAY BE EMPTY , SO WE ARE TRYING FOR 
    #  THE NEXT LEVEL SEARCHING
    if mode == 0:
        min_terminal_gap = MIN_TERMINAL_GAP
        terminal_gap = MAX_TERMINAL_GAP
        ADD_ON = 900 # 15 min
    else :
        min_terminal_gap = BREAK
        terminal_gap = BREAK + MAX_TERMINAL_GAP
        ADD_ON = 900 # 15 min
    # NEED TO OPTIMIZE BELOW LOOP AS EVERY TIME IT LOOPS THROUGH THE ENTIRE LEGS TILL
    # THE SPECIFIED TERMINAL GAP , CAN USE EXTEND OR CONCAT TO ITERATIVELY ADDING UP THE 
    # TEMP SET  
    while len(temp_set) < MIN_TEMPSET_SIZE and terminal_gap < MAX_SPLIT: # 1 hr split
        temp_set = temp_set_df[
            (temp_set_df['Terminal Gap'] >= min_terminal_gap) & (
                temp_set_df['Terminal Gap'] < terminal_gap)  # |
            # (temp_set['Duty'] >= MIN_DUTY) & (temp_set['Duty'] <= MAX_DUTY)
        ]
        terminal_gap += ADD_ON
    # print(f"Type of gap = {type(temp_set['Terminal Gap'][0])}")
    # temp_set['Duty'] = leg['Duty'] + temp_set['Running Time'] + temp_set['Terminal Gap']
    temp_set.loc[:, 'Duty'] = leg['Duty'] + temp_set['Running Time'] # should bee run for all legs
    # temp_set.loc[temp_set['Terminal Gap'] < MAX_TERMINAL_GAP, 'Duty'] += temp_set.loc[temp_set['Terminal Gap'] < MAX_TERMINAL_GAP, 'Terminal Gap']
    mask = temp_set['Terminal Gap'] < MAX_TERMINAL_GAP
    temp_set.loc[mask, 'Duty'] += temp_set.loc[mask, 'Terminal Gap']
    y = time.time()
    exe_generateTempSet += (y - x)
    # if len(temp_set) < 2 : print(f"Size of tempset == {len(temp_set)}")
    temp_set.reset_index(drop=True, inplace=True)
    return temp_set

#  Pop Tempset 
# - This function pops the currently visited leg from the corresponding tempset, then the tempset will always contain the possible legs from a given leg that satisfies the criteria needed   
def popTempSet(temp_set) -> pd.DataFrame:
    global exe_popTempSet
    x = time.time()
    temp_set.drop(0, inplace=True)
    # print("popTempSet")
    # display(temp_set)
    temp_set.reset_index(inplace=True)
    temp_set.drop('index',axis= 1, inplace=True)
    y = time.time()
    exe_popTempSet += (y - x)
    return temp_set

## Display Trip
def displayTrip(stack):
    global trips_count
    frame = pd.DataFrame()
    for x in stack:
        frame = pd.concat([frame, (x['current_leg'].to_frame()).T], ignore_index=True)
    frame['Terminal Gap'] = frame['Terminal Gap'].shift(-1)
    #Calculating the steering duty 
    duty = secToTime(frame['Duty'].iloc[len(frame) - 1])
    spread_over = secToTime((stack[-1]['current_leg'])['Arrival Time'] - (stack[0]['current_leg'])['Departure Time'])
    frame = frame.drop('Duty', axis=1)
    trips_count += 1
    return [frame, duty, spread_over]

def seconds_to_time(df, columns):
    df[columns] = df[columns].apply(lambda x: pd.to_datetime(x, unit='s').dt.strftime('%H:%M:%S'))

#Remove Legs
# - Once a leg is taken for a trip , it should be removed so that it will not be considered for the next round of iterations  
def removeLegs(trip) -> None:
    global success
    for i in range(len(trip)):
        if trip.iloc[i]['Departure Place'] == START_PLACE:
            # remove from both df and start_legs 
            df.drop((df[df['Sl No.'] == trip.iloc[i]['Sl No.']]).index, axis= 0, inplace=True)
            start_legs.drop((start_legs[start_legs['Sl No.'] == trip.iloc[i]['Sl No.']]).index, axis= 0, inplace=True)
            df.reset_index(drop=True, inplace=True)
            start_legs.reset_index(drop=True, inplace=True)
            success += 1
        else:
            # remove only from df 
            df.drop((df[df['Sl No.'] == trip.iloc[i]['Sl No.']]).index, axis= 0, inplace=True)
            df.reset_index(drop=True, inplace=True)
        

#Backtracking 
 
def backtrack(stack):
    #  If temp_set is empty , it means that we cannot go to any other places from the 
    # last leg , so we can pop the last leg in the stack  
    stack.pop()
    # After popping stack top , there are also chances that the temp_set of top elements 
    # in the stack may be empty, so those ones also should be popped out, because we cannot 
    # goto anywhere else from there  
    while(stack[-1]['temp_set'].empty) :
            stack.pop()
    stack[-1]['current_leg'] = stack[-1]['temp_set'].iloc[0]
    stack[-1]['temp_set'] = popTempSet(stack[-1]['temp_set'])

# Decorators 
def exception_handler(func):
    def wrapper(stack):
        try:
            return func(stack)
        except Exception as e:
            # removeLegs(start_leg)
            start_legs.drop(0, axis=0, inplace=True)
            start_legs.reset_index(drop=True, inplace=True)
            # print(f"Error occured = {e}")
            return False
    return wrapper

# ALGORITHM
@exception_handler
def generateTrip(stack):
    # Making the break flag False initially 
    # SHOULD BE CONSIDERED GLOBALLY 
    IS_BREAK = False
    spread_over = 0
    
    while len(stack) > 0 : 
        temp_set = generateTempSet(stack[-1]['current_leg'])
        if temp_set.empty :
            # EXCEPTION CASES CAN BE HANDLED HERE , MEANS WE CAN CHECK WHETHER THE 
            # STACK GETS EMPTY ON BACKTRACKING TO AVOID OUT OF BOUND 
            backtrack(stack)
            # After backtracking a new leg is replaced on the top , so we can just continue
            continue
        
        if (stack[-1]['current_leg'])['Duty'] > MIN_LIMIT_DUTY and stack[-1]["break"] == False:
            # display(stack[-1])
            temp_set = generateTempSet(stack[-1]['current_leg'], 1)
            # temp_set.reset_index(drop=True, inplace=True)
            # print("TempSet is below ")
            # display(temp_set)
            stack.append({"current_leg": temp_set.iloc[0], "temp_set": popTempSet(temp_set), "break": True})
            spread_over = (stack[-1]['current_leg'])['Arrival Time'] - (stack[0]['current_leg'])['Departure Time']
        else:
            # In the below line , break is made to follow the stack top because after setting it true inside the 
            # break insertion logic , the subsequent legs should have break True . So it should follow stack top  
            stack.append({"current_leg": temp_set.iloc[0], "temp_set": popTempSet(temp_set), "break": stack[-1]["break"]})
            spread_over = (stack[-1]['current_leg'])['Arrival Time'] - (stack[0]['current_leg'])['Departure Time']
        if (stack[-1]['current_leg'])['Duty'] > MAX_DUTY or spread_over > MAX_SPREAD_OVER \
            or ((stack[-1]['current_leg'])['Duty'] > BREAK_LIMIT_DUTY and stack[-1]["break"] == False) :
            backtrack(stack)
        else:
            if (top_leg:=stack[-1]['current_leg'])['Arrival Place']==START_PLACE and top_leg['Duty'] > MIN_DUTY \
            and stack[-1]["break"]==True: 
                # break
                return stack

## MAIN PART
def main(file_path):
    global df, start_legs
    # Initializations
    df = pd.read_excel(file_path).reset_index(drop=True) 
    df['Terminal Gap'] = [0] * len(df)
    df['Duty'] = [0] * len(df)
    start_legs = df[df['Departure Place'] == START_PLACE].sort_values('Departure Time', ascending=True)
    start_legs.reset_index(drop=True,inplace=True)
    # setting the initial running time of start legs as its running time itself
    start_legs['Duty'] = start_legs['Running Time']  
    trips_json = []  # List to store JSON representations of each trip
    trip_number = 1  # Initialize trip number
    if not start_legs.empty:
        while not start_legs.empty:
            status = generateTrip([{"current_leg": start_legs.iloc[0], "temp_set": pd.DataFrame(), "break": False}])
            if status:
                result = displayTrip(status)
                removeLegs(result[0])
                # Append JSON representation of trip to the list
                trip_dict = result[0].to_dict(orient='records')
                trips_json.append({
                    "trip_number": trip_number,  # Include trip number in JSON
                    "trip": trip_dict,
                    "steering_duty": str(result[1]),  # Convert steering duty to string for JSON serialization
                    "spread_over": str(result[2])      # Convert spread over to string for JSON serialization
                })
                trip_number += 1  # Increment trip number
            else:
                continue
    # Construct the return value containing trip details
    return json.dumps({
        "success_legs": success,
        "missing_routes": 104 - success,
        "number_of_trips": trips_count,
        "trips_details": trips_json
    }, indent=4)


result = main('dataset/processed/psl.xlsx')
print(result)

