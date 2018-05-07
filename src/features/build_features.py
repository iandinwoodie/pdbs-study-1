import logging
import os
import sqlite3
import pandas as pd
import scipy.stats as scs


def get_data_file():
    """Verify that the input data file exits."""
    if os.path.isfile(processed_filepath):
        return processed_filepath
    else:
        print('Error: no scrubbable data file exists.')
        quit()


class Database(object):

    def __init__(self, path):
        """Initialize a Database object."""
        self.__conn = sqlite3.connect(path)
        self.__cursor = self.__conn.cursor()

    def close(self):
        """Terminate the connection to the database."""
        self.__conn.close()

    def commit(self):
        """Commit changes to the database."""
        self.__conn.commit()

    def select(self, table, fields, qualifications=''):
        """Return the data for the provided criteria."""
        query = 'SELECT %s FROM %s %s;' %(fields, table, qualifications)
        df = pd.read_sql_query(query, self.__conn)
        return df


class Manager(object):

    def __init__(self, path):
        """Initialize a Manager object."""
        self.__db = Database(processed_filepath)
        self.__path = path

    def __del__(self):
        """Destructor for the Manager object."""
        self.__db.close()

    def first_investigation(self):
        """Perform first investigation analysis."""
        ## Get relevant data.
        table = 'dogs'
        # q04_1 = thunderstorm phobia
        # q04_2 = noise phobia
        # q04_9 = separation anxiety
        fields = 'q04_1, q04_2, q04_9'
        df = self.__db.select(table, fields)
        df.columns = ['thunder', 'noise', 'anxiety']
        df['thunder'] = pd.to_numeric(df['thunder'])
        df['noise'] = pd.to_numeric(df['noise'])
        df['anxiety'] = pd.to_numeric(df['anxiety'])
        ## Determine relationships.
        print('First Investigation:')
        print('Modes:')
        print(df.mode())
        print('')
        pairs = [
            ['thunder', 'noise'],
            ['thunder', 'anxiety'],
            ['noise', 'anxiety']
            ]
        for pair in pairs:
            print('Chi2 Contingency: %s - %s'
                  %(pair[0], pair[1]))
            contingency = pd.crosstab(df[pair[0]], df[pair[1]])
            print(scs.chi2_contingency(contingency))
            print('')

    def second_investigation(self):
        """Perform second investigation analysis."""
        ## Get relevant data.
        table = 'dogs'
        # q02_main_2 = fearful/anxious behavior
        # q02_main_3 = repetitive behavior
        fields = 'q02_main_2, q02_main_3'
        df = self.__db.select(table, fields)
        df.columns = ['anxious', 'repetitive']
        df['anxious'] = pd.to_numeric(df['anxious'])
        df['repetitive'] = pd.to_numeric(df['repetitive'])
        ## Determine relationships.
        print('Second Investigation:')
        print('Modes:')
        print(df.mode())
        print('')
        print('Chi2 Contingency: anxious - repetitive')
        contingency = pd.crosstab(df['anxious'], df['repetitive'])
        print(scs.chi2_contingency(contingency))
        print('')


def main():
    """
    Runs feature processing scripts to analuze the cleaned data from
    (../processed).
    """
    logger = logging.getLogger(__name__)

    manager = Manager(get_data_file())
    manager.first_investigation()
    manager.second_investigation()

    logger.info('dataset generation complete')


if __name__ == '__main__':
    log_fmt = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    logging.basicConfig(level=logging.INFO, format=log_fmt)

    # store necessary paths
    project_dir = os.path.join(os.path.dirname(__file__), os.pardir, os.pardir)
    data_dir = os.path.join(project_dir, 'data')
    processed_filepath = os.path.join(data_dir, 'processed', 'processed.db')

    main()
