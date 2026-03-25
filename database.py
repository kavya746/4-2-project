import mysql.connector
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def create_connection():
    connection = mysql.connector.connect(
        host=os.getenv("DB_HOST"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        database=os.getenv("DB_NAME")
    )
    return connection
