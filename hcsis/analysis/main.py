import pandas as pd
from pathlib import Path

def main():
    pandas_settings()
    df = load()
    keyword = "dead"
    df = df[df["non_compliance_area"].str.contains(keyword, na=False)]
    df = df["non_compliance_area"]
    print(df)
    df.to_csv(f"./analyzed_data/{keyword}.csv")


def pandas_settings():
    pd.set_option("display.max_columns", 40)
    pd.set_option("display.width", 3000)
    pd.set_option("display.max_rows", 2000)

def load():
    data_dir = Path("../scraped_data/")
    data_file_path = list(data_dir.glob('*.csv'))[0]  # get first csv in dir
    df = pd.read_csv(data_file_path, dtype={'provider_id': 'object', 'service_location_id': 'object'})
    return df



if __name__ == '__main__':
    main()