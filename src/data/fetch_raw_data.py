from dotenv import find_dotenv, load_dotenv
from requests import post
import csv
import logging
import os


def main():
    """Fetching the raw data from REDCap."""
    logger = logging.getLogger(__name__)

    logger.info('fetching raw data from database')
    database_url = os.environ.get("DATABASE_URL")
    api_token = os.environ.get("API_TOKEN")
    payload = {
        'token': api_token,
        'format': 'csv',
        'content': 'record'
        }
    response = post(database_url, data=payload)
    data = response.text.splitlines()

    logger.info('saving data to file')
    with open('raw.csv', 'w') as fout:
        writer = csv.writer(fout)
        reader = csv.reader(data)
        for row in reader:
            writer.writerow(row)


if __name__ == "__main__":
    log_fmt = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    logging.basicConfig(level=logging.INFO, format=log_fmt)

    # find .env automagically by walking up directories until it's found, then
    # load up the .env entries as environment variables
    load_dotenv(find_dotenv())

    main()
