import mysql.connector
from mysql.connector import Error
from dotenv import load_dotenv
import os

load_dotenv()  # Loads .env file variables into environment

def create_connection():
    try:
        # Establish connection using environment variables for security
        connection = mysql.connector.connect(
            host=os.getenv("DB_HOST"),
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD"),
            database=os.getenv("DB_NAME")
        )
        if connection.is_connected():
            return connection  # Return open connection for query functions
    except Error as e:
        # Better to print or log error so you know why connection failed
        print(f"Error connecting to MySQL: {e}")
        return None  # Return None explicitly if connection fails

def fetch_all_users():
    connection = create_connection()
    if connection:
        cursor = connection.cursor(dictionary=True)  # Use dictionary=True for easier data handling
        try:
            cursor.execute("SELECT * FROM users")  # Execute a SELECT query
            users = cursor.fetchall()  # Fetch all rows
            return users  # Return data to caller
        except Error as e:
            print(f"Error fetching users: {e}")
            return []  # Return empty list on failure
        finally:
            cursor.close()  # Always close cursor to free resources
            connection.close()  # Close DB connection
    else:
        return []  # No connection, return empty list
    
def update_user_password(email: str, hashed_password: str):
    conn = create_connection()
    if not conn:
        return False
    try:
        cursor = conn.cursor()
        query = "UPDATE users SET hashed_password = %s WHERE email = %s"
        cursor.execute(query, (hashed_password, email))
        conn.commit()
        affected = cursor.rowcount
        cursor.close()
        conn.close()
        return affected > 0
    except Error as e:
        print(f"MySQL error: {e}")
        return False

def close_connection(connection):
    if connection and connection.is_connected():
        connection.close()  # Graceful connection closing

# For debugging when running the file directly
if __name__ == "__main__":
    users = fetch_all_users()
    print(users)  # Print fetched users or empty list if error occured
