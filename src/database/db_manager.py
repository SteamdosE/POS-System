import mysql.connector
from mysql.connector import Error

class DatabaseManager:
    def __init__(self, host, user, password, database):
        self.host = host
        self.user = user
        self.password = password
        self.database = database
        self.connection = None

    def create_connection(self):
        """ Create a database connection to a MySQL database """
        try:
            self.connection = mysql.connector.connect(
                host=self.host,
                user=self.user,
                password=self.password,
                database=self.database
            )
            if self.connection.is_connected():
                print("Connection to MySQL DB successful")
        except Error as e:
            print(f"Error: '{e}'")

    def close_connection(self):
        """ Close the database connection """
        if self.connection.is_connected():
            self.connection.close()
            print("Connection to MySQL DB closed")

    def execute_query(self, query):
        """ Execute a single query """
        cursor = self.connection.cursor()
        try:
            cursor.execute(query)
            self.connection.commit()
            print("Query executed successfully")
        except Error as e:
            print(f"Error: '{e}'")

    def fetch_query(self, query):
        """ Fetch results from a query """
        cursor = self.connection.cursor()
        cursor.execute(query)
        return cursor.fetchall()
