import click
import pandas as pd
from sqlalchemy import create_engine
from tqdm.auto import tqdm

@click.command()
@click.option('--pg-user', default='root', help='PostgreSQL user')
@click.option('--pg-pass', default='root', help='PostgreSQL password')
@click.option('--pg-host', default='localhost', help='PostgreSQL host')
@click.option('--pg-port', default=5432, type=int, help='PostgreSQL port')
@click.option('--pg-db', default='ny_taxi', help='PostgreSQL database name')
@click.option('--year', default=2021, type=int, help='Year of the data')
@click.option('--month', default=1, type=int, help='Month of the data')
@click.option('--target-table', default='yellow_taxi_data', help='Target table name')
@click.option('--chunksize', default=100000, type=int, help='Chunk size for reading CSV')
def run(pg_user, pg_pass, pg_host, pg_port, pg_db, year, month, target_table, chunksize):
    
    # Format month to always have two digits (e.g., 1 -> "01", 10 -> "10")
    month_str = f"{month:02d}"
    
    # URL address using parameters
    yellow_taxi_url = f'https://github.com/DataTalksClub/nyc-tlc-data/releases/download/yellow/yellow_tripdata_{year}-{month_str}.csv.gz'
    zones_url = f'https://d37ci6vzurychx.cloudfront.net/misc/taxi_zone_lookup.csv'

    # Define data types
    dtype = {
        "VendorID": "Int64", "passenger_count": "Int64", "trip_distance": "float64",
        "RatecodeID": "Int64", "store_and_fwd_flag": "string", "PULocationID": "Int64",
        "DOLocationID": "Int64", "payment_type": "Int64", "fare_amount": "float64",
        "extra": "float64", "mta_tax": "float64", "tip_amount": "float64",
        "tolls_amount": "float64", "improvement_surcharge": "float64",
        "total_amount": "float64", "congestion_surcharge": "float64"
    }
    parse_dates = ["tpep_pickup_datetime", "tpep_dropoff_datetime"]

    # Create connection using function arguments
    engine = create_engine(f'postgresql://{pg_user}:{pg_pass}@{pg_host}:{pg_port}/{pg_db}')

    # Prepare iterator
    df_iter = pd.read_csv(
        yellow_taxi_url,
        dtype=dtype,
        parse_dates=parse_dates,
        iterator=True,
        chunksize=chunksize
    )

    # Import zone lookup
    print(f'Downloading zone data from {zones_url}...')
    zone_lookup = pd.read_csv(zones_url)
    zone_lookup.columns = [c.lower() for c in zone_lookup.columns]
    zone_lookup.to_sql(name='zones', con=engine, if_exists='replace')
    print('Inserted zone data successfully')

    # First batch and schema
    df = next(df_iter)
    df.head(n=0).to_sql(name=target_table, con=engine, if_exists='replace')

    # Loading loop
    print(f"Loading data to table {target_table} on host {pg_host}...")
    df.to_sql(name=target_table, con=engine, if_exists='append')

    for df_chunk in tqdm(df_iter):
        df_chunk.to_sql(name=target_table, con=engine, if_exists='append')
    
    print("Completed successfully!")

if __name__ == '__main__':
    run()
