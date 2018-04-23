from dotenv import find_dotenv, load_dotenv
from requests import post
import csv
import hashlib
import logging
import os
import re


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

    logger.info('hashing emails and saving data')
    hashes = {}
    m = hashlib.md5()
    pattern = r'.*@.*\.[a-z]*'
    outfile = os.path.join(project_dir, 'data', 'raw', 'raw.csv')
    with open(outfile, 'w') as fout:
        writer = csv.writer(fout)
        reader = csv.reader(data)
        for row in reader:
            for index, col in enumerate(row):
                if col != '' and re.match(pattern, col):
                    if not col in hashes:
                        m.update(col.encode('utf-8'))
                        hashes[col] = m.hexdigest()
                    row[index] = hashes[col]
            writer.writerow(row)


if __name__ == "__main__":
    log_fmt = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    logging.basicConfig(level=logging.INFO, format=log_fmt)

    # store the project dir as a variable
    project_dir = os.path.join(os.path.dirname(__file__), os.pardir, os.pardir)

    # find .env automagically by walking up directories until it's found, then
    # load up the .env entries as environment variables
    load_dotenv(find_dotenv())

    main()
