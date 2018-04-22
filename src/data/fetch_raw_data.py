from dotenv import find_dotenv, load_dotenv
from requests import post
import logging
import os
import json


def main():
    database_url = os.environ.get("DATABASE_URL")
    api_token = os.environ.get("API_TOKEN")
    payload = {
        'token': api_token,
        'format': 'json',
        'content': 'record'
        }
    logger = logging.getLogger(__name__)
    logger.info('fetching raw data from database')
    response = post(database_url, data=payload)
    logger.info('saving data to file')
    data = response.json()
    with open('raw.json', 'w') as fout:
        json.dump(data, fout)


if __name__ == "__main__":
    log_fmt = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    logging.basicConfig(level=logging.INFO, format=log_fmt)

    # find .env automagically by walking up directories until it's found, then
    # load up the .env entries as environment variables
    load_dotenv(find_dotenv())

    main()
