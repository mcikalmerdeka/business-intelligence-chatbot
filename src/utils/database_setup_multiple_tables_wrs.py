# Script to create and populate WRS EHR tables in Neon Postgres (wrs schema)
import pandas as pd
import psycopg2
from psycopg2.extras import execute_values
import os
from dotenv import load_dotenv

load_dotenv()

# Step 1: Load the CSV files
base_path = 'datasets/dataset_multiple_tables/wrs_ehr_db/'
facilities      = pd.read_csv(f'{base_path}facilities.csv')
insurance_plans = pd.read_csv(f'{base_path}insurance_plans.csv')
patients        = pd.read_csv(f'{base_path}patients.csv')
providers       = pd.read_csv(f'{base_path}providers.csv')
appointments    = pd.read_csv(f'{base_path}appointments.csv')
diagnoses       = pd.read_csv(f'{base_path}diagnoses.csv')
prescriptions   = pd.read_csv(f'{base_path}prescriptions.csv')
lab_results     = pd.read_csv(f'{base_path}lab_results.csv')

all_df = [facilities, insurance_plans, patients, providers, appointments, diagnoses, prescriptions, lab_results]
all_df = [df.where(pd.notnull(df), None) for df in all_df]

table_names = ["facilities", "insurance_plans", "patients", "providers", "appointments", "diagnoses", "prescriptions", "lab_results"]

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
    cursor.execute("CREATE SCHEMA IF NOT EXISTS wrs;")
    conn.commit()
    print("Schema `wrs` created successfully!")
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
        cursor.execute(f"DROP TABLE IF EXISTS wrs.{table};")
        cursor.execute(f"CREATE TABLE wrs.{table} ({col_defs});")
        conn.commit()
        print(f"Table `wrs.{table}` created successfully!")
    except psycopg2.Error as e:
        conn.rollback()
        print(f"Error creating table `wrs.{table}`: {e}")

# Step 5: Batch insert
for df, table in zip(all_df, table_names):
    rows = [tuple(row) for _, row in df.iterrows()]
    try:
        execute_values(cursor, f"INSERT INTO wrs.{table} VALUES %s", rows, page_size=10000)
        conn.commit()
        print(f"Inserted {len(rows)} rows into `wrs.{table}` successfully!")
    except psycopg2.Error as e:
        conn.rollback()
        print(f"Error inserting into `wrs.{table}`: {e}")

cursor.close()
conn.close()
