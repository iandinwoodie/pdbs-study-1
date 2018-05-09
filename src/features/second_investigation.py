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
        print('\nSecond Investigation:')
        print('The Relationship Between Anxiety and Compulsion')
        print('\nSums:')
        for index, row in df.sum().iteritems():
            print('%s = %d' %(index,row))
        print('\nModes:')
        for index, row in df.mode().iteritems():
            print('%s = %d' %(index,row))
        print('\nContingency Table:')
        contingency = pd.crosstab(df['anxious'], df['repetitive'])
        print(contingency)
        print('\nProbabilities:')
        for index, row in contingency.iterrows():
            for index2, row2 in row.iteritems():
                prob = row2/5017
                print('%s: %d, %s: %d, P = %.3f'
                      %(contingency.axes[0].name, index, row.axes[0].name,
                        index2, prob))
        c, p, dof, expected = scs.chi2_contingency(contingency,
                                                   correction=False)
        print('\nChi-square Test of Independence:')
        print('chi2 = %f, p = %.2E, dof = %d' %(c, p, dof))
        print('')


def main():
    """
    Runs feature processing scripts to analuze the cleaned data from
    (../processed).
    """
    manager = Manager(get_data_file())
    manager.second_investigation()


if __name__ == '__main__':
    # store necessary paths
    project_dir = os.path.join(os.path.dirname(__file__), os.pardir, os.pardir)
    data_dir = os.path.join(project_dir, 'data')
    processed_filepath = os.path.join(data_dir, 'processed', 'processed.db')

    main()
