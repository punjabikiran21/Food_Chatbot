import os
from typing import List, Dict
import json
from datetime import datetime
import mysql.connector
from mysql.connector import Error
from dotenv import load_dotenv

class OrderDatabase:
    def __init__(self):
        """Initialize MySQL database connection and create database if it doesn't exist"""
        try:
            load_dotenv()

            db_host = os.getenv('DB_HOST')
            db_user = os.getenv('DB_USER')
            db_password = os.getenv('DB_PASSWORD')
            db_port = int(os.getenv('DB_PORT'))
            db_name = os.getenv('DB_NAME')

            self.connection = mysql.connector.connect(
                host=db_host,
                user=db_user, 
                password=db_password,  
                database=db_name,
                port=db_port)

            print(f"Connecting to database: {db_host}, {db_user}, {db_password}, {db_port}, {db_name}")

            # Create database if it doesn't exist
            self._create_database()

            # Create tables
            self.create_tables()
            
        except Error as e:
            print(f"Error connecting to MySQL database: {e}")
            raise

    def _create_database(self):
        try:
            cursor = self.connection.cursor()
            cursor.execute("SHOW DATABASES LIKE 'restaurant_db'")
            result = cursor.fetchone()
            
            if not result:
                cursor.execute("CREATE DATABASE restaurant_db")
                print("Database 'restaurant_db' created successfully")
            
            cursor.close()
            
        except Error as e:
            print(f"Error creating database: {e}")
            raise

    def create_tables(self):
        """Create necessary tables if they don't exist"""
        try:
            cursor = self.connection.cursor()
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS orders (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    items JSON NOT NULL,
                    total_price DECIMAL(10, 2) NOT NULL,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            self.connection.commit()
            
        except Error as e:
            print(f"Error creating tables: {e}")
            raise
        finally:
            cursor.close()

    def save_order(self, items: List[Dict], total_price: float) -> int:
        try:
            cursor = self.connection.cursor()
            
            cursor.execute(
                'INSERT INTO orders (items, total_price, timestamp) VALUES (%s, %s, %s)',
                (json.dumps(items), total_price, datetime.now())
            )
            
            order_id = cursor.lastrowid
            
            self.connection.commit()
            print(f"Order saved successfully with ID: {order_id}")
            return order_id
            
        except Error as e:
            print(f"Error saving order: {e}")
            self.connection.rollback()
            raise
        finally:
            cursor.close()

    def get_best_selling_items(self) -> List[Dict]:
        try:
            cursor = self.connection.cursor(dictionary=True)
            cursor.execute('''
                SELECT 
                    item_name,
                    SUM(quantity) as total_quantity,
                    SUM(total_item_price) as total_revenue
                FROM order_items
                GROUP BY item_name
                ORDER BY total_quantity DESC
                LIMIT 5
            ''')
            return cursor.fetchall()
        except Error as e:
            print(f"Error getting best selling items: {e}")
            raise
        finally:
            cursor.close()

    def get_daily_sales(self) -> List[Dict]:
        try:
            cursor = self.connection.cursor(dictionary=True)
            cursor.execute('''
                SELECT 
                    DATE(timestamp) as date,
                    COUNT(*) as total_orders,
                    SUM(total_price) as total_revenue
                FROM orders
                GROUP BY DATE(timestamp)
                ORDER BY date DESC
                LIMIT 30
            ''')
            return cursor.fetchall()
        except Error as e:
            print(f"Error getting daily sales: {e}")
            raise
        finally:
            cursor.close()

    def __del__(self):
        if hasattr(self, 'connection') and self.connection.is_connected():
            self.connection.close()


if __name__ == "__main__":
    main()