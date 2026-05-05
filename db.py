import mysql.connector
import os

def get_db_connection():
    print("HOST:", os.getenv("MYSQLHOST"))
    print("PORT:", os.getenv("MYSQLPORT"))

    return mysql.connector.connect(
        host=os.getenv("MYSQLHOST"),
        user=os.getenv("MYSQLUSER"),
        password=os.getenv("MYSQLPASSWORD"),
        database=os.getenv("MYSQLDATABASE"),
        port=int(os.getenv("MYSQLPORT", 3306))
    )