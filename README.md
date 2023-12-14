# EV-Navigator
EV-Navigator is an innovative microservice solution for EV owners to find the best charging stations near their destinations. It merges multiple external services for data on road conditions, weather and charging availability. The project estimates state of charge at each station. It includes Docker setup and comprehensive documentation.

## Features
- Real-time data integration for weather, road conditions, and charging stations.
- Estimations of SoC upon arrival at each station.
- Docker configuration for easy deployment.

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
  "max_radius": 50,
  "ev_model": "ModelName",
  "initial_SOC": 80,
  "fast_charging_priority": true
}
