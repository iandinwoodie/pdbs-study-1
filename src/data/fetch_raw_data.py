from dotenv import find_dotenv, load_dotenv
from requests import post
import logging
import os


def main():
    database_url = os.environ.get("DATABASE_URL")
    api_token = os.environ.get("API_TOKEN")
    print(api_token)

    payload = {
        'token': api_token,
        'format': 'json',
        'content': 'record'
        }

    response = post(database_url, data=payload)
    print (response.status_code)

    data = response.json()
    logger = logging.getLogger(__name__)
    logger.info('fetching raw data from database')


if __name__ == "__main__":
    log_fmt = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    logging.basicConfig(level=logging.INFO, format=log_fmt)

    # find .env automagically by walking up directories until it's found, then
    # load up the .env entries as environment variables
    load_dotenv(find_dotenv())

    main()
