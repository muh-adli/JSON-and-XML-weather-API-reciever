import os
import requests
import pandas as pd
import geopandas as gpd
import datetime
import matplotlib.pyplot as plt
import json

try:
    with open('.venv/API.txt', 'r') as file:
        API_KEY = file.read().strip()
    print('API Key found.')
except Exception as e:
    print('API Key not found.')

## make code for input city name
print('Default city is Jakarta')
# city = input('Enter a city name: ')
city = 'Jakarta' # Default city is Jakarta

# API calling format to change city and use API KEY
BASE_URL = 'http://api.openweathermap.org/data/2.5/weather'
request_url = f'{BASE_URL}?appid={API_KEY}&q={city}'
print('Calling API')
response = requests.get(request_url)

# to make sure the response is correct
if response.status_code == 200:
    data = response.json()
    print('Data Accepted.')
else:
    print(f'Error {response.status_code}: {response.text}')

print('Processing Data.')
# Get Coordinate
Lat = data['coord']['lat']
Long = data['coord']['lon']

# Convert Unix time to Datetime
Date = str(datetime.datetime.fromtimestamp(data['dt']).strftime('%Y-%m-%d %H:%M:%S'))

# Get weather data
City_Name = data['name']
Temp_Avg = round(((data['main']['temp_max']+data['main']['temp_min'])/2)- 273.15,2) # Converting Kelvin to Celsius
Pressure = data['main']['pressure']
Humidity = data['main']['humidity']
Wind_spd = data['wind']['speed']
Wind_deg = data['wind']['deg']
Cloud_Percent = data['clouds']['all']

# Printing output data from API
print(f'''
      It's {Date}
      temperature in {City_Name} is {Temp_Avg}°C
      with {Cloud_Percent}% cloud
      and {Humidity}% Humidity''')

# Formating from JSON to Pandas Dataframe
Data_Clean = pd.DataFrame({
    'Date': Date,
    'City': City_Name,
    'Temp_Avg': str(Temp_Avg) + ' Celcius',
    'Pressure': Pressure,
    'Humidity': str(Humidity) + ' %',
    'Wind_spd': Wind_spd,
    'Wind_deg': Wind_deg,
    'Cloud': str(Cloud_Percent) + ' %',
    'Long': Long,
    'Lat': Lat,}
    , index=[0])
print('Done.')

# Location
crs = {'init':'epsg:4326'}
geo_data = Data_Clean
Data_Clean['geometry'] = gpd.points_from_xy(Data_Clean['Long'], Data_Clean['Lat'])
geo_data = gpd.GeoDataFrame(Data_Clean, crs=crs, geometry=Data_Clean['geometry'])
geo_data.explore()

# Convert the DataFrame to a dictionary and then to JSON
if 'geometry' in Data_Clean.columns:
    Data_Clean = pd.DataFrame(Data_Clean.drop(columns='geometry'))
JSON_Data = Data_Clean.to_dict(orient='records')

# Export JSON data to a file
try:
    file_path = 'datastorage/weatherdata.json'
    # Checking weather data storage
    if os.path.exists(file_path):
        print('Dataset exists. Reading Data.')
        Data_Clean['Date'] = pd.to_datetime(Data_Clean['Date'])
        Data_Existing = pd.read_json(file_path)

        print('Merging data.')
        Data_Merged = pd.concat([Data_Clean,Data_Existing], ignore_index=True)
        Data_Merged = Data_Merged.to_json(orient = 'records')

        with open(file_path, 'w') as JSON_File:
            json.dump(json.loads(Data_Merged), JSON_File)
        print('DataFrame exported to JSON successfully.')

    # if data not available, make a new one
    else:
        print('Dataset not found. Building new dataset.')
        with open(file_path, 'w') as JSON_File:
            json.dump(JSON_Data, JSON_File)
        print('DataFrame exported to JSON successfully.')

# Printing error that occured if existed
except Exception as e:
    print(f'Error: {e}')

# Load Dataset file
Dataset = pd.read_json(file_path)
print('Dataset found.')

# Define CRS
CRS = {'init':'epsg:4326'}

# Plotting coordinate with geopandas
print('Plotting with coordinate')
Dataset['geometry'] = gpd.points_from_xy(Dataset['Long'], Dataset['Lat'])
GeoDataset = gpd.GeoDataFrame(Dataset, crs=crs, geometry=Dataset['geometry'])
GeoDataset['Date'] = GeoDataset['Date'].dt.strftime('%Y-%m-%d %H:%M:%S')
GeoDataset.explore()

## Code to input desired city
print('Default city is Jakarta')
# Filter_City = input('Input a City to visualize: ')
Filter_City = 'Jakarta' # Default filtered city is Jakarta
Dataset_Filtered = Dataset[Dataset['City'] == Filter_City]

if Dataset_Filtered.empty:
    # Print console if dataset is empty
    print('Data not available.')

else:
    print('Processing Data.')
    # Cleansing data to dd-mm-yy format
    Dataset_Filtered['Date'] = Dataset_Filtered['Date'].dt.strftime('%d-%m-%Y')

    # Removing Geometry data if available
    if 'geometry' in Dataset_Filtered.columns:
        Dataset_Filtered = pd.DataFrame(Dataset_Filtered.drop(columns='geometry'))

    # Removing city column because its object that cannot use by .mean()
    if 'City' in Dataset_Filtered.columns:
        Dataset_Filtered = pd.DataFrame(Dataset_Filtered.drop(columns='City'))

    # Converting the object data value to numeric value
    convert_columns = ['Temp_Avg', 'Humidity', 'Cloud']
    for column in convert_columns:
        Dataset_Filtered[column] = pd.to_numeric(Dataset_Filtered[column].str.extract(r'(\d+\.*\d*)')[0], errors='coerce')

    # Averaging data by date
    Filtered_Date = Dataset_Filtered.groupby('Date').mean().reset_index()

    numeric_columns = ['Temp_Avg', 'Pressure', 'Humidity', 'Wind_spd', 'Wind_deg', 'Cloud']
    Filtered_Date[numeric_columns] = Filtered_Date[numeric_columns].round(2)

    ## Averaging data by Hour
    # Filtered_Hour = Dataset_Filtered.groupby([Dataset_Filtered['time'].dt.hour]).mean().reset_index()

    # Adding city data by filtered city
    Dataset_Filtered['City'] = Filter_City
    print('Done.')

### Visualizing Data from dataset
print('Visualizing Data.')
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10,6))
plt.subplots_adjust(left=0.1, right=0.9, bottom=0.1, top=0.9, wspace=0.2, hspace=0.4)
fig.suptitle(f'Weather in {Filter_City}')

# Sorting Data
Filtered_Date = Filtered_Date.sort_values(by='Date', ascending=False).reset_index(drop=True)

# Define data to plotting
ax1.plot(Filtered_Date['Date'],
        Filtered_Date['Temp_Avg'], 'o-')

ax2.plot(Filtered_Date['Date'],
        Filtered_Date['Cloud'], 'o-')

# Configure the label and title figure
ax1.set(ylabel=r'Celcius ($^\circ$C)',
       )
ax1.set_title('Temperature')

ax2.set(xlabel='Date',
       ylabel=r'Percentage (%)',
       )
ax2.set_title('Cloud Percentage')

# Configure grid to visualize the y axis grid
ax1.grid(which='both')
ax1.grid(which='minor', alpha=0.2, linestyle='dotted')
ax1.grid(which='major', alpha=0.5, linestyle='dotted')
ax1.set_ylim([0, 100])

ax2.grid(which='both')
ax2.grid(which='minor', alpha=0.2, linestyle='dotted')
ax2.grid(which='major', alpha=0.5, linestyle='dotted')
ax2.set_ylim([0, 100])
print('Done.')

plt.show()