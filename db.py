import mysql.connector

def get_db_connection():
    conn = mysql.connector.connect(
        host="localhost",
        user="fprms_user",        # change if needed
        password="fprms_pass",    # change if needed
        database="fprms"
    )
    return conn
