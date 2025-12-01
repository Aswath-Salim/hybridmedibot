import datetime
import os
from pymongo import MongoClient

def connect_to_mongodb():
    """Connects to MongoDB using the connection string from the .env file."""
    try:
        mongo_uri = os.environ.get("MONGODB_CONNECTION_STRING")
        if not mongo_uri:
            print("Error: MongoDB connection string not found in environment variables")
            return None
            
        # Updated connection parameters
        client = MongoClient(
            mongo_uri,
            tls=True,
            tlsAllowInvalidCertificates=True,  # For development only
            serverSelectionTimeoutMS=5000
        )
        
        # Test the connection
        client.admin.command('ping')
        return client
        
    except Exception as e:
        print(f"Error connecting to MongoDB: {e}")
        return None

def get_user_collection(client):
    """Returns the user collection from the MongoDB database."""
    db = client.get_database(os.environ.get("MONGODB_DATABASE_NAME", "jarvis"))  # Use environment variable for database name, default to "jarvis"
    user_collection = db.get_collection("users")
    return user_collection

def store_user_data(user_id, data):
    """Stores user data in MongoDB."""
    client = connect_to_mongodb()
    if client:
        user_collection = get_user_collection(client)
        user_collection.update_one(
            {"user_id": user_id},
            {"$set": data},
            upsert=True
        )
        client.close()
        return True
    else:
        return False

def get_user_data(user_id):
    """Retrieves user data from MongoDB."""
    client = connect_to_mongodb()
    if client:
        user_collection = get_user_collection(client)
        user_data = user_collection.find_one({"user_id": user_id})
        client.close()
        return user_data
    else:
        return None

def get_weather_collection(client):
    """Returns the weather collection from the MongoDB database."""
    db = client.get_database(os.environ.get("MONGODB_DATABASE_NAME", "jarvis"))
    weather_collection = db.get_collection("weather")
    return weather_collection

def store_weather_data(city, data):
    """Stores weather data in MongoDB."""
    client = connect_to_mongodb()
    if client:
        weather_collection = get_weather_collection(client)
        weather_collection.update_one(
            {"city": city},
            {"$set": {"data": data, "timestamp": datetime.datetime.utcnow()}},
            upsert=True
        )
        client.close()
        return True
    else:
        return False

def store_user_location(user_id, city, state):
    """Stores user location in MongoDB."""
    client = connect_to_mongodb()
    if client:
        user_collection = get_user_collection(client)
        user_collection.update_one(
            {"user_id": user_id},
            {"$set": {"city": city, "state": state}},
            upsert=True
        )
        client.close()
        return True
    else:
        return False

def get_user_location(user_id):
    """Retrieves user location from MongoDB."""
    client = connect_to_mongodb()
    if client:
        user_collection = get_user_collection(client)
        user_data = user_collection.find_one({"user_id": user_id})
        client.close()
        if user_data:
            return {"city": user_data.get("city"), "state": user_data.get("state")}
        else:
            return None
    else:
        return None

def get_weather_data(city):
    """Retrieves weather data from MongoDB if it's less than 5 minutes old."""
    client = connect_to_mongodb()
    if client:
        weather_collection = get_weather_collection(client)
        weather_data = weather_collection.find_one({"city": city})
        client.close()
        if weather_data:
            time_difference = datetime.datetime.utcnow() - weather_data["timestamp"]
            if time_difference.total_seconds() < 300:  # 5 minutes = 300 seconds
                return weather_data["data"]
            else:
                return None
        else:
            return None
    else:
        return None


if __name__ == '__main__':
    import datetime
    # Example usage
    client = connect_to_mongodb()
    if client:
        print("Connected to MongoDB successfully!")
        user_collection = get_user_collection(client)
        print("Got user collection successfully!")

        # Store user data
        user_id = "12345"
        user_data = {"name": "John Doe", "city": "New York"}
        if store_user_data(user_id, user_data):
            print(f"Stored user data for user_id: {user_id}")

        # Retrieve user data
        retrieved_data = get_user_data(user_id)
        if retrieved_data:
            print(f"Retrieved user data: {retrieved_data}")
        else:
            print(f"Could not retrieve user data for user_id: {user_id}")

        # Store weather data
        city = "London"
        weather_data = {"temperature": 20, "condition": "Cloudy"}
        if store_weather_data(city, weather_data):
            print(f"Stored weather data for city: {city}")

        # Retrieve weather data
        retrieved_weather_data = get_weather_data(city)
        if retrieved_weather_data:
            print(f"Retrieved weather data: {retrieved_weather_data}")
        else:
            print(f"Could not retrieve weather data for city: {city}")

        client.close()
    else:
        print("Failed to connect to MongoDB.")