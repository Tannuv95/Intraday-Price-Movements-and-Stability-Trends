import pandas as pd
from datetime import datetime, timedelta, time


# Parameters to adjust for backtesting
#start_date = "01-11-2024"  # in format DD-MM-YYYY
#end_date = "31-12-2024"
start_date = "2024-10-01"  # in format DD-MM-YYYY
end_date = "2024-12-31"
day = "all"  # 'all', 'mo', 'tu', 'we', 'th', 'fr'
time_difference = 1
start_time = time(9, 30)  # = NYT9:30
end_time = time(10, 25)   # = NYT10:25
start_for_confirmation = time(10, 30) # NYT10:30
entry_after_confirmation = "Yes"  # "Yes" or "No"
fixed_entry_time = time(10, 0)  # NYT10:00
session_close = time(15, 55) # NYT15:55
extension_target = 1.0
break_even = 2 
stop_trading = time(13, 0) # NYT13:00
tick_size = 0.25
entry_time_limit = timedelta(minutes=60)
strategy_end_time=time(16,10)
file_type='txt' #specify file tipe here
#file_path = r"C:\Users\bospa\Downloads\CL 25-7 tot 23-8.csv" #replace with your file path
file_path = r"C:\Users\HP\Downloads\data_iso.csv"

# PHASE I: Load and Filter Data
def filter_data(data):
    # Parse the date column and filter between start_date and end_date
    data['Date'] = pd.to_datetime(data['Date'])
    new_data = data[(data['Date'] >= start_date) & (data['Date'] <= end_date)]

    # Filter for specified day of the week if not 'all'
    if day != 'all':
        day_map = {'mo': 0, 'tu': 1, 'we': 2, 'th': 3, 'fr': 4}
        new_data = new_data[new_data['Date'].dt.weekday == day_map[day]]

    # Filter data within the session time range
    session_data = new_data[(new_data['Time'] >= start_time) & (new_data['Time'] <= session_close)]

    return session_data

# Calculate DR/IDR Framework
def calculate_dr_idr(filtered_data):
    dr_idr = []
    grouped_data = filtered_data.groupby('Date')
    
    for date, group in grouped_data:
        dr_data = group[(group['Time'] >= start_time) & (group['Time'] <= end_time)]
        DR_High = dr_data['High'].max()
        DR_Low = dr_data['Low'].min()
        IDR_High = dr_data['Close'].max()
        IDR_Low = dr_data['Close'].min()
        dr_idr.append((date, DR_High, DR_Low, IDR_High, IDR_Low))
        
    return pd.DataFrame(dr_idr, columns=['Date', 'DR_High', 'DR_Low', 'IDR_High', 'IDR_Low'])

def confirmation(data, dr_idr):
    confirmation_results = []
    
    for _, row in dr_idr.iterrows():
        daily_data = data[data['Date'] == row['Date']]
        confirm_data = daily_data[(daily_data['Time'] >= start_for_confirmation) & (daily_data['Time'] <= session_close)]
        confirmation_time = None
        direction = None
        
        for _, confirm_row in confirm_data.iterrows():
            if entry_after_confirmation == "Yes" and confirm_row['Time'] <= stop_trading:
                if confirm_row['Close'] > row['DR_High']:
                    confirmation_time = confirm_row['Time']
                    direction = "Long"
                    break
                elif confirm_row['Close'] < row['DR_Low']:
                    confirmation_time = confirm_row['Time']
                    direction = "Short"
                    break
            
        if entry_after_confirmation == "No":
            confirmation_time = fixed_entry_time
        
        confirmation_results.append((row['Date'], confirmation_time, direction))
    confirmation_df =pd.DataFrame(confirmation_results, columns=['Date', 'Confirmation_Time', 'Direction'])
    time_counts = confirmation_df['Confirmation_Time'].value_counts().sort_index()
    time_percentages = (time_counts / time_counts.sum()) * 100
    summary = pd.DataFrame({
        'Count': time_counts,
        'Percentage': time_percentages.round(2)
    }).reset_index().rename(columns={'index': 'Confirmation_Time'})
    
    return confirmation_df, summary



# Calculate SD after Confirmation Time
def calculate_sd(dr_idr, confirmation_df):
    # Create a list to store the SD results
    sd_results = []

    # Iterate over each row in confirmation DataFrame
    for _, row in confirmation_df.iterrows():
        # Get the IDR_High and IDR_Low for the corresponding date
        dr_row = dr_idr[dr_idr['Date'] == row['Date']].iloc[0]
        
        IDR_High = dr_row['IDR_High']
        IDR_Low = dr_row['IDR_Low']
        confirmation_time = row['Confirmation_Time']
        
        # Calculate SD if confirmation_time exists
        if confirmation_time is not None:
            SD = (IDR_High - IDR_Low) / 10
        else:
            SD = None  # No SD if there's no confirmation time
        
        # Append the result for the current day
        sd_results.append((row['Date'],SD))

    # Return as DataFrame
    return pd.DataFrame(sd_results, columns=['Date','SD'])






def calculate_box_size(data, dr_idr_results):
    # Filter data to get 'Open' price at start_time and 'Close' price at end_time for each date
    start_time_data = data[data['Time'] == start_time].set_index('Date')
    end_time_data = data[data['Time'] == end_time].set_index('Date')

    # Merge 'Open' from start_time and 'Close' from end_time based on Date
    merged_data = start_time_data[['Open']].merge(end_time_data[['Close']], 
                                                  left_index=True, 
                                                  right_index=True, how='inner')
    # Add 'Date' as a column, not as an index
    merged_data['Date'] = merged_data.index
    merged_data.reset_index(drop=True, inplace=True)  # Reset the index to avoid duplicated 'Date' as index
    
    def box_size(row):
        # Fetch IDR_High and IDR_Low for the current date from dr_idr_results using row['Date']
        day_dr_idr = dr_idr_results[dr_idr_results['Date'] == row['Date']]  # Using row['Date'] for consistency
        
        if not day_dr_idr.empty:
            IDR_High = day_dr_idr['IDR_High'].iloc[0]
            IDR_Low = day_dr_idr['IDR_Low'].iloc[0]
        else:
            return pd.Series([0.0, "Grey"], index=['box_size', 'box_color'])

        # Calculate box_size and determine box_color
        if row['Open'] < row['Close']:
            box_color = "Green"
            box_size = round((row['Close'] - row['Open']) / (IDR_High - IDR_Low), 2)
        elif row['Open'] > row['Close']:
            box_color = "Red"
            box_size = round((row['Close'] - row['Open']) / (IDR_High - IDR_Low), 2) 
        else:  # Open == Close
            box_color = "Grey"
            box_size = 0.0
        
        return pd.Series([box_size, box_color], index=['box_size', 'box_color'])

    # Apply box_size function to merged data
    merged_data[['box_size', 'box_color']] = merged_data.apply(box_size, axis=1)

    return merged_data




def calculate_retracement(filtered_data, dr_idr_df, confirmation_results, sd_df):
    retracement_results = []
    
    # Group data by Date
    grouped_data = filtered_data.groupby('Date')
    
    for date, group in grouped_data:
        # Get relevant DR/IDR values for this day
        day_dr_idr = dr_idr_df[dr_idr_df['Date'] == date]
        if day_dr_idr.empty:
            continue  # Skip if no DR/IDR data
        
        # Extract IDR high and low
        IDR_High = day_dr_idr['IDR_High'].iloc[0]
        IDR_Low = day_dr_idr['IDR_Low'].iloc[0]
        
        # Get direction from confirmation results
        direction_row = confirmation_results[confirmation_results['Date'] == date]
        direction = direction_row['Direction'].iloc[0] if not direction_row.empty else None
        
        # Get SD value for the day
        sd_row = sd_df[sd_df['Date'] == date]
        if sd_row.empty:
            continue  # Skip if no SD data
        SD = sd_row['SD'].iloc[0]
        
        # Filter group data within IDR retracement timeframe
        after_confirmation = group[group['Time'] > direction_row['Confirmation_Time'].iloc[0]]  # Adjust 'Time' column if named differently
        
        if direction == "Long":
            ret=after_confirmation['Low'].min()
            retracement = round(((after_confirmation['Low'].min() - IDR_High) / SD / 10),2)
            
        elif direction == "Short":
                ret=after_confirmation['High'].max()
                retracement = round(((IDR_Low - after_confirmation['High'].max()) / SD / 10),2)
        else:
            retracement = None
     
        
        retracement_results.append((date,ret, retracement))
    
    # Return as DataFrame
    return pd.DataFrame(retracement_results, columns=['Date', 'Ret','Retracement'])



# Calculate Extension (Target)
# Calculate Extension (Target) for each day
def calculate_extension(filtered_data, dr_idr_df, confirmation_results, sd_df):
    extension_results = []
    
   # Group data by Date
    grouped_data = filtered_data.groupby('Date')
    
    for date, group in grouped_data:
        # Get relevant DR/IDR values for this day
        day_dr_idr = dr_idr_df[dr_idr_df['Date'] == date]
        if day_dr_idr.empty:
            continue  # Skip if no DR/IDR data
        
        # Extract IDR high and low
        IDR_High = day_dr_idr['IDR_High'].iloc[0]
        IDR_Low = day_dr_idr['IDR_Low'].iloc[0]
        
        # Get direction from confirmation results
        direction_row = confirmation_results[confirmation_results['Date'] == date]
        direction = direction_row['Direction'].iloc[0] if not direction_row.empty else None
        
        # Get SD value for the day
        sd_row = sd_df[sd_df['Date'] == date]
        if sd_row.empty:
            continue  # Skip if no SD data
        SD = sd_row['SD'].iloc[0]
        
        # Filter group data within IDR retracement timeframe
        after_confirmation = group[group['Time'] > direction_row['Confirmation_Time'].iloc[0]]  # Adjust 'Time' column if named differently
        
        # Calculate Extension for Long or Short
        if direction == "Long":
            ext=after_confirmation['High'].max()
            extension = round(((after_confirmation['High'].max() - IDR_High) / SD / 10),2)
        elif direction == "Short":
            ext=after_confirmation['Low'].min()
            extension = round(((IDR_Low-after_confirmation['Low'].min()) / SD / 10),2)
        else:
            extension = None
        
        extension_results.append((date,ext, extension))
    
    # Return as DataFrame
    return pd.DataFrame(extension_results, columns=['Date', 'Ext','Extension'])






# Preparing datasets for strategy test
def strategy_data(data):
    # Parse the date column and filter between start_date and end_date
    data['Date'] = pd.to_datetime(data['Date'])
    new_data = data[(data['Date'] >= start_date) & (data['Date'] <= end_date)]

    # Filter for specified day of the week if not 'all'
    if day != 'all':
        day_map = {'mo': 0, 'tu': 1, 'we': 2, 'th': 3, 'fr': 4}
        new_data = new_data[new_data['Date'].dt.weekday == day_map[day]]

    # Filter data within the 9:30 to 16:10
    strat_data = new_data[(new_data['Time'] >= start_time) & (new_data['Time'] <= strategy_end_time)]

    return strat_data


def run_backtest(data):
    session_data = filter_data(data) # data set for phase 1
    strategy_test_data=strategy_data(data) # data set for phase 2
    dr_idr_results = calculate_dr_idr(session_data)
    confirmation_results,Conf_times = confirmation(session_data, dr_idr_results)
    SD = calculate_sd(dr_idr_results, confirmation_results)
    retracement = calculate_retracement(session_data, dr_idr_results,confirmation_results , SD)
    extension = calculate_extension(session_data, dr_idr_results, confirmation_results, SD)
    box_sizes = calculate_box_size(session_data, dr_idr_results)

    # Merge the data frames based on the 'Date' column
    combined_data = session_data.merge(dr_idr_results, on='Date', how='left') \
                            .merge(confirmation_results, on='Date', how='left') \
                            .merge(SD, on='Date', how='left') \
                            .merge(retracement, on='Date', how='left') \
                            .merge(extension, on='Date', how='left')

    
    combined_file_filtered = combined_data[['Date', 'DR_High','DR_Low', 'IDR_High', 'IDR_Low', 
                    'Confirmation_Time', 'Direction', 'SD', 'Retracement', 'Extension','Ret','Ext']]
    merged_df = pd.merge(box_sizes,combined_file_filtered ,on='Date', how='inner')
     # Renaming the columns
    merged_df= merged_df.rename(columns={
        'Open': 'Box_open',
        'Close':'Box_close',
        'DR_High': 'DRH',
        'DR_Low': 'DRL',
        'IDR_High': 'IDRH',
        'IDR_Low': 'IDRL',
        'Retracement': 'SD Retracement',
        'Extension': 'SD Extension',
        'box_size': 'Box_size',
        'box_color': 'Box_color'
    })
     # Reordering columns
    columns_order = [
        'Date', 'DRH', 'DRL', 'IDRH', 'IDRL', 'Box_open', 'Box_close', 
        'Confirmation_Time', 'SD', 'Direction', 'Ret','SD Retracement','Ext',
        'SD Extension', 'Box_size', 'Box_color'
    ]
    
    merged_df=merged_df[columns_order]
    # To find unique rows
    merged_df_unique = merged_df.drop_duplicates()
   
    merged_df_unique.to_csv('combined_file.csv', index=False)
    
    merged_strategy_data=pd.merge(strategy_test_data, merged_df, on='Date', how='right')
    merged_strategy_data_sorted = merged_strategy_data.sort_values(by=['Date', 'Time'], ascending=[True, True])
    unique_strategy_data = merged_strategy_data_sorted.drop_duplicates(subset=['Date', 'Time'])
    
    return merged_df_unique, unique_strategy_data, Conf_times
    
    
# Load the CSV file with semicolon as the delimiter
def load_data(file_path, file_type='csv'):
    if file_type == 'csv':
        raw_data = pd.read_csv(file_path) # Replace "your_file.txt" with the actual file path
        raw_data=raw_data.dropna(axis=1,how='all')
        return raw_data
    elif file_type == 'txt':
        raw_data = pd.read_csv(file_path, delimiter=';') # Replace "your_file.txt" with the actual file path
        return raw_data
    else:
        raise ValueError("Unsupported file type.")


df = pd.read_csv(file_path)

# Ensure that the 'time' column is ISO and datetime format (with New York timezone)
df['datetime'] = pd.to_datetime(df['time'], utc=True)

# Adjust the timezone to UTC-5
df['datetime'] = df['datetime'].dt.tz_convert('US/Eastern')


# Ensure the datetime column is in ISO format
#df['datetime'] = pd.to_datetime(df['time'],utc='True')


## Initialize empty list to hold new data
new_data = []

# Iterate over the rows of the dataframe
for index, row in df.iterrows():
    # Extract the Date and Time from the 'datetime' column
    date = row['datetime'].date()
    time = row['datetime'].time()

   
    # Append the result to the new data list
    new_data.append({
        'Date': date,
        'Time': time,
        'Open': row['open'],
        'High' : row['high'],
        'Low' : row['low'],
        'Close': row['close']
    })


# For Sample Check, save the updated DataFrame back to a CSV
# Create a new DataFrame with the result
raw_data = pd.DataFrame(new_data)

# Optionally, save the new DataFrame to a CSV file
raw_data.to_csv(r'C:\\Users\\HP\\Documents\\new_file.csv', index=False)


# Run backtest
results,strategy_dataset,confirmation_times=run_backtest(raw_data)
# Save strategy_dataset to a CSV file for later use
strategy_dataset.to_csv(r'C:\\Users\\HP\\Documents\\strategy_dataset.csv', index=False)
print(results.head(10))
print('\n Confirmation Times')
print(confirmation_times)
#print(strategy_dataset)

