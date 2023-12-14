# Import necessary libraries and modules
from fastapi import FastAPI, Body, HTTPException
from pydantic import BaseModel, Field
from fastapi.middleware.cors import CORSMiddleware
import requests
import logging
import os

# Initialize logging with INFO level
logging.basicConfig(level=logging.INFO)

# Create a FastAPI instance
app = FastAPI()

# Retrieve CORS origins from environment variable or use default values
origins = os.getenv('CORS_ORIGINS', 'http://localhost:3000,http://127.0.0.1:3000').split(',')
# Configure CORS policy for the FastAPI app
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Define Pydantic model for input data validation
class EVInputData(BaseModel):
    origin_location: str
    destination_location: str
    max_radius: float
    ev_model: str
    initial_SOC: float = Field(..., ge=0, le=100)  # Range 0-100%
    fast_charging_priority: bool = False

# Endpoint to process EV routing data
@app.post("/process_data")
async def process_data(data: EVInputData = Body(...)):
    try:
        # Convert input data to JSON
        json_data = data.dict()
        
        # Navigator service endpoint URL
        navigator_url = "http://navigator:8001/calculate_route"
        
        # Make a POST request to navigator service
        response = requests.post(navigator_url, json=json_data)
        
        # Handle response
        if response.status_code == 200:
            station_results = response.json()
            return {"message": "Data processed successfully", "charging_stations": station_results}
        else:
            raise HTTPException(status_code=response.status_code, detail=response.text)
    
    except requests.RequestException as req_exc:
        logging.error(f"Request failed: {req_exc}")
        raise HTTPException(status_code=503, detail="Navigator service unavailable")
    
    except Exception as e:
        logging.error(f"An error occurred: {e}")
        raise HTTPException(status_code=500, detail=str(e))
