# EV-Navigator Microservice
EV-Navigator is an innovative microservice solution for EV owners to find the best charging stations near their destinations. It merges multiple external services for data on road conditions, weather and charging availability. The project estimates state of charge at each station. It includes Docker setup and comprehensive documentation.

## Microservice: 3 docker containers: Navigator + API +Database

## Features

- Integrates with external APIs for road, weather, elevation and charging station data.
- Estimates the State of Charge (SoC) for EVs.
- Utilizes Docker for simplified orchestration of services.

## Setup
1. Clone the repository.
2. Use `docker-compose up` to start the services.
3. Send a POST request to the API with necessary parameters.

## Usage
Send a POST request with the following JSON payload structure:
```json
{
  "origin_location": "CityA",
  "destination_location": "CityB",
  "max_radius": 50 "in kilometres",
  "ev_model": "ModelName eg Nissan Leaf",
  "initial_SOC": 80,
  "fast_charging_priority": true/false
}

### How It Works

#### Data Collection

1. **User Inputs**: Collects origin, destination, EV model, and other parameters.
2. **Geolocation**: Uses the Nominatim API to get coordinates for the entered locations.
3. **Weather**: Fetches current temperature using the Open-Meteo API.
4. **Charging Stations**: Uses the Open Charge Map API to find available charging stations within a specified radius.
5. **Route Information**: Uses the Bing Maps API to get route details between the origin and each charging station.
6. **Elevation**: Uses the Bing Maps API to calculate elevation changes along the route.
7. **Walking Distance**: Calculates the walking distance and time from each station to the destination.

### Repository Structure

- `docker-compose.yml`: Docker Compose file to orchestrate the containers.
- `init.sql`: SQL file to initialize the database.
- `navigator/`: Folder containing the main application.
  - `main.py`: Main application logic.
  - `Dockerfile`: Dockerfile for the application.
  - `requirements.txt`: Required Python packages.
- `api/`: Folder containing the API.
  - `api.py`: API server code.
  - `Dockerfile`: Dockerfile for the application.
  - `requirements.txt`: Required Python packages.

### Built With

- Python
- MySQL
- Docker
- Various APIs (Nominatim, Open-Meteo, Open Charge Map, Bing Maps)

### Dependencies

All Python package dependencies are listed in `requirements.txt` and can be installed using pip.

```bash
pip install -r requirements.txt
```
### Authors
Fernando Pintado - Initial work - YourGitHub
License
This project is licensed under the MIT License - see the LICENSE.md file for details.


