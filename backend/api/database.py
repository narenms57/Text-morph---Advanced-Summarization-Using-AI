import mysql.connector
from mysql.connector import Error
from dotenv import load_dotenv
import os

load_dotenv()  # Loads .env file variables into environment
print(f"DB_USER={os.getenv('DB_USER')}")
print(f"DB_PASSWORD={'***' if os.getenv('DB_PASSWORD') else 'NOT SET'}")



#tables needed:
    #login_history
    #profiles
    #user_feedback
    #user_texts
    #users


def create_connection():
    try:
        # Establish connection using environment variables for security
        connection = mysql.connector.connect(
            host=os.getenv("DB_HOST"),
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD"),
            database=os.getenv("DB_NAME"),
            port=3306,
            use_pure=True
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



def update_text_in_db(record_id, new_content):
    connection = create_connection()
    if connection:
        cursor = connection.cursor()
        cursor.execute("UPDATE user_texts SET content_text = %s WHERE id = %s", (new_content, record_id))
        connection.commit()
        cursor.close()
        connection.close()

def delete_text_in_db(record_id):
    connection = create_connection()
    if connection:
        cursor = connection.cursor()
        cursor.execute("DELETE FROM user_texts WHERE id = %s", (record_id,))
        connection.commit()
        cursor.close()
        connection.close()



# ------------------ New code for storing summaries and paraphrases ------------------

def create_user_texts_table():
    """
    Create a table to hold generated user texts (summary/paraphrase) linked to users.
    Call this once at app setup or migration step.
    """
    connection = create_connection()
    if connection:
        try:
            cursor = connection.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS user_texts (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    user_id INT NOT NULL,
                    input_text TEXT NOT NULL,
                    content_text TEXT NOT NULL,
                    content_type VARCHAR(20) NOT NULL,  -- 'summary' or 'paraphrase'
                    model_used VARCHAR(100), --model name
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(id)
                )
            """)
            connection.commit()
            print("user_texts table is ready.")
        except Error as e:
            print(f"Error creating user_texts table: {e}")
        finally:
            cursor.close()
            connection.close()


def save_generated_text(user_id: int, content_text: str, content_type: str, input_text: str, model_used: str) :
    """
    Save generated text (summary or paraphrase) linked to a user.
    content_type should be 'summary' or 'paraphrase'.
    """
    connection = create_connection()
    if connection:
        try:
            cursor = connection.cursor()
            cursor.execute("""
                INSERT INTO user_texts (user_id, content_text, content_type, input_text, model_used)
                VALUES (%s, %s, %s, %s, %s)
            """, (user_id, content_text, content_type, input_text, model_used))
            connection.commit()
            return True
        except Error as e:
            print(f"Error saving generated text: {e}")
            return False
        finally:
            cursor.close()
            connection.close()
    else:
        print("Unable to connect to DB, save_generated_text failed.")
        return False

# ------------------ End of new code ------------------
def create_user_feedback_table():
    """
    Create the user_feedback table.
    Run this once during app initialization or migration.
    """
    connection = create_connection()
    if connection:
        try:
            cursor = connection.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS user_feedback (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    user_id INT NOT NULL,
                    feedback_type ENUM('like', 'dislike') NOT NULL,
                    comment TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
                )
            """)
            connection.commit()
            print("user_feedback table is ready.")
        except Error as e:
            print(f"Error creating user_feedback table: {e}")
        finally:
            cursor.close()
            connection.close()

def save_user_feedback(user_id: int, feedback_type: str, comment: str) -> bool:
    try:
        conn = create_connection()
        cursor = conn.cursor()
        sql = """
        INSERT INTO user_feedback (user_id, feedback_type, comment)
        VALUES (%s, %s, %s)
        """
        cursor.execute(sql, (user_id, feedback_type, comment))
        conn.commit()
        cursor.close()
        conn.close()
        return True
    except Error as e:
        print(f"Failed to save feedback: {e}")
        return False
    

def create_login_history_table():
    """
    Create the login_history table to store user login events.
    Call this once at app setup or migration.
    """
    connection = create_connection()
    if connection:
        try:
            cursor = connection.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS login_history (
                    id INT PRIMARY KEY AUTO_INCREMENT,
                    user_id INT,
                    login_time DATETIME,
                    FOREIGN KEY (user_id) REFERENCES users(id)
                )
            """)
            connection.commit()
            print("login_history table is ready.")
        except Error as e:
            print(f"Error creating login_history table: {e}")
        finally:
            cursor.close()
            connection.close()



def update_user_role(user_id: int, new_role: str) -> bool:
    """
    Update a user's role to 'admin' or 'user'.
    """
    connection = create_connection()
    if connection:
        try:
            cursor = connection.cursor()
            cursor.execute("UPDATE users SET role = %s WHERE id = %s", (new_role, user_id))
            connection.commit()
            cursor.close()
            connection.close()
            return True
        except Error as e:
            print(f"Failed to update user role: {e}")
            return False
    return False


def record_login(user_id):
    connection = create_connection()
    if connection:
        cursor = connection.cursor()
        cursor.execute(
            "INSERT INTO login_history (user_id, login_time) VALUES (%s, NOW())", (user_id,)
        )
        connection.commit()
        cursor.close()
        connection.close()



def delete_user(user_id):
    conn = create_connection()
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute("START TRANSACTION;")

            cursor.execute("DELETE FROM login_history WHERE user_id = %s", (user_id,))
            cursor.execute("DELETE FROM profiles WHERE user_id = %s", (user_id,))
            cursor.execute("DELETE FROM user_feedback WHERE user_id = %s", (user_id,))
            cursor.execute("DELETE FROM user_texts WHERE user_id = %s", (user_id,))
            cursor.execute("DELETE FROM users WHERE id = %s", (user_id,))

            cursor.execute("COMMIT;")
            cursor.close()
            conn.close()
            return True
        except Error as e:
            cursor.execute("ROLLBACK;")
            print(f"Failed to delete user and dependencies: {e}")
            return False
    return False






def fetch_user_texts_by_id(user_id: int):
    connection = create_connection()
    results = []
    if connection:
        try:
            cursor = connection.cursor(dictionary=True)
            cursor.execute("""
                SELECT input_text, content_text, content_type, model_used, created_at
                FROM user_texts
                WHERE user_id = %s
                ORDER BY created_at DESC
            """, (user_id,))
            results = cursor.fetchall()
        except Error as e:
            print(f"Database error: {e}")
        finally:
            cursor.close()
            connection.close()
    return results



# For debugging when running the file directly
if __name__ == "__main__":
    # You can create the user_texts table by uncommenting the below line:
    # create_user_texts_table()

    users = fetch_all_users()
    print(users)  # Print fetched users or empty list if error occured
