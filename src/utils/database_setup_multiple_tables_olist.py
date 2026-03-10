# Script to create and populate Olist e-commerce tables in Neon Postgres (olist schema)
import pandas as pd
import psycopg2
from psycopg2.extras import execute_values
import os
from dotenv import load_dotenv

load_dotenv()

# Step 1: Load the CSV files
base_path = 'datasets/dataset_multiple_tables/olist_db/'
customers      = pd.read_csv(f'{base_path}customers_dataset.csv')
geolocation    = pd.read_csv(f'{base_path}geolocation_dataset.csv')
order_items    = pd.read_csv(f'{base_path}order_items_dataset.csv')
order_payments = pd.read_csv(f'{base_path}order_payments_dataset.csv')
order_reviews  = pd.read_csv(f'{base_path}order_reviews_dataset.csv')
orders         = pd.read_csv(f'{base_path}orders_dataset.csv')
products       = pd.read_csv(f'{base_path}product_dataset.csv', index_col=0)
sellers        = pd.read_csv(f'{base_path}sellers_dataset.csv')

all_df = [customers, geolocation, order_items, order_payments, order_reviews, orders, products, sellers]
all_df = [df.where(pd.notnull(df), None) for df in all_df]

table_names = ["customers", "geolocation", "order_items", "order_payments", "order_reviews", "orders", "products", "sellers"]

# Step 2: Connect to Neon via DATABASE_URL
try:
    conn = psycopg2.connect(os.getenv("DATABASE_URL"))
    cursor = conn.cursor()
    print("Connected to Neon Postgres successfully!")
except psycopg2.Error as e:
    print(f"Error connecting to Neon: {e}")
    exit()

# Step 3: Map Pandas dtypes to PostgreSQL types
def map_dtype_to_sql(dtype):
    if pd.api.types.is_integer_dtype(dtype):
        return "INT"
    elif pd.api.types.is_float_dtype(dtype):
        return "FLOAT"
    elif pd.api.types.is_bool_dtype(dtype):
        return "BOOLEAN"
    elif pd.api.types.is_datetime64_any_dtype(dtype):
        return "TIMESTAMP"
    else:
        return "VARCHAR(255)"

# Step 4: Create schema and tables
try:
    cursor.execute("CREATE SCHEMA IF NOT EXISTS olist;")
    conn.commit()
    print("Schema `olist` created successfully!")
except psycopg2.Error as e:
    conn.rollback()
    print(f"Error creating schema: {e}")
    exit()

for df, table in zip(all_df, table_names):
    col_defs = ", ".join([
        f"{col} {map_dtype_to_sql(dtype)}"
        for col, dtype in zip(df.columns, df.dtypes)
    ])
    try:
        cursor.execute(f"DROP TABLE IF EXISTS olist.{table};")
        cursor.execute(f"CREATE TABLE olist.{table} ({col_defs});")
        conn.commit()
        print(f"Table `olist.{table}` created successfully!")
    except psycopg2.Error as e:
        conn.rollback()
        print(f"Error creating table `olist.{table}`: {e}")

# Step 5: Batch insert with large page_size to minimize round-trips
for df, table in zip(all_df, table_names):
    rows = [tuple(row) for _, row in df.iterrows()]
    total = len(rows)
    try:
        execute_values(
            cursor,
            f"INSERT INTO olist.{table} VALUES %s",
            rows,
            page_size=10000
        )
        conn.commit()
        print(f"Inserted {total} rows into `olist.{table}` successfully!")
    except psycopg2.Error as e:
        conn.rollback()
        print(f"Error inserting into `olist.{table}`: {e}")

cursor.close()
conn.close()
