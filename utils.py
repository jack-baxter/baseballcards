#Jack Baxter 
#util functions for loading API keys and env variables 

#load 
#dotenv looks for env file and reads keys
from dotenv import load_dotenv
#os for python operating system 
import os

#helper function to load API keys 
def load_env():
    """Load environment variables from .env"""
    load_dotenv()
    #confirm 
    if load_dotenv():
        print('environment loaded')
    else: 
        print('no environment file found')

#function to get API keys from env 
def get_api_keys(key_name: str) -> str:
    """Safely get API keys from environment variables"""
    #gets key
    value = os.getenv(key_name)
    #checks if key exists
    if value is None:
        raise ValueError(f"Warning:  {key_name} not found in environment variables")
    return value