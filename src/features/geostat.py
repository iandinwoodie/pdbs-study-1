import logging
import os
import sqlite3
import pandas as pd
import re
import urllib
import json

API_URL = 'http://api.zippopotam.us/'


def get_study_database():
    """Verify that the study database exists."""
    if os.path.isfile(processed_filepath):
        return processed_filepath
    else:
        print('Error: study database does not exist.')
        quit()


class Database(object):
    def __init__(self, path):
        """Initialize a Database object."""
        self.__conn = sqlite3.connect(path)
        self.__cursor = self.__conn.cursor()

    def __del__(self):
        """Destructor for the Database object."""
        self.close()

    def close(self):
        """Terminate the connection to the database."""
        self.__conn.close()

    def get_connection(self):
        """Get the connection to the database."""
        return self.__conn


class Extractor(object):

    def __init__(self, path):
        """Initialize an Extractor object."""
        self.__db = Database(path)
        self.__df = pd.DataFrame()
        self.__postal_dict = {}

    def populate_dataframe(self):
        self.__df = pd.read_sql_query("select zip_code from users;",
                                      self.__db.get_connection())

    def translate_zip_codes(self):
        self.__df['translation'] = self.__df['zip_code'].apply(
                self.__translate_zip_code)

    def print_geo_stats(self):
        #print(self.__df['translation'].value_counts())
        df = pd.DataFrame(self.__df['translation'].value_counts())
        df.rename(columns={'translation':'count'}, inplace=True)
        df = df.rename_axis('country', axis=1)
        print('')
        print(df)
        print('')

    def __get_postal_country(self, zip_code):
        if zip_code != 'N/A':
            # US, Germany, Mexico, Dominican Republic, Spain, Finland, France,
            # Italy
            if re.match(r'^[0-9]{5}(\-[0-9]{4}){,1}$', zip_code):
                codes = ['us', 'de', 'mx', 'do', 'es', 'fi', 'fr', 'it']
            # Canada
            elif re.match(r'^([A-Z][0-9]){3}$', zip_code):
                codes = ['ca']
            # UK
            elif re.match(r'^[A-Z]{1,2}[0-9]{1,3}[A-Z]{0,2}$', zip_code):
                codes = ['gb']
            # Australia, Belgium, Austria, Argentina, Bangladesh, Bulgaria,
            # Switzerland, Denmark
            elif re.match(r'^[0-9]{4}$', zip_code):
                codes = ['au', 'be', 'at', 'ar', 'bd', 'bg', 'ch', 'dk']
            # Russia, India
            elif re.match(r'^[0-9]{6}$', zip_code):
                codes = ['ru', 'in']
            # Poland
            elif re.match(r'^[0-9]{2}\-{1}[0-9]{3}$', zip_code):
                codes = ['pl']
            # Portugal
            elif re.match(r'^[0-9]{4}\-{1}[0-9]{3}$', zip_code):
                codes = ['pt']
            else:
                codes = []
        return codes

    def __reformat_postal_code(self, zip_code, codes):
        if 'ca' in codes: zip_code = zip_code[:3]
        elif 'gb' in codes: zip_code = zip_code[:3]
        elif 'us' in codes: zip_code = zip_code[:5]
        return zip_code

    def __translate_zip_code(self, zip_code):
        translation=''
        # Remove whitespace and homogenize type case.
        zip_code = zip_code.replace(' ', '').upper()
        codes = self.__get_postal_country(zip_code)
        zip_code = self.__reformat_postal_code(zip_code, codes)
        # Attempt to translate locally.
        if zip_code in self.__postal_dict:
            return self.__postal_dict[zip_code]
        # Attempt to translate remotely.
        info_found = False
        for code in codes:
            url = API_URL + code + '/' + zip_code
            try:
                with urllib.request.urlopen(url) as response:
                    data = json.loads(response.read())
                    if 'country' in data:
                        info_found = True
                        translation = data['country']
                        break
            except:
                pass
        if not info_found:
            if not zip_code:
                translation = 'Not Provided'
            else:
                translation = 'Not Identified'
        self.__postal_dict[zip_code] = translation
        return translation


def main():
    logger = logging.getLogger(__name__)
    logger.info('connecting to database')
    db = Database(get_study_database())
    logger.info('extracting postal data')
    extractor = Extractor(get_study_database())
    extractor.populate_dataframe()
    logger.info('translating postal codes')
    extractor.translate_zip_codes()
    extractor.print_geo_stats()
    logger.info('execution complete')


if __name__ == "__main__":
    log_fmt = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    logging.basicConfig(level=logging.INFO, format=log_fmt)
    project_dir = os.path.join(os.path.dirname(__file__), os.pardir, os.pardir)
    data_dir = os.path.join(project_dir, 'data')
    processed_filepath = os.path.join(data_dir, 'processed', 'processed.db')
    main()
