# import mysql.connector

# def create_connection():
#     connection = mysql.connector.connect(
#         host="localhost",
#         user="root",
#         password="Kavya@74",
#         database="maternal_care_ai"
#     )
#     return connection



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