from fastapi import FastAPI
import json
import random

app = FastAPI()

# Function to read JSON file and return a random quantity of items (minimum 5)
def load_json_data():
    try:
        with open('data.json', 'r') as file:
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
    return {
        'status': 'success',
        'data': data
    }
