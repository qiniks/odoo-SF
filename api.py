from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import json
import random

app = FastAPI()

# Configure CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins, restrict this in production
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)


# Function to read JSON file and return a random quantity of items (minimum 5)
def load_json_data():
    try:
        with open("data.json", "r") as file:
            data = json.load(file)
            # Check if data is a list and not empty
            if isinstance(data, list) and data:
                # Get total number of items
                total_items = len(data)
                # Randomly choose a quantity between 5 and total_items
                random_quantity = random.randint(5, total_items)
                # Return a random sample of that quantity
                return random.sample(data, k=random_quantity)
            else:
                return {"error": "No valid data found in JSON"}
    except FileNotFoundError:
        return {"error": "Data file not found"}
    except json.JSONDecodeError:
        return {"error": "Invalid JSON format"}
    except ValueError:
        return {"error": "Invalid quantity generated"}


# API endpoint
@app.get("/api/get_data")
async def get_data():
    data = load_json_data()
    # Ensure we return between 1-5 random items
    try:
        with open("data.json", "r") as file:
            all_data = json.load(file)
            if isinstance(all_data, list) and all_data:
                # Get random amount between 1 and 5 (or length of data if less than 5)
                random_amount = random.randint(1, min(5, len(all_data)))
                # Return random sample of that size
                return {
                    "status": "success",
                    "data": random.sample(all_data, k=random_amount),
                }
            else:
                return {"status": "error", "message": "No valid data found in JSON"}
    except FileNotFoundError:
        return {"status": "error", "message": "Data file not found"}
    except json.JSONDecodeError:
        return {"status": "error", "message": "Invalid JSON format"}
    except ValueError:
        return {"status": "error", "message": "Error generating random data"}


# API endpoint that returns a specific random amount of data
@app.get("/api/get_data/{amount}")
async def get_random_data(amount: int):
    try:
        with open("data.json", "r") as file:
            data = json.load(file)
            # Check if data is a list and not empty
            if isinstance(data, list) and data:
                # Ensure amount is not larger than available data
                amount = min(amount, len(data))
                # Return a random sample of the specified amount
                return {"status": "success", "data": random.sample(data, k=amount)}
            else:
                return {"status": "error", "message": "No valid data found in JSON"}
    except FileNotFoundError:
        return {"status": "error", "message": "Data file not found"}
    except json.JSONDecodeError:
        return {"status": "error", "message": "Invalid JSON format"}
    except ValueError:
        return {"status": "error", "message": "Invalid amount specified"}
