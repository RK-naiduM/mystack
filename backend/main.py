import os
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from pymongo import MongoClient
from bson import ObjectId
from typing import List
from dotenv import load_dotenv
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables from .env file
load_dotenv()

# Get MongoDB URI from environment variable
mongo_uri = os.getenv("MONGO_URI")

# Check if the MongoDB URI is loaded correctly
if not mongo_uri:
    logger.error("MongoDB URI not found in environment variables!")
    raise ValueError("MongoDB URI is not set in the .env file")

# MongoDB connection setup
try:
    client = MongoClient(mongo_uri)
    db = client.contact_manager
    collection = db.contacts
    logger.info("MongoDB connection successful!")
except Exception as e:
    logger.error(f"Failed to connect to MongoDB: {e}")
    raise ConnectionError(f"Could not connect to MongoDB: {e}")

# FastAPI app initialization
app = FastAPI()

# Pydantic model for contact details (including ObjectId handling)
class Contact(BaseModel):
    name: str
    age: int
    mobile: str
    email: str

    class Config:
        # Make sure ObjectId is serialized to string when returning in API responses
        json_encoders = {
            ObjectId: str
        }

# Create contact
@app.post("/contacts/")
def create_contact(contact: Contact):
    try:
        contact_dict = contact.dict()
        result = collection.insert_one(contact_dict)
        logger.info(f"Contact created with ID: {result.inserted_id}")
        return {"id": str(result.inserted_id), "message": "Contact created successfully"}
    except Exception as e:
        logger.error(f"Error creating contact: {e}")
        raise HTTPException(status_code=500, detail="Error creating contact")

# Get all contacts
@app.get("/contacts/", response_model=List[Contact])
def get_contacts():
    try:
        contacts = list(collection.find())
        logger.info(f"Retrieved {len(contacts)} contacts from MongoDB")
        return contacts
    except Exception as e:
        logger.error(f"Error retrieving contacts: {e}")
        raise HTTPException(status_code=500, detail="Error retrieving contacts")

# Update contact
@app.put("/contacts/{contact_id}")
def update_contact(contact_id: str, contact: Contact):
    try:
        updated_contact = contact.dict()
        result = collection.update_one({"_id": ObjectId(contact_id)}, {"$set": updated_contact})
        if result.matched_count == 0:
            raise HTTPException(status_code=404, detail="Contact not found")
        logger.info(f"Contact with ID {contact_id} updated successfully")
        return {"message": "Contact updated successfully"}
    except Exception as e:
        logger.error(f"Error updating contact with ID {contact_id}: {e}")
        raise HTTPException(status_code=500, detail="Error updating contact")

# Delete contact
@app.delete("/contacts/{contact_id}")
def delete_contact(contact_id: str):
    try:
        result = collection.delete_one({"_id": ObjectId(contact_id)})
        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Contact not found")
        logger.info(f"Contact with ID {contact_id} deleted successfully")
        return {"message": "Contact deleted successfully"}
    except Exception as e:
        logger.error(f"Error deleting contact with ID {contact_id}: {e}")
        raise HTTPException(status_code=500, detail="Error deleting contact")

# Application shutdown to close the MongoDB connection
@app.on_event("shutdown")
def shutdown_db_client():
    try:
        client.close()
        logger.info("MongoDB connection closed successfully")
    except Exception as e:
        logger.error(f"Error closing MongoDB connection: {e}")
