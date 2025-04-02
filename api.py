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

# Helper function to load JSON data
def load_json_data():
    try:
        with open("data.json", "r") as file:
            data = json.load(file)
            if isinstance(data, list) and data:
                return data
            else:
                return None
    except FileNotFoundError:
        return None
    except json.JSONDecodeError:
        return None

# API endpoint to return a random number of items (1 to max, capped at 100)
@app.get("/api/get_data")
async def get_data():
    data = load_json_data()
    if data is None:
        return {"status": "error", "message": "Error loading data (file not found or invalid JSON)"}
    
    total_items = len(data)
    # Randomly choose a quantity between 1 and the total number of items (up to 100)
    random_quantity = random.randint(1, min(total_items, 100))
    return {
        "status": "success",
        "data": random.sample(data, k=random_quantity),
    }

# API endpoint to return a specific random amount of data (1 to max, capped at 100)
@app.get("/api/get_data/{amount}")
async def get_random_data(amount: int):
    data = load_json_data()
    if data is None:
        return {"status": "error", "message": "Error loading data (file not found or invalid JSON)"}
    
    total_items = len(data)
    # Ensure amount is between 1 and the total items, capped at 100
    if amount < 1:
        return {"status": "error", "message": "Amount must be at least 1"}
    amount = min(amount, total_items, 100)
    return {
        "status": "success",
        "data": random.sample(data, k=amount),
    }

# Optional: Run the app (for testing with uvicorn)
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
