import pandas as pd
import numpy as np
from datetime import datetime, timedelta, time


# Define column mappings
COLUMN_MAP = {
    "ADR": [
        "Date", "Time", "Open", "High", "Low", "Close", "Contract", "Session",
        "ADR_DR_High", "ADR_DR_Low", "ADR_IDR_High", "ADR_IDR_Low", "ADR_SD", "ADR_Open_Box",
        "ADR_Close_Box", "ADR_Box_Size", "ADR_Box_Color", "ADR_Confirmation_Time", "ADR_Direction"
    ],
    "ODR": [
        "Date", "Time", "Open", "High", "Low", "Close", "Contract", "Session",
        "ODR_DR_High", "ODR_DR_Low", "ODR_IDR_High", "ODR_IDR_Low", "ODR_SD", "ODR_Open_Box",
        "ODR_Close_Box", "ODR_Box_Size", "ODR_Box_Color", "ODR_Confirmation_Time", "ODR_Direction"
    ],
    "RDR": [
        "Date", "Time", "Open", "High", "Low", "Close", "Contract", "Session",
        "RDR_DR_High", "RDR_DR_Low", "RDR_IDR_High", "RDR_IDR_Low", "RDR_SD", "RDR_Open_Box",
        "RDR_Close_Box", "RDR_Box_Size", "RDR_Box_Color", "RDR_Confirmation_Time", "RDR_Direction"
    ]
}

# Ask the user for input
choice = input("Enter your choice (ADR, ODR, RDR): ").strip().upper()
if choice not in COLUMN_MAP:
    raise ValueError(f"Invalid choice: {choice}. Please select from ADR, ODR, or RDR.")

# Get the selected columns
selected_columns = COLUMN_MAP[choice]

# Provide the path to your data file
file_path = r"C:\Users\HP\Downloads\strategy_data All.csv"
data1 = pd.read_csv(file_path)

# Filter columns based on the user's choice
data1 = data1[selected_columns]
#print(data1)
# Sort and process data
data1 = data1.sort_values(by="Date", ascending=True)
data1 =data1.dropna().reset_index(drop=True)
data=data1.drop_duplicates(subset='Date')



#Parameters to adjust for backtesting
prefix = choice
stop_ticks=3
start_date = "2024-10-01"  # in format DD-MM-YYYY
end_date = "2024-12-31"
day = "all"
entry_after_confirmation_time='Yes'
fixed_entry_time=time(10,30)
stop_trading=time(14,30)
start_window=time(10,35)
end_window=time(11,30)
entry_time_limit=timedelta(minutes=60)

 # Convert fixed_entry_time to a full datetime object
dummy_date = datetime(1900, 1, 1)  # Use any dummy date
fixed_entry_datetime = datetime.combine(dummy_date, fixed_entry_time)
entry_time_adjusted = fixed_entry_datetime - pd.Timedelta(minutes=5)
# Extract the time component
entry_time_adjusted = entry_time_adjusted.time()
#filter data
data1= data1[(data1['Date'] >= start_date) & (data1['Date'] <= end_date)]

data = data[(data['Date'] >= start_date) & (data['Date'] <= end_date)]
if day != 'all':
        day_map = {'mo': 0, 'tu': 1, 'we': 2, 'th': 3, 'fr': 4}
        data = data[data['Date'].dt.weekday == day_map[day]]

if day != 'all':
        day_map = {'mo': 0, 'tu': 1, 'we': 2, 'th': 3, 'fr': 4}
        data1 = data1[data1['Date'].dt.weekday == day_map[day]]
        
data = data.sort_values(by="Date", ascending=True)

print(data)

# configurations
CONFIGS = {														
	1: {'entry_type': 'DR', 'stop_type': 'SD', 'stop_cluster':-0.1, 'stop_adjust': 3, 'target':1.1, 'break_even':0},													
	2: {'entry_type': 'IDR', 'stop_type': 'SD', 'stop_cluster': 0.1, 'stop_adjust': 3, 'target':1.1, 'break_even':0},													
	3: {'entry_type': 'IDR', 'entry_cluster': 0.0 , 'stop_type': 'SD', 'stop_cluster':-0.3, 'stop_adjust': 3, 'target':1, 'break_even':2,'confirm_direction': 'Short'},													
	4: {'entry_type': 'custom', 'entry_cluster': -0.1 , 'stop_type': 'SD', 'stop_cluster':-0.2, 'stop_adjust': 0, 'target':1.1, 'break_even':0},													
	5: {'entry_type': 'custom', 'entry_cluster': -0.1 , 'stop_type': '25', 'stop_cluster':-0.2, 'stop_adjust': 0, 'target':1.1, 'break_even':0}													

}


# Provide the path to your data file
#file_path = r"C:\Users\HP\Documents\strategy_dataset.csv"

#data1 = pd.read_csv(file_path)
#data1 = data1.sort_values(by='Date', ascending=True)
#data=data1.drop_duplicates(subset='Date')
#print(data)
#print(data1)

# Assuming you're working with configuration ID 3
CONFIG= CONFIGS[3]  # You can change this to dynamically select the config if needed
def calculate_trading_strategy(stats,prefix):
    # Access the standard deviation from stats
    sd = stats[f"{prefix}_SD"]  # Use 'SD' from the column names
    
    # Initialize variables
    entry_level = None
    stop_level = None
    stop_offset = None
    entry_offset = None
    box_offset = None
    stop_boxplace=0
    
    direction = stats[f"{prefix}_Direction"]
    date=stats['Date']
    # Determine entry level and stop level based on entry type
    if CONFIG['entry_type'] == 'IDR':
        entry_offset=CONFIG['entry_cluster']*sd*10
        entry_level = round((stats[f"{prefix}_IDR_High"]+entry_offset),2) if stats[f"{prefix}_Direction"] == 'Long' else round((stats[f"{prefix}_IDR_Low"]-entry_offset),2)            
        stop_offset = CONFIG['stop_cluster'] * sd * 10
        stop_level = round((stats[f"{prefix}_IDR_High"] + stop_offset),2) if stats[f"{prefix}_Direction"] == 'Long' else round((stats[f"{prefix}_IDR_Low"] - stop_offset),2)
        stop_place=stop_level-(stop_ticks/100) if stats[f"{prefix}_Direction"]=='Long' else stop_level+(stop_ticks/100)
        box_offset=round(((stats[f"{prefix}_Close_Box"]-stats[f"{prefix}_Open_Box"])*0.25),2) if stats[f"{prefix}_Box_Color"]=='Green' else round(((stats[f"{prefix}_Open_Box"]-stats[f"{prefix}_Close_Box"])*0.25),2)
        target_offset=sd*CONFIG['target']*10
        target_level=round((stats[f"{prefix}_IDR_High"]+target_offset),2) if stats[f"{prefix}_Direction"]=='Long' else stats[f"{prefix}_IDR_Low"]-target_offset
        
        if stats[f"{prefix}_Direction"] == 'Short':
            if stats[f"{prefix}_Box_Color"] == 'Red':
                stop_boxplace = round((stats[f"{prefix}_Close_Box"] + box_offset), 2)
            else:
                stop_boxplace = round((stats[f"{prefix}_Open_Box"] + box_offset), 2)
        elif stats[f"{prefix}_Direction"] == 'Long':
            if stats[f"{prefix}_Box_Color"] == 'Red':
                stop_boxplace = round((stats[f"{prefix}_Open_Box"] - box_offset), 2)
            else:
                stop_boxplace = round((stats[f"{prefix}_Close_Box"] - box_offset), 2)
        

    elif CONFIG['entry_type'] == 'DR':
        entry_offset=CONFIG['entry_cluster']*sd*10
        entry_level = round((stats[f"{prefix}_DR_High"]+entry_offset),2) if stats[f"{prefix}_Direction"] == 'Long' else round((stats[f"{prefix}_DR_Low"]-entry_offset),2)
        stop_offset = CONFIG['stop_cluster'] * sd * 10
        stop_level = round((stats[f"{prefix}_DR_High"] + stop_offset),2) if stats[f"{prefix}_Direction"] == 'Long' else round((stats[f"{prefix}_DR_Low"] - stop_offset),2)
        stop_place=stop_level-(stop_ticks/100) if stats[f"{prefix}_Direction"]=='Long' else stop_level+(stop_ticks/100)
        box_offset=abs(round(((stats[f"{prefix}_Close_Box"]-stats[f"{prefix}_Open_Box"])*0.25),2))
        target_offset=sd*CONFIG['target']*10
        target_level=round((stats[f"{prefix}_DR_High"]+target_offset),2) if stats[f"{prefix}_Direction"]=='Long' else stats[f"{prefix}_DR_Low"]-target_offset
        if stats[f"{prefix}_Direction"] == 'Short':
            if stats[f"{prefix}_Box_Color"] == 'Red':
                stop_boxplace = round((stats[f"{prefix}_Close_Box"] + box_offset), 2)
            else:
                stop_boxplace = round((stats[f"{prefix}_Open_Box"] + box_offset), 2)
        elif stats[f"{prefix}_Direction"] == 'Long':
            if stats[f"{prefix}_Box_Color"] == 'Red':
                stop_boxplace = round((stats[f"{prefix}_Open_Box"] - box_offset), 2)
            else:
                stop_boxplace = round((stats[f"{prefix}_Close_Box"] - box_offset), 2)
        
    elif CONFIG['entry_type'] == 'custom':
        if CONFIG['stop_type'] == 'SD':
            entry_offset = CONFIG['entry_cluster'] * sd * 10
            entry_level = round((stats[f"{prefix}_IDR_High"]+entry_offset),2) if stats[f"{prefix}_Direction"] == 'Long' else round((stats[f"{prefix}_IDR_Low"]-entry_offset),2)
            stop_offset = CONFIG['stop_cluster'] * sd * 10
            stop_level = round((stats[f"{prefix}_IDR_High"] + stop_offset),2) if stats[f"{prefix}_Direction"] == 'Long' else round((stats[f"{prefix}_IDR_Low"] - stop_offset),2)
            stop_place=stop_level-(stop_ticks/100) if stats[f"{prefix}_Direction"]=='Long' else stop_level+(stop_ticks/100)
            box_offset=abs(round(((stats[f"{prefix}_Close_Box"]-stats[f"{prefix}_Open_Box"])*0.25),2))
            target_offset=sd*CONFIG['target']*10
            target_level=round((stats[f"{prefix}_IDR_High"]+target_offset),2) if stats[f"{prefix}_Direction"]=='Long' else stats[f"{prefix}_IDR_Low"]-target_offset
            if stats[f"{prefix}_Direction"] == 'Short':
                if stats[f"{prefix}_Box_Color"] == 'Red':
                    stop_boxplace = round((stats[f"{prefix}_Close_Box"] + box_offset), 2)
                else:
                    stop_boxplace = round((stats[f"{prefix}_Open_Box"] + box_offset), 2)
            elif stats[f"{prefix}_Direction"] == 'Long':
                if stats[f"{prefix}_Box_Color"] == 'Red':
                    stop_boxplace = round((stats[f"{prefix}_Open_Box"] - box_offset), 2)
                else:
                    stop_boxplace = round((stats[f"{prefix}_Close_Box"] - box_offset), 2)
        
        elif CONFIG['stop_type'] in ['25', '50', '75']:
            entry_offset = CONFIG['entry_cluster'] * sd * 10
            entry_level = round((stats[f"{prefix}_IDR_High"]+entry_offset),2) if stats[f"{prefix}_Direction"] == 'Long' else round((stats[f"{prefix}_IDR_Low"]-entry_offset),2)
            stop_offset = CONFIG['stop_cluster'] * sd * 10
            stop_level = round((stats[f"{prefix}_IDR_High"] + stop_offset),2) if stats[f"{prefix}_Direction"] == 'Long' else round((stats[f"{prefix}_IDR_Low"] - stop_offset),2)
            stop_place=stop_level-(stop_ticks/100) if stats[f"{prefix}_Direction"]=='Long' else stop_level+(stop_ticks/100)
            box_offset=abs(round(((stats[f"{prefix}_Close_Box"]-stats[f"{prefix}_Open_Box"])*0.25),2))
            target_offset=sd*CONFIG['target']*10
            target_level=round((stats[f"{prefix}_IDR_High"]+target_offset),2) if stats[f"{prefix}_Direction"]=='Long' else stats[f"{prefix}_IDR_Low"]-target_offset
            if stats[f"{prefix}_Direction"] == 'Short':
                if stats[f"{prefix}_Box_Color"] == 'Red':
                    stop_boxplace = round((stats[f"{prefix}_Close_Box"] + box_offset), 2)
                else:
                    stop_boxplace = round((stats[f"{prefix}_Open_Box"] + box_offset), 2)
            elif stats[f"{prefix}_Direction"] == 'Long':
                if stats[f"{prefix}_Box_Color"] == 'Red':
                    stop_boxplace = round((stats[f"{prefix}_Open_Box"] - box_offset), 2)
                else:
                    stop_boxplace = round((stats[f"{prefix}_Close_Box"] - box_offset), 2)
        else:
            raise ValueError("Invalid stop_type in CONFIG")

    # Return the calculated values
    return {
        'entry_offset': entry_offset,
        'entry_level': entry_level,
        'stop_offset':stop_offset,
        'stop_level': stop_level,
        'stop_place': stop_place,
        'box_offset': box_offset,
        'stop_boxplace': stop_boxplace,
        'target_offset': target_offset,
        'target_level': target_level,
        'direction': direction,
        'date':date

    }
def calculate_entry_level_new(df):
    df["Time"] = pd.to_datetime(df["Time"], format="%H:%M:%S").dt.time
    df = df.sort_values(by="Time", ascending=True)
    #print(df)  
    # Filter the data to find rows matching the adjusted time
    entry_level_new = df[df['Time'] == entry_time_adjusted]['Close']
    #print(entry_level_new)
    
    return entry_level_new

    
    
    
    
    
def classify_hit(day_df, res_df, confirmation_time,prefix):
    # Initialize default values
    Hit_entry_cluster = "No"
    Stopped_out = "No"
    Reached_target = "No"
    Break_even = "No"
    
    Direction=res_df['direction']
    
    if entry_after_confirmation_time == 'Yes':
        # Filter data to start from confirmation time
        day_df = day_df[(day_df['Time'] > confirmation_time) & (day_df['Time'] <= stop_trading)]
        day_df = day_df.sort_values(by='Time')
        #print(confirmation_time)
        # Ensure time is in the correct range
        time_window = (day_df['Time'] >= start_window) & (day_df['Time'] <= end_window)
        df = day_df[time_window]
        #print(day_df)

        # For 'Short' direction
        if CONFIG['confirm_direction'] == 'Short':
            # pick the data having direction short
            day_df = day_df[day_df[f"{prefix}_Direction"] == "Short"]
            df = df[df[f"{prefix}_Direction"] == "Short"]
            # Case: Entry Level is Triggered
            if not df.empty:  
                if (min(df['Low']) > res_df['entry_level']) or (max(df['High']) < res_df['entry_level']):
                    Hit_entry_cluster = "No"
                elif ((df['Low'] <= res_df['entry_level']) | (df['High'] >= res_df['entry_level'])).any():
                    Hit_entry_cluster = "Hit"
                    if ((df['Low'] <= res_df['entry_level']) & (df['High'] >= res_df['stop_level'])).any(): #entry_level and stop_level hit by same candle 
                        Stopped_out = "Hit"
                        R=-1
                        Break_even = "No"
                        #R=round((res_df['entry_level']-res_df['target_level'])/(res_df['stop_level']-res_df['entry_level']))
                    else:
                        entry_row = df[((df['Low'] <= res_df['entry_level']) | (df['High'] >= res_df['entry_level']))].iloc[0]
                        # Check what happens after entry
                        post_entry_df = day_df[day_df['Time'] >= entry_row['Time']]
                        #print(post_entry_df)
                        #print(res_df['entry_level'])
                        # Determine which level is hit first
                        for _, row in post_entry_df.iterrows():
                            #print(row)
                            high = row['High']
                            low = row['Low']
                            #print(low,high)
                            if low <= res_df['target_level']:
                                Reached_target = "Hit"
                                #R=round((res_df['entry_level']-res_df['target_level'])/(res_df['stop_level']-res_df['entry_level']),2)
                                break
                            elif high >= res_df['stop_level']:
                                R=round((res_df['entry_level']-res_df['target_level'])/(res_df['stop_level']-res_df['entry_level']),2)
                                if R>=CONFIG['break_even']:
                                    Break_even="Yes"
                                    Stopped_out = "No"
                                else:
                                    Stopped_out = "Hit"
                                break
                                #print(res_df)
                                #print(post_entry_df['Date'])
                                #print(R)
                                
                        # when neither the target level nor the stop level is triggered 
                        if Reached_target == "No" and Stopped_out == "No":
                            profit_price=day_df[day_df['Time'] == stop_trading]['Open']
                            R=round((res_df['entry_level']-profit_price)/(res_df['stop_level']-res_df['entry_level']),2)
                            if (R<0).all():
                                if Break_even=="Yes":
                                    Stopped_out = "No"
                                else:
                                    Stopped_out = "Hit"
                            elif (R>=1).all():
                                Reached_target = "Hit"
                            elif (R>=0).all() & (R<1).all():
                                Break_even="Yes"
                else:
                    # Case: Entry Level is not Triggered
                    Hit_entry_cluster = "No"
            # for 'long direction
        elif CONFIG['confirm_direction'] == 'Long':
            # pick the data having direction long
            day_df = day_df[day_df[f"{prefix}_Direction"] == "Long"]
            df = df[df[f"{prefix}_Direction"] == "Long"]
            # Case: Entry Level is Triggered
            if not df.empty:   
                if (min(df['Low']) > res_df['entry_level']) or (max(df['High']) < res_df['entry_level']):
                    Hit_entry_cluster = "No"
                elif ((df['Low'] <= res_df['entry_level']) | (df['High'] >= res_df['entry_level'])).any():
                    #print(df)
                    Hit_entry_cluster = "Hit"
                    if ((df['Low'] <= res_df['entry_level']) & (df['Low'] <= res_df['stop_place'])).any(): #entry_level and stop_level hit by same candle 
                        Stopped_out = "Hit"
                        print(Stopped_out)
                        R=-1
                        Break_even = "No"
                    else:
                        entry_row = df[((df['Low'] <= res_df['entry_level']) | (df['High'] >= res_df['entry_level']))].iloc[0]
                        # Check what happens after entry
                        post_entry_df = day_df[day_df['Time'] >= entry_row['Time']]
                        #print(post_entry_df)
                        for _, row in post_entry_df.iterrows():
                            high = row['High']
                            low = row['Low']
                            if low<=res_df['entry_level'] and low<=res_df['stop_place']:
                                R = round((res_df['target_level'] - res_df['entry_level']) /(res_df['entry_level'] - res_df['stop_place']), 2)
                                if R >= CONFIG['break_even']:
                                    Break_even = "Yes"
                                    Stopped_out = "No"
                                else:
                                    Stopped_out = "Hit"
                                break
                            if high >= res_df['target_level']:
                                    Reached_target = "Hit"
                                    #calculate R's
                                    R = round((res_df['target_level'] - res_df['entry_level']) /(res_df['entry_level'] - res_df['stop_place']), 2)
                                    break
                            elif low <= res_df['stop_place']:
                                    R = round((res_df['target_level'] - res_df['entry_level']) /(res_df['entry_level'] - res_df['stop_place']), 2)
                                    if R>=CONFIG['break_even']:
                                        print(R)
                                        Break_even="Yes"
                                        Stopped_out = "No"
                                    else:
                                        Stopped_out = "Hit"
                                        print(Stopped_out)
                                    break   
                # when neither the target level nor the stop level is triggered 
                        if Reached_target == "No" and Stopped_out == "No":
                            profit_price=day_df[day_df['Time'] == stop_trading]['Open']
                            R = round((profit_price - res_df['entry_level']) /(res_df['entry_level'] - res_df['stop_level']),2)
                            if (R<0).all():
                                if Break_even=="Yes":
                                    Stopped_out = "No"
                                else:
                                    Stopped_out = "Hit"                                
                            elif (R>=1).all():
                                Reached_target = "Hit"
                            elif (R>=0).all() & (R<1).all():
                                Break_even="Yes"
                else:
                # Case: Entry Level is not Triggered
                    Hit_entry_cluster = "No"
    else:  # If entry_after_confirmation_time == 'No'
        Hit_entry_cluster="NA"
        day_df=day_df.sort_values(by="Time", ascending=True)
        day_df = day_df[(day_df['Time'] >= entry_time_adjusted) & (day_df['Time'] <= stop_trading)]
        
        if CONFIG['confirm_direction'] == 'Short':
            # pick the data having direction short
            day_df = day_df[day_df[f"{prefix}_Direction"] == "Short"]
            # Determine which level is hit first
            for _, row in day_df.iterrows():
                high = row['High']
                low = row['Low']
                
                if res_df['new_entry_level'] <= res_df['stop_place']:
                    Stopped_out = "No"
                    Reached_target = "No"
                    
                elif low <= res_df['target_level']:
                    Reached_target = "Hit"
                    #calculate R's
                    #R=round((res_df['entry_level']-res_df['target_level'])/(res_df['stop_level']-res_df['entry_level']),2)
                    break
                
                elif high >= res_df['stop_level']:
                    R=round((res_df['new_entry_level']-res_df['target_level'])/(res_df['stop_level']-res_df['new_entry_level']),2)
                    if R >= CONFIG['break_even']:
                        Break_even="Yes"
                        Stopped_out = "No"
                    else:
                        Stopped_out = "Hit"
                    break   
                    
                      
                    # when neither the target level nor the stop level is triggered 
        # if Reached_target == "No" and Stopped_out == "No":
                        #profit_price=day_df[day_df['Time'] == stop_trading]['Open']
                        #R=round((res_df['new_entry_level']-profit_price)/(res_df['stop_level']-res_df['new_entry_level']),2)
                        #if (R<0).all():
                        #    Stopped_out = "Hit"
                        #elif (R>=1).all():
                          #  Reached_target = "Hit"
                        #elif (R>=0).all() & (R<1).all():
                           # Break_even="Yes"        
        elif CONFIG['confirm_direction'] == 'Long':
            # pick the data having direction long
            day_df = day_df[day_df[f"{prefix}_Direction"] == "Long"]
            #print(day_df)
            for _, row in day_df.iterrows():
                        high = row['High']
                        low = row['Low']
                        
                        # Skip the trade if entry is below stop level
                        if res_df['new_entry_level'] <= res_df['stop_place']:
                            Stopped_out = "No"
                            Reached_target = "No"
                            
                        elif low <= res_df['stop_place']:
                            #print(low)
                            R=round((res_df['stop_place']-res_df['new_entry_level'])/(res_df['new_entry_level']-res_df['target_level']),2)
                            if R >= CONFIG['break_even']:
                                Break_even="Yes"
                                Stopped_out = "No"
                            else:
                                Stopped_out = "Hit"
                            break
                            
                        elif high >= res_df['target_level']:
                            #print(high)
                            Reached_target = "Hit"                            
                            break
                
            
                
    return {
        'Hit_entry_cluster': Hit_entry_cluster,
        'Stopped_out': Stopped_out,
        'Reached_target': Reached_target,
        'Break_even': Break_even,
        'Direction':Direction
    }


def calculate_win_amount_expected_value(res_df, res2_df):
    if entry_after_confirmation_time == 'Yes':
        # Calculate 'win' based on conditions
        if res2_df['Hit_entry_cluster'] == 'No':
            win = "No Trade"
        elif res2_df['Hit_entry_cluster'] == 'Hit' and res2_df['Reached_target'] == 'Hit':
            win = "Win"
        elif res2_df['Hit_entry_cluster'] == 'Hit' and res2_df['Stopped_out'] == 'Hit':
            win = "Expanse"
        else:
            win = "?"

        # Calculate 'Amount' based on conditions
        if win == "Win":
            amount = round(((res_df['target_level'] - res_df['entry_level']) / (res_df['entry_level'] -res_df['stop_place'])),2)
        elif win == "Expanse":
            amount = -1
        else:
            amount = 0

        # Calculate 'Expected Value' based on conditions
        if win == "No Trade":
            expected_value = 0
        else:
            expected_value = round(((res_df['target_level'] - res_df['entry_level']) / (res_df['entry_level'] -res_df['stop_place'])),2)
    else:
        if res2_df['Reached_target'] == 'Hit':
            win = "Win"
        elif res2_df['Stopped_out'] == 'Hit':
            win = "Expanse"
        else:
            win= "No Trade"
        
        if win == "Win":
            amount = round(((res_df['target_level'] - res_df['new_entry_level']) / (res_df['new_entry_level'] -res_df['stop_place'])),2)
        elif win == "Expanse":
            amount = -1
        else:
            amount = 0
        
        if win == "No Trade":
            expected_value = 0
        else:
            expected_value = round(((res_df['target_level'] - res_df['new_entry_level']) / (res_df['new_entry_level'] -res_df['stop_place'])),2)
            

    return win, amount, expected_value

def calculate_max_drawdown(values):
    values=np.array(values)
    # Convert list to numpy array for efficient computation					
    values = np.array(values)					
    					
    # Track the cumulative maximum values up to each point in time					
    peak = np.maximum.accumulate(values)					
    					
    # Calculate drawdowns as the drop from the peak to the current value					
    drawdowns = (peak - values) / peak							
    # Maximum drawdown is the largest drawdown percentage					
    max_drawdown = np.max(drawdowns) * 100 				
    return max_drawdown						

def performance_overview(res3_df): 
    total_trades = len(res3_df)
    win_count = len(res3_df[res3_df['Win'] == "Win"])
    expanse_count = len(res3_df[res3_df['Win'] == "Expanse"])
    no_trade_count = len(res3_df[res3_df['Win'] == "No Trade"])
    win_rate = round((win_count / total_trades) * 100, 2) if win_count != 0 else 0.0
    total_return=sum(res3_df["Amount of R's"])
    expectancy=round((total_return/total_trades),2)
    expected_value=sum(res3_df['Expected_Value'])
    max_drawdown = calculate_max_drawdown(portfolio_values)
    
    
    
    performance = {
        "Trades": total_trades,
        "Win": win_count,
        "Expanse": expanse_count,
        "No trade" :no_trade_count,
        "Win Rate": win_rate,  
        "Expectancy": expectancy,  
        "Total Return in R's": total_return,
        "Expectancy": expectancy,
        "Expected Value": expected_value,  
        "Max Drawdown": f"{max_drawdown:.2f}%" 
    }
    
    return performance
'''
def calculate_box_colors(stat_df, res3_df,prefix):
    counters = {
        'Win_Green_Long': 0,
        'Win_Green_Short': 0,
        'Win_Red_Long': 0,
        'Win_Red_Short': 0,
        'Expanse_Green_Long': 0,
        'Expanse_Green_Short': 0,
        'Expanse_Red_Long': 0,
        'Expanse_Red_Short': 0
    }
    
    for (index, row), (_, res_row) in zip(stat_df.iterrows(), res3_df.iterrows()):
        result = res_row['Win']  # 'Win' or 'Expanses' from result3
        color = row[f"{prefix}_Box_Color"]  # 'Green' or 'Red' from stat_df
        direction = row[f"{prefix}_Direction"]  # 'Long' or 'Short' from stat_df

        key = f"{result}_{color}_{direction}"
        
        if key in counters:
            counters[key] += 1

    # Calculate percentages
    total_entries = sum(counters.values())
    for key in counters:
        counters[key] = (counters[key], round((counters[key] / total_entries) * 100, 2) if total_entries > 0 else 0.0)

    return counters

def format_output(counters):
    # Preparing the formatted table
    categories = ['Win', 'Expanse']
    directions = ['Long', 'Short']
    colors = ['Green', 'Red']
    
    print(f"{'':<15}{'Green':<15}{'Red':<15}")
    
    for category in categories:
        for direction in directions:
            green_key = f"{category}_Green_{direction}"
            red_key = f"{category}_Red_{direction}"
            
            green_value, green_percent = counters.get(green_key, (0, 0.0))
            red_value, red_percent = counters.get(red_key, (0, 0.0))
            
            print(f"{category} {direction:<8}{green_value} ({green_percent}%)   {red_value} ({red_percent}%)")

'''
portfolio_values = [100000 ,120000 ,90000,95000 ,130000, 80000, 150000]

# Initialize results lists
results1 = []
results2 = []
results3 = []

import pandas as pd

# Assuming data1 is your DataFrame
date_groups = list(data1.groupby('Date'))

group_data = []
entry_level_new = []
new_entry_level = []

for date, group in date_groups:
    # Convert the 'Time' column to datetime and then to time
    group["Time"] = pd.to_datetime(group["Time"], format="%H:%M:%S").dt.time
    group_data.append(group)
    entry_level_new = calculate_entry_level_new(group)
    new_entry_level.append(entry_level_new)



for index, row in data.iterrows():
    calculations = calculate_trading_strategy(row,prefix)
    # Append calculations to results1
    results1.append(calculations)
if entry_after_confirmation_time=="Yes":
    result1_df = pd.DataFrame(results1)
else:
    result1_df=pd.DataFrame(results1, columns=["entry_offset","stop_offset","stop_level","stop_place","box_offset","stop_boxplace","target_offset","target_level","direction"])
    result1_df = result1_df.reset_index(drop=True)
    new_entry_level = pd.concat(new_entry_level, ignore_index=True)
    result1_df["new_entry_level"] = new_entry_level
    




result2 = []
group_data_list = []
for (index, row), (date, group) in zip(result1_df.iterrows(), date_groups):
    # Convert 'Time' column to datetime
    group['Time'] = pd.to_datetime(group['Time'], format='%H:%M:%S').dt.time

    # Append the group to list
    group_data_list.append(group)

    # Extract confirmation time
    confirmation_time = pd.to_datetime(group[f"{prefix}_Confirmation_Time"].iloc[0]).time()

    # Classify the hit
    classification = classify_hit(group, row, confirmation_time, prefix)
    
    # Append classification results
    result2.append(classification)
all_groups_data = pd.concat(group_data_list, ignore_index=True)

# Save to CSV
all_groups_data.to_csv('grouped_data.csv', index=False)
if CONFIG['confirm_direction'] == 'Short':
    result2_df = pd.DataFrame(result2, columns=["Hit_entry_cluster", "Stopped_out", "Reached_target", "Break_even","Direction"])
    result2_df = result2_df[result2_df['Direction'] == "Short"]
elif CONFIG['confirm_direction'] == 'Long':
    result2_df = pd.DataFrame(result2, columns=["Hit_entry_cluster", "Stopped_out", "Reached_target", "Break_even","Direction"])
    result2_df = result2_df[result2_df['Direction'] == "Long"]

if CONFIG['confirm_direction'] == 'Short':
    result1_df=result1_df[result1_df['direction']=="Short"]
    for index, (res_row, res2_row) in enumerate(zip(result1_df.iterrows(), result2_df.iterrows())):
        # Calculate win, amount, and expected value using res_row and Hits results
        win_metrics = calculate_win_amount_expected_value(res_row[1], res2_row[1])
        # Append the win, amount, and expected value to results3
        results3.append(win_metrics)
elif CONFIG['confirm_direction'] == 'Long':
    result1_df=result1_df[result1_df['direction']=="Long"]
    for index, (res_row, res2_row) in enumerate(zip(result1_df.iterrows(), result2_df.iterrows())):
        # Calculate win, amount, and expected value using res_row and Hits results
        win_metrics = calculate_win_amount_expected_value(res_row[1], res2_row[1])
        # Append the win, amount, and expected value to results3
        results3.append(win_metrics)
    

results3_df = pd.DataFrame(results3, columns=["Win", "Amount of R's", "Expected_Value"])
performance=performance_overview(results3_df)
#Box_color_result = calculate_box_colors(data, results3_df,prefix)



# Define the bins for Box Size categorization
box_size_bins = [
    (-1.31, float("-inf"), "< -1.31"),
    (-1.30, -1.21, "-1.21 / -1.30"),
    (-1.20, -1.11, "-1.11 / -1.20"),
    (-1.10, -1.01, "-1.01 / -1.10"),
    (-1.00, -0.91, "-0.91 / -1.00"),
    (-0.90, -0.81, "-0.81 / -0.90"),
    (-0.80, -0.71, "-0.71 / -0.80"),
    (-0.70, -0.61, "-0.61 / -0.70"),
    (-0.60, -0.51, "-0.51 / -0.60"),
    (-0.50, -0.41, "-0.41 / -0.50"),
    (-0.40, -0.31, "-0.31 / -0.40"),
    (-0.30, -0.21, "-0.21 / -0.30"),
    (-0.20, -0.11, "-0.11 / -0.20"),
    (-0.10, -0.01, "-0.01 / -0.10"),
    (0.0, 0.09, "0.0 / 0.09"),
    (0.1, 0.19, "0.1 / 0.19"),
    (0.2, 0.29, "0.2 / 0.29"),
    (0.3, 0.39, "0.3 / 0.39"),
    (0.4, 0.49, "0.4 / 0.49"),
    (0.5, 0.59, "0.5 / 0.59"),
    (0.6, 0.69, "0.6 / 0.69"),
    (0.7, 0.79, "0.7 / 0.79"),
    (0.8, 0.89, "0.8 / 0.89"),
    (0.9, 0.99, "0.9 / 0.99"),
    (1.0, 1.09, "1.0 / 1.09"),
    (1.1, 1.19, "1.1 / 1.19"),
    (1.2, 1.29, "1.2 / 1.29"),
    (1.3, float("inf"), "> 1.30")
]
# Initialize counters
counts = {bin_name: 0 for _, _, bin_name in box_size_bins}

    

box_size_metrics = {bin_name: {'Trades': 0, 'Win Rate': 0.0, 'Winners': 0, 'Expenses': 0, 'Break Even': 0, 'Result': 0}
                    for _, _, bin_name in box_size_bins}

# Function to update box size metrics
def update_box_size_metrics(stat_df, res3_df,res2_df,prefix):
    # Reset the index of both dataframes to align them by position
    res3_df.reset_index(drop=True, inplace=True)
    res2_df.reset_index(drop=True, inplace=True)
    if CONFIG['confirm_direction'] == 'Short':
        direc=f"{prefix}_Direction"
        stat_df=stat_df[stat_df[direc]=="Short"]
        stat_df.reset_index(drop=True, inplace=True)
        

        # Iterate over the rows in stat_df
        for index, row in stat_df.iterrows():
            Box = f"{prefix}_Box_Size"
            box_size = row[Box]
            metrics = None
            for lower, upper, bin_name in box_size_bins:
                if lower <= box_size <= upper:
                    metrics = box_size_metrics[bin_name]
                    break
            if metrics:
                metrics['Trades'] += 1
                # Get the result from res3_df: 'Win', 'Expanse', or 'No Trade'
                result = res3_df.loc[index, 'Win']  # 'Win' or 'Expanse'
                result2=res2_df.loc[index,'Break_even']
                result3=res3_df.loc[index,"Amount of R's"]
                # Update metrics based on the result type (Win or Expanse)
                if result == 'Win':
                    metrics['Winners'] += 1
                    metrics['Result']+=result3
                elif result == 'Expanse':
                    metrics['Expenses'] += 1
                    metrics['Result']+=result3
                if result2=='Yes':
                    metrics['Break Even']+=1
                
            
                # Calculate Win Rate (Winners / Trades * 100)
                if metrics['Trades'] > 0:
                    metrics['Win Rate'] = round((metrics['Winners'] / metrics['Trades']) * 100, 2)
                else:
                    metrics['Win Rate'] = 0.0
                
            #Result need to define result
    if CONFIG['confirm_direction'] == 'Long':
        direc=f"{prefix}_Direction"
        stat_df=stat_df[stat_df[direc]=="Long"]
        stat_df.reset_index(drop=True, inplace=True)
        

        # Iterate over the rows in stat_df
        for index, row in stat_df.iterrows():
            Box = f"{prefix}_Box_Size"
            box_size = row[Box]
            metrics = None
            for lower, upper, bin_name in box_size_bins:
                if lower <= box_size <= upper:
                    metrics = box_size_metrics[bin_name]
                    break
            if metrics:
                metrics['Trades'] += 1
                # Get the result from res3_df: 'Win', 'Expanse', or 'No Trade'
                result = res3_df.loc[index, 'Win']  # 'Win' or 'Expanse'
                result2=res2_df.loc[index,'Break_even']
                result3=res3_df.loc[index,"Amount of R's"]
                # Update metrics based on the result type (Win or Expanse)
                if result == 'Win':
                    metrics['Winners'] += 1
                    metrics['Result']+=result3
                elif result == 'Expanse':
                    metrics['Expenses'] += 1
                    metrics['Result']+=result3
                if result2=='Yes':
                    metrics['Break Even']+=1
                
            
                # Calculate Win Rate (Winners / Trades * 100)
                if metrics['Trades'] > 0:
                    metrics['Win Rate'] = round((metrics['Winners'] / metrics['Trades']) * 100, 2)
                else:
                    metrics['Win Rate'] = 0.0

# Ensure that box_size_metrics is populated
update_box_size_metrics(data, results3_df,result2_df,prefix)

# Display the final box_size_metrics_df DataFrame
box_size_metrics_df = pd.DataFrame.from_dict(box_size_metrics, orient='index')

# Reset index to include bin names as a column
box_size_metrics_df.reset_index(inplace=True)
box_size_metrics_df.rename(columns={'index': 'Box Size Bin'}, inplace=True)


bins = [
    ('Box size > -0.51', box_size_metrics_df['Box Size Bin'].str.contains('-0.51 / -0.60|-0.61 / -0.70|-0.71 / -0.80|-0.81 / -0.90|-0.91 / -1.00|-1.01 / -1.10|-1.11 / -1.20|-1.21 / -1.30|< -1.31')),
    ('Box size -0.01 < -0.5', box_size_metrics_df['Box Size Bin'].str.contains('-0.01 / -0.10|-0.11 / -0.20|-0.21 / -0.30|-0.31 / -0.40|-0.41 / -0.50')),
    ('Box size 0.0 < 0.49', box_size_metrics_df['Box Size Bin'].str.contains('0.0 / 0.09|0.1 / 0.19|0.2 / 0.29|0.3 / 0.39|0.4 / 0.49')),
    ('Box size > 0.5 ', box_size_metrics_df['Box Size Bin'].str.contains('0.5 / 0.59|0.6 / 0.69|0.7 / 0.79|0.8 / 0.89|0.9 / 0.99|1.0 / 1.09|1.1 / 1.19|1.2 / 1.29|> 1.30'))
]

# Apply filters to define Box Size Range
box_size_metrics_df['Box Size Range'] = ''
for label, condition in bins:
    box_size_metrics_df.loc[condition, 'Box Size Range'] = label

# Sort by 'Box Size Range' to ensure negative bins come first
box_size_metrics_df['Box Size Range'] = pd.Categorical(box_size_metrics_df['Box Size Range'], 
                                                       categories=[ 'Box size -0.01 < -0.5', 'Box size > -0.51',
                                                                   'Box size 0.0 < 0.49', 'Box size > 0.5 '], 
                                                       ordered=True)

# Summarize the data by 'Box Size Range'
summary_df = box_size_metrics_df.groupby('Box Size Range', observed=False).agg(
    Trades=('Trades', 'sum'),
    Win_Rate=('Winners', lambda x: f"{(x.sum() / box_size_metrics_df.loc[x.index, 'Trades'].sum()) * 100:.0f}%" if x.sum() > 0 else "0%"),
    Winners=('Winners', 'sum'),
    Expenses=('Expenses', 'sum'),
    Break_Even=('Break Even', 'sum'),
    Result=('Result', 'sum')
).reset_index()

# Print results
print('\nCalculations from Trading Strategy:')

print(result1_df)
# Save to CSV
result1_df.to_csv('trading_strategy_results.csv', index=False)

print('\nHits Classification:')
print(result2_df)
result2_df.to_csv('Hits Classification.csv', index=False)
print("\n Amount of R's :")
print(results3_df)
results3_df.to_csv('Amounts.csv', index=False)
print('\n Strategy analyse Report')
print(performance)
#print('\n Box Color:')
#print(format_output(Box_color_result))
print(box_size_metrics_df)
# Print the summarized Box_size_matrices DataFrame
print("Summary DataFrame:")
print(summary_df)
