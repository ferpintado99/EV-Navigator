# Import necessary libraries and modules
from fastapi import FastAPI, HTTPException, Body
from pydantic import BaseModel
from geopy.geocoders import Nominatim
import requests
import json
import mysql.connector
import os
import logging
logging.basicConfig(level=logging.INFO)
import sys
from bs4 import BeautifulSoup

# Initialize FastAPI app
app = FastAPI()


# Define a Pydantic model to validate and structure incoming data
class RouteCalculationData(BaseModel):
    origin_location: str
    destination_location: str
    max_radius: float
    ev_model: str
    initial_SOC: float
    fast_charging_priority: bool = False

# Endpoint to calculate the route and return charging station data
@app.post("/calculate_route")
async def calculate_route(data: RouteCalculationData):
    try:
        # Call the main processing function with input data
        return your_main_code(data)
    except HTTPException as http_ex:
        # Forward the HTTPException
        raise http_ex
    except Exception as ex:
        # Handle unexpected exceptions
        raise HTTPException(status_code=500, detail=str(ex))
    
# API keys configuration

# IMPORTANT: Please obtain your own API keys and fill in the following variables.

# Open Charge Map API Key: Obtain your key from https://openchargemap.org/site and replace below
OCM_API_KEY = 'YOUR_OPEN_CHARGE_MAP_API_KEY_HERE'
# Bing Maps API Key: Obtain your key from https://www.bingmapsportal.com/ and replace below
BING_MAPS_API_KEY = "YOUR_BING_MAPS_API_KEY_HERE"



def get_coordinates(geolocator, address):

    """
    Retrieve geographic coordinates for a given address using the specified geolocator.

    Args:
    geolocator: The geocoding service instance used for converting addresses into coordinates.
    address (str): The address to geocode.

    Returns:
    tuple: A pair of floats (latitude, longitude) representing the geographic coordinates of the address.
           Returns None if the address cannot be found or if an error occurs.

    This function attempts to find the latitude and longitude of an address. If successful, it returns the coordinates.
    If the address is not found or if a geocoding service error occurs, appropriate errors are logged, and None is returned.
    """

    try:
        location = geolocator.geocode(address)
        if location:
            return location.latitude, location.longitude
        logging.error("Address not found. Please enter a valid address.")
        return None
    except GeocoderTimedOut:
        logging.error("Geocoding service timed out. Please try again later.")
        return None
    except Exception as e:
        logging.error(f"Error occurred: {e}")
        return None



def is_percentage(value):

    """
    Determine if a value is within the percentage range (0 to 100).

    Args:
    value (float/int): The value to be checked.

    Returns:
    bool: True if the value is between 0 and 100 (inclusive), False otherwise.

    This function evaluates whether a given value falls within the standard percentage range.
    It's useful for validating whether a number represents a valid percentage.
    """

    return 0 <= value <= 100

def get_temperature(latitude, longitude):

    """
    Retrieve the current temperature for specified geographic coordinates.

    Args:
    latitude (float): The latitude coordinate.
    longitude (float): The longitude coordinate.

    Returns:
    float: The current temperature at the given location. Returns None if the temperature
           cannot be fetched or an error occurs.

    This function fetches the current temperature using an external weather API.
    It handles various response scenarios and logs any errors encountered during the request.
    """

    url = 'https://api.open-meteo.com/v1/forecast'
    params = {
        'latitude': latitude,
        'longitude': longitude,
        'current_weather': 'true',
        'hourly': 'temperature_2m'
    }

    try:
        response = requests.get(url, params=params)
        if response.status_code == 200:
            data = response.json()
            return data['current_weather']['temperature']
        else:
            logging.error(f"Error fetching temperature: {response.json().get('error')}")
            return None
    except requests.exceptions.RequestException as e:
        logging.error(f"Error occurred during temperature request: {e}")
        return None


    
def fetch_charging_station_data(api_key, latitude, longitude, max_radius):
   
    """
    Fetches charging station data from the Open Charge Map API based on given coordinates and search radius.

    Args:
    api_key (str): The API key for accessing the Open Charge Map API.
    latitude (float): The latitude coordinate of the search location.
    longitude (float): The longitude coordinate of the search location.
    max_radius (int): The maximum search radius in kilometers.

    Returns:
    list or None: A list of charging stations within the specified radius if successful, None otherwise.

    The function constructs a request to the Open Charge Map API with the provided parameters. If the request is successful
    and returns a status code of 200, the function returns the JSON response containing charging station data. If the request
    fails or returns a different status code, the function logs an error message and returns None.
    """

    ocm_url = 'https://api.openchargemap.io/v3/poi/'
    params = {
        "output": "json",
        "maxresults": 10,
        "compact": False,
        "verbose": False,
        "key": api_key,
        "latitude": latitude,
        "longitude": longitude,
        "distance": max_radius,
        "distanceunit": "KM",
        "includechargingprices": True
    }
    
    try:
        response = requests.get(ocm_url, params=params)
        if response.status_code == 200:
            return response.json()
        else:
            logging.error(f"Failed to get charging station data: {response.status_code}")
            return None
    except requests.exceptions.RequestException as e:
        logging.error(f"Error occurred during charging station data request: {e}")
        return None


def get_charging_stations(api_key, coordinates, max_radius):
    
    """
    Retrieves a list of charging stations within a specified radius of given coordinates.

    Args:
    api_key (str): The API key for accessing the charging stations data.
    coordinates (str): The latitude and longitude of the search center, separated by a comma.
    max_radius (int): The maximum search radius in kilometers.

    Returns:
    list: A list of dictionaries, each containing information about a charging station.

    The function splits the coordinates into latitude and longitude, and then calls fetch_charging_station_data to retrieve
    charging stations data from the Open Charge Map API. It processes the API response and constructs a list of dictionaries
    with relevant information about each station, including location, name, operator, usage type, cost, and connection details.
    If no data is received, it logs a warning and returns an empty list.
    """

    latitude, longitude = map(float, coordinates.split(','))
    ocm_data = fetch_charging_station_data(api_key, latitude, longitude, max_radius)

    if ocm_data is None:
        logging.warning("No charging station data received.")
        return []

    stations_info = []
    for station in ocm_data:
        station_dict = {
            'location': (station.get("AddressInfo", {}).get("Latitude"), station.get("AddressInfo", {}).get("Longitude")),
            'name': station.get("AddressInfo", {}).get("Title", "Unknown"),
            'operator': station.get('OperatorInfo', {}).get('Title', "Unknown"),
            'usage_type': station.get('UsageType', {}).get('Title', "Unknown"),
            'usage_cost': station.get('UsageCost', "Unknown"),
            'connections': [
                {
                    'connection_type': conn.get('ConnectionType', {}).get('Title', "Unknown"),
                    'price': conn.get('PricingModel', "Unknown")
                }
                for conn in station.get('Connections', [])
            ]
        }
        stations_info.append(station_dict)

    return stations_info


def get_route_info(origin, destination):
    
    """
    Retrieves detailed route information for driving from the origin to the destination.

    Args:
    origin (str): The starting point coordinates.
    destination (str): The endpoint coordinates.

    Returns:
    dict: A dictionary containing route details if successful, None otherwise.

    The function constructs a request to the Bing Maps API with origin and destination coordinates and specific parameters
    like avoiding tolls. It processes the API response, returning detailed route information in JSON format. In case of a request
    exception, an error is logged, and None is returned.
    """

    url = "http://dev.virtualearth.net/REST/V1/Routes/Driving"
    params = {
        "wp.0": origin,
        "wp.1": destination,
        "avoid": "minimizeTolls",
        "key": BING_MAPS_API_KEY,
    }

    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        logging.error(f"Error fetching route information: {e}")
        return None


def get_road_type(item):
    
    """
    Identifies the road type from a route segment.

    Args:
    item (dict): A dictionary representing a segment of the route.

    Returns:
    str: The type of road for the given segment, defaulting to 'Street' if not specified.

    This function examines the 'details' key in the route segment item to determine the road type, defaulting to 'Street' if
    the road type is not explicitly mentioned or if the mode of travel is not driving.
    """


    details = item.get("details", [])
    for detail in details:
        if detail.get("mode") == "Driving":
            return detail.get("roadType", "Street")
    return "Unknown"

def analyze_route(route_data):
    
    """
    Analyzes route data to aggregate distance information based on road types.

    Args:
    route_data (dict): Route data from Bing Maps API.

    Returns:
    tuple: A tuple containing a dictionary of route info and the sum of segment distances.

    This function processes the route data, extracting and aggregating travel distances for different road types. It calculates
    total travel distance, duration, and identifies traffic congestion levels. If the route data is invalid or missing key information,
    an error is logged, and default values are returned.
    """

    try:
        route_info = {
            "distance": route_data["resourceSets"][0]["resources"][0]["travelDistance"],
            "duration": route_data["resourceSets"][0]["resources"][0]["travelDuration"],
            "traffic_congestion": route_data["resourceSets"][0]["resources"][0].get("trafficCongestion", "Unknown"),
            "Highway": {"distance": 0}, "MajorRoad": {"distance": 0},
            "Arterial": {"distance": 0}, "LocalRoad": {"distance": 0},
            "Street": {"distance": 0}, "Ramp": {"distance": 0},
            "LimitedAccessHighway": {"distance": 0}
        }

        segment_distances_sum = 0
        itinerary_items = route_data["resourceSets"][0]["resources"][0]["routeLegs"][0]["itineraryItems"]
        
        for item in itinerary_items:
            road_type = get_road_type(item)
            distance = item["travelDistance"]
            if road_type in route_info:
                route_info[road_type]["distance"] += round(distance, 2)
                segment_distances_sum += round(distance, 2)

        route_info["distance"] = round(route_info["distance"], 2)
        return route_info, segment_distances_sum
    except (KeyError, IndexError, TypeError):
        logging.error("Error analyzing route data. Invalid data structure.")
        return None, 0

def get_ev_information(model):
    
    """
    Retrieves electric vehicle information from the database for a specified model.

    Args:
    model (str): The model of the electric vehicle.

    Returns:
    tuple: A tuple containing various attributes of the EV, or None if an error occurs.

    This function connects to the MySQL database to retrieve EV data. It queries the database for specific EV
    model attributes. If the model is found, it returns various attributes like usable capacity, charge port types,
    and efficiency rates. It handles database connection errors and cases where the EV model is not found.
    """

    
    try:
        cnx = mysql.connector.connect(
            host="db",  # Use the service name specified in docker-compose.yml
            user="root",
            password="password",
            database="ev_database"
        )

    except mysql.connector.Error as err:
        logging.error(f"Something went wrong: {err}")
        return None
    
    # Create a cursor to execute SQL queries
    cursor = cnx.cursor()

    # Define the SQL query
    query = "SELECT EV_model, Useable_Capacity, Charge_Port, Fast_charge_port, charge_power, charge_speed, city_cold_rate, highway_cold_rate, combined_cold_rate, city_mild_rate, highway_mild_rate, combined_mild_rate, weight FROM ev_data"

    # Execute the query
    cursor.execute(query)

    # Fetch all rows from the result
    rows = cursor.fetchall()

    # Find the matching EV model
    formatted_model = model.replace(" ", "-").title()
    try:
        for row in rows:
            if row[0] == formatted_model:
                ev_model = row[0]
                useable_capacity_str = row[1]
                charge_port = row[2]
                fast_charge_port = row[3]
                charge_power = row[4]
                charge_speed = row[5]
                city_cold_rate_str = row[6]
                highway_cold_rate_str = row[7]
                combined_cold_rate_str = row[8]
                city_mild_rate_str = row[9]
                highway_mild_rate_str = row[10]
                combined_mild_rate_str = row[11]
                weight = row[12]
                break  # Stop iterating after finding the matching EV model
        else:
            logging.error("EV model not found in the database")
            return None
    except mysql.connector.Error as err:
        logging.error(f"Database connection error: {err}")
        return None

    # Close the cursor and database connection
    cursor.close()
    cnx.close()

    rates = {
            'city_cold_rate_str': city_cold_rate_str,
            'highway_cold_rate_str': highway_cold_rate_str,
            'combined_cold_rate_str': combined_cold_rate_str,
            'city_mild_rate_str': city_mild_rate_str,
            'highway_mild_rate_str': highway_mild_rate_str,
            'combined_mild_rate_str': combined_mild_rate_str,
        }
    
    return useable_capacity_str, charge_port, fast_charge_port, charge_power, charge_speed, rates, weight

    
def get_elevation_change(origin_coords, destination_coords, bing_maps_key):
    
    """
    Calculates the elevation change between two geographic coordinates using Bing Maps API.

    Args:
    origin_coords (str): The starting coordinates.
    destination_coords (str): The ending coordinates.
    bing_maps_key (str): Bing Maps API key.

    Returns:
    float or str: The elevation change in meters, or 'Unknown' in case of an error.

    The function constructs an API request to Bing Maps to get elevation data for the specified coordinates.
    It calculates the elevation change and handles possible request exceptions by logging errors and returning 'Unknown'.
    """

    elevation_url = f'http://dev.virtualearth.net/REST/v1/Elevation/List?points={origin_coords},{destination_coords}&key={bing_maps_key}'

    try:
        elevation_response = requests.get(elevation_url)
        elevation_response.raise_for_status()
        elevation_data = elevation_response.json()

        if 'resourceSets' in elevation_data and elevation_data['resourceSets']:
            elevations = elevation_data['resourceSets'][0]['resources'][0]['elevations']
            elevation_change = elevations[1] - elevations[0]
            return elevation_change
        else:
            logging.warning("No elevation data found in the Bing Maps API response.")
            return "Unknown"
    except requests.RequestException as e:
        logging.error(f"An error occurred while fetching elevation data: {e}")
        return "Unknown"



def get_walking_route(origin_coords, destination_coords, bing_maps_key):

    """
    Calculates the walking route distance and duration between two coordinates using Bing Maps API.

    Args:
    origin_coords (str): The starting coordinates.
    destination_coords (str): The ending coordinates.
    bing_maps_key (str): Bing Maps API key.

    Returns:
    tuple: A tuple of the walking distance in kilometers and duration in minutes, or ('Unknown', 'Unknown') in case of an error.

    The function requests walking route data from Bing Maps API and extracts distance and duration. It handles request exceptions
    by returning 'Unknown' values for both distance and duration.
    """

    route_url = f'http://dev.virtualearth.net/REST/V1/Routes/Walking?wp.0={origin_coords}&wp.1={destination_coords}&optmz=distance&key={bing_maps_key}'
    
    try:
        route_response = requests.get(route_url)
        route_response.raise_for_status()
        route_data = route_response.json()
    

        if 'resourceSets' in route_data and route_data['resourceSets']:
            travel_distance = route_data['resourceSets'][0]['resources'][0]['travelDistance']
            travel_duration = route_data['resourceSets'][0]['resources'][0]['travelDuration']
            return travel_distance, travel_duration / 60  # Convert duration to minutes
        else:
            return "Unknown", "Unknown"
    except requests.RequestException as e:

        return "Unknown", "Unknown"



def calculate_soc(altitude_change, useable_capacity_str, weight, initial_SOC, temperature, route_info, rates_dict):

    """
    Calculates the State of Charge (SOC) for an electric vehicle considering various factors.

    Args:
    altitude_change (float): Change in altitude between origin and destination.
    useable_capacity_str (str): String representing the usable battery capacity.
    weight (float): Weight in kg of the vehicle.
    initial_SOC (float): Initial state of charge as a percentage.
    temperature (float): Ambient temperature.
    route_info (dict): Information about the route including distances by road type.
    rates_dict (dict): Dictionary containing discharge rates.

    Returns:
    tuple: A tuple containing final SOC and altitude-adjusted SOC percentages.

    The function calculates energy consumption based on road type, distance traveled, and discharge rates.
    It adjusts the SOC for potential energy  lost due to positive altitude changes. Exception handling is used
    to manage potential calculation errors, returning None in such cases.
    """

    try:

        weight = float(weight)  # Make sure weight is a float for calculations
        useable_capacity = float(useable_capacity_str.split()[0])
        potential_energy = (altitude_change * 9.81 * weight) / 3600000      
        discharge_highway = float(rates_dict['highway_cold_rate_str'].split()[0])
        discharge_city = float(rates_dict['city_cold_rate_str'].split()[0])
        
        # Calculate highway and city kilometers based on the route info
        highway_kilometers = (
            route_info["LimitedAccessHighway"]["distance"]
            + route_info["Highway"]["distance"]
            + route_info["Ramp"]["distance"]
            + route_info["Arterial"]["distance"]
            + route_info["MajorRoad"]["distance"]
        )
        

        city_kilometers = route_info["Street"]["distance"] + route_info["LocalRoad"]["distance"]
        

        if not rates_dict or all(value is None for value in rates_dict.values()):
            logging.error("Insufficient data to calculate SOC.")
            return None, None
        else:
            temperature_threshold = 10
            if temperature < temperature_threshold:
                discharge_highway = float(rates_dict['highway_cold_rate_str'].split()[0])
                discharge_combined = float(rates_dict['combined_cold_rate_str'].split()[0])
                discharge_city = float(rates_dict['city_cold_rate_str'].split()[0])
            else:
                discharge_highway = float(rates_dict['highway_mild_rate_str'].split()[0])
                discharge_combined = float(rates_dict['combined_mild_rate_str'].split()[0])
                discharge_city = float(rates_dict['city_mild_rate_str'].split()[0])

            final_SOC = ((initial_SOC * float(useable_capacity) * 10 - (discharge_highway * highway_kilometers + discharge_city * city_kilometers)) / (float(useable_capacity) * 1000)) * 100
            
            if altitude_change > 0:
                adjusted_SOC = final_SOC - potential_energy
            else:
                adjusted_SOC = final_SOC
        
        return final_SOC, adjusted_SOC

    except Exception as e:
        logging.error(f"An error occurred during SOC calculation: {e}")
        return None, None



def your_main_code(data: RouteCalculationData):
    """
    Processes user input to find optimal charging stations and calculate SoC around the final destination of an electric vehicle trip.

    Args:
    data (RouteCalculationData): User inputs including EV model, origin, destination, maximum search radius, initial state of charge (SoC), and fast charging priority.

    Returns:
    dict: Dictionary containing a success message and a list of suitable charging stations and parameters such as final SoC or walking time at each station.

    The function integrates several steps: retrieving EV information, converting locations to coordinates, getting temperature data, fetching charging stations, and calculating SoC. 
    Each charging station is evaluated for its suitability based on the route, available chargers, and expected SoC upon arrival. Exception handling ensures appropriate responses in case of data retrieval issues or missing information.
    """
    
    # Initialize the geolocator and extract necessary data from the input

    geolocator = Nominatim(user_agent="Navigator")
    origin_location = data.origin_location
    destination_location = data.destination_location
    max_radius = data.max_radius
    ev_model = data.ev_model
    initial_SOC = data.initial_SOC

    # Retrieve EV information from the database
    useable_capacity_str, charge_port, fast_charge_port, charge_power, charge_speed, rates, weight = get_ev_information(ev_model)
    if useable_capacity_str is None:
        raise HTTPException(status_code=404, detail="EV model not found in the database")

    # Convert origin and destination locations into latitude and longitude
    origin_latitude, origin_longitude = get_coordinates(geolocator, origin_location)
    if origin_latitude is None or origin_longitude is None:
        raise HTTPException(status_code=404, detail="Could not find the origin location")

    destination_latitude, destination_longitude = get_coordinates(geolocator, destination_location)
    if destination_latitude is None or destination_longitude is None:
        raise HTTPException(status_code=404, detail="Could not find the destination location")

    # Prepare coordinates for API calls
    origin_coordinates = f"{origin_latitude},{origin_longitude}"
    destination_coordinates = f"{destination_latitude},{destination_longitude}"

    # Get temperature and charging stations data
    temperature_origin = get_temperature(origin_latitude, origin_longitude)
    charging_stations = get_charging_stations(OCM_API_KEY, f"{destination_latitude},{destination_longitude}", max_radius)
    
    if not charging_stations:
        raise HTTPException(status_code=404, detail="No charging stations found within the specified radius and destination.")
    

    x = 1
    # Process each charging station and calculate SOC
    station_results = []  # Initialize a list to store station results
    for station in charging_stations:
        temperature_station = get_temperature(*station['location'])
        temperature = (temperature_origin + temperature_station) / 2
        station_coordinates = f"{station['location'][0]},{station['location'][1]}"
        origin_coordinates = f"{origin_latitude},{origin_longitude}"
        route_data = get_route_info(origin_coordinates, station_coordinates)
        route_info, segment_distances_sum = analyze_route(route_data)
        altitude_change = get_elevation_change(origin_coordinates, station_coordinates, BING_MAPS_API_KEY)
       
        walking_distance, walking_time = get_walking_route(station_coordinates, destination_coordinates, BING_MAPS_API_KEY)
        final_SOC, adjusted_SOC = calculate_soc(altitude_change, useable_capacity_str, weight, initial_SOC, temperature, route_info, rates)
        
        if adjusted_SOC<0:
            adjusted_SOC=0
        if x == 1 and adjusted_SOC==0:
            return("Your range is not enough to reach the destination. Please choose a closer destination.")
        if adjusted_SOC < 7.5:
            station_result = {
                "station_number": x,
                "station_name": station['name'],
                "warning": f"Predicted SOC at this charging station is too low ({adjusted_SOC:.1f}%)."
            }
        
        else:
           

            try:
                station_result = {
                    "station_number": x,
                    "station_name": station['name'],
                    "route_distance_km": route_info['distance'],
                    "route_duration_minutes": "{:.1f}".format(route_info['duration'] / 60),
                    "traffic_congestion": route_info['traffic_congestion'],
                    "charger_connections": [{"charger_type": conn['connection_type'], "price": conn.get('price', 'Unknown')} for conn in station['connections']],
                    "operator": station.get('operator', 'Unknown'),
                    "usage_cost": station.get('usage_cost', 'Unknown'),
                    "walking_time": "{:.1f}".format(float(walking_time)),
                    "elevation_change_m": altitude_change,
                    "final_SOC": final_SOC,
                    "altitude_adjusted_SOC": adjusted_SOC
            }
            except Exception as e:
                    logging.error(f"An error occurred: {e}")
           
        station_results.append(station_result)
        x=x+1
    response = {
        "message": "Data processed successfully",
        "charging_stations": station_results
    }
    return response


