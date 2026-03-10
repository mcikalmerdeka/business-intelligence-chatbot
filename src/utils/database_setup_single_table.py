# Script to create and populate the sales.sales table in Neon Postgres
import pandas as pd
import psycopg2
from psycopg2.extras import execute_values
import os
from dotenv import load_dotenv

load_dotenv()

# Step 1: Load the CSV file
csv_file = "datasets/dataset_single_table/sales_data_sample.csv"
df = pd.read_csv(csv_file, encoding='ISO-8859-1')
df = df.where(pd.notnull(df), None)

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

# Step 4: Create schema and table
schema = ", ".join([
    f"{col} {map_dtype_to_sql(dtype)}"
    for col, dtype in zip(df.columns, df.dtypes)
])

try:
    cursor.execute("CREATE SCHEMA IF NOT EXISTS sales;")
    # Clean up any table previously created in public schema
    cursor.execute("DROP TABLE IF EXISTS public.sales;")
    cursor.execute("DROP TABLE IF EXISTS sales.sales;")
    cursor.execute(f"CREATE TABLE sales.sales ({schema});")
    conn.commit()
    print("Schema `sales` and table `sales.sales` created successfully!")
except psycopg2.Error as e:
    conn.rollback()
    print(f"Error creating schema/table: {e}")
    exit()

# Step 5: Batch insert
rows = [tuple(row) for _, row in df.iterrows()]
try:
    execute_values(cursor, "INSERT INTO sales.sales VALUES %s", rows, page_size=10000)
    conn.commit()
    print(f"Inserted {len(rows)} rows into `sales.sales` successfully!")
except psycopg2.Error as e:
    conn.rollback()
    print(f"Error inserting data: {e}")

cursor.close()
conn.close()
