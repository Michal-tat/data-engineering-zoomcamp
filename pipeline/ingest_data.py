import pandas as pd
from sqlalchemy import create_engine
from tqdm.auto import tqdm

def run():
    # 1. Parametry połączenia i pliku
    user = 'root'
    password = 'root'
    host = 'localhost'
    port = 5432
    db = 'ny_taxi'
    table_name = 'yellow_taxi_data'
    
    year = 2021
    month = "01" # jako string, żeby zachować zero w "01"
    
    # Adres URL z użyciem f-string (zwróć uwagę na 'f' przed cudzysłowem)
    url = f'https://github.com/DataTalksClub/nyc-tlc-data/releases/download/yellow/yellow_tripdata_{year}-{month}.csv.gz'

    # 2. Definicja typów danych
    dtype = {
        "VendorID": "Int64",
        "passenger_count": "Int64",
        "trip_distance": "float64",
        "RatecodeID": "Int64",
        "store_and_fwd_flag": "string",
        "PULocationID": "Int64",
        "DOLocationID": "Int64",
        "payment_type": "Int64",
        "fare_amount": "float64",
        "extra": "float64",
        "mta_tax": "float64",
        "tip_amount": "float64",
        "tolls_amount": "float64",
        "improvement_surcharge": "float64",
        "total_amount": "float64",
        "congestion_surcharge": "float64"
    }
    parse_dates = ["tpep_pickup_datetime", "tpep_dropoff_datetime"]

    # 3. Tworzenie połączenia z bazą
    engine = create_engine(f'postgresql://{user}:{password}@{host}:{port}/{db}')

    # 4. Przygotowanie iteratora (wczytujemy paczkami po 100 000 wierszy)
    df_iter = pd.read_csv(
        url,
        dtype=dtype,
        parse_dates=parse_dates,
        iterator=True,
        chunksize=100000
    )

    # 5. Pobieramy pierwszą paczkę, aby stworzyć strukturę tabeli
    df = next(df_iter)
    
    # 'replace' usunie tabelę jeśli istniała i stworzy nową z samym nagłówkiem
    df.head(n=0).to_sql(name=table_name, con=engine, if_exists='replace')

    # 6. Pętla ładująca dane
    print(f"Rozpoczynam ładowanie danych do tabeli {table_name}...")
    
    # Ładujemy pierwszą paczkę (tę już pobraną)
    df.to_sql(name=table_name, con=engine, if_exists='append')

    # Ładujemy resztę w pętli
    for df_chunk in tqdm(df_iter):
        df_chunk.to_sql(name=table_name, con=engine, if_exists='append')
    
    print("Zakończono sukcesem!")

if __name__ == '__main__':
    run()