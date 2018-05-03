import csv
import logging
import os
import re
import shutil
import sqlite3


def get_data_file():
    """Verify the input data file."""
    if os.path.isfile(raw_path):
        return raw_path
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

    def get_count(self, table, modifiers=''):
        """Return the record count for the provided table."""
        query = 'SELECT COUNT(*) FROM %s %s;' %(table, modifiers)
        print(query)
        self.__cursor.execute(query)
        return self.__cursor.fetchone()[0]

    def create_table(self, table, header):
        """Create a table in the database."""
        fields = ' text, '.join(header)
        query = 'CREATE TABLE %s (%s);' %(table, fields)
        self.__cursor.execute(query)

    def insert_record(self, table, record):
        """Insert record into the database table."""
        placeholder = '?'
        placeholders = ', '.join(placeholder * len(record))
        query = 'INSERT INTO %s VALUES (%s);' %(table, placeholders)
        self.__cursor.execute(query, record)


class Manager(object):

    def __init__(self, path):
        """Initialize a Manager object."""
        self.__db = Database(db_path)
        self.__path = path
        self.__headers = {}
        self.__parse_headers()
        self.__data = {}
        self.__parse_data()
        self.__create_tables()
        self.__populate_tables()

    def __del__(self):
        """Destructor for the Manager object."""
        self.__db.close()

    def __parse_headers(self):
        """Parse headers from the data file."""
        with open(self.__path, 'r') as fin:
            for row in csv.reader(fin, delimiter=','):
                self.__headers['users'] = row[0:11]
                self.__headers['dogs'] = row[11:146]
                self.__headers['feedback'] = row[685:689]
                break
        # Add the record_id field to all headers
        self.__headers['dogs'].insert(0, self.__headers['users'][0])
        self.__headers['feedback'].insert(0, self.__headers['users'][0])
        # Remove clutter to improve field readability
        for key, value in self.__headers.items():
            h = value
            for i in range(len(h)):
                h[i] = re.sub('_1[a-e]', '', h[i])
                h[i] = re.sub('___', '_', h[i])

    def __parse_data(self):
        """Parse data from the data file."""
        datastore = Datastore()
        with open(self.__path, 'r') as fin:
            for row in csv.reader(fin, delimiter=','):
                datastore.add_entry(row)
        self.__data = datastore.get_users()

    def __create_tables(self):
        """Generate tables with the generated headers."""
        self.__db.create_table('users', self.__headers['users'])
        self.__db.create_table('dogs', self.__headers['dogs'])
        self.__db.create_table('feedback', self.__headers['feedback'])

    def __populate_tables(self):
        """Populate the generated tables with the raw data."""
        for user, user_entry in self.__data.items():
            self.__db.insert_record('users', user_entry.get_user_info())
            self.__db.insert_record('feedback', user_entry.get_feedback())
            dog_entries = user_entry.get_dogs()
            for dog_entry in dog_entries:
                self.__db.insert_record('dogs', dog_entry.get_data())
        self.__db.commit()

    def display_metrics(self):
        """Display the database metrics."""
        print('users:')
        print('  - total: %d' %self.__db.get_count('users'))
        mod = 'WHERE phase_1_welcome_complete="0"'
        print('  - invalid: %d' %self.__db.get_count('users', mod))
        join = 'JOIN feedback ON users.record_id=feedback.record_id'
        mod = '%s WHERE phase_1_feedback_complete="2"' %join
        print('  - complete: %d' %self.__db.get_count('users', mod))
        print('dogs:')
        print('  - total: %d' %self.__db.get_count('dogs'))


class DogEntry(object):

    def __init__(self, uid, data):
        """Initialize a DogEntry object."""
        self.__name = data[0]
        self.__data = data
        self.__verify_data()
        self.__data.insert(0, uid)

    def __verify_data(self):
        """Verify the recorded dog entry data."""
        if len(self.__data) < 135:
            self.__data.insert(133, 0)

    def get_name(self):
        """Return the dog name."""
        return self.__name

    def get_data(self):
        """Return the dog data."""
        return self.__data


class UserEntry(object):

    def __init__(self, uid, data):
        """Initialize a UserEntry object."""
        # demographic status: 10, feedback status: 688 
        # incomplete: row[10]=0, partial: row[688]=0
        self.__uid = uid
        self.__user = data[8]
        self.__user_info = [uid] + data[1:11] # indices replaced with uid
        self.__feedback = [uid] + data[685:689]
        self.__dogs = []
        self.__update_dogs(data)

    def __update_dogs(self, data):
        """Update dog data for the user."""
        dog_cols = [
            {'start': 11, 'end': 146},
            {'start': 146, 'end': 281},
            {'start': 281, 'end': 416},
            {'start': 416, 'end': 551},
            {'start': 551, 'end': 685}
            ]
        for entry in dog_cols:
            replacement = False
            if data[entry['end']-1] == '2': # only record complete dog entries
                dog_data = data[entry['start']:entry['end']]
                for counter, dog in enumerate(self.__dogs):
                    if dog.get_name().lower() == dog_data[0].lower():
                        # Update existing data with newest complete submission.
                        self.__dogs[counter] = DogEntry(self.__uid, dog_data)
                        replacement = True
                        break
                if not replacement:
                    # If an entry for the dog does not exist, create one.
                    self.__dogs.append(DogEntry(self.__uid, dog_data))

    def update(self, data):
        """Update the user with new entry data."""
        # We do not currently update user info or feedback
        self.__update_dogs(data)

    def get_user_info(self):
        """Return the user info."""
        return self.__user_info

    def get_feedback(self):
        """Return the feedback for the user."""
        return self.__feedback

    def get_dogs(self):
        """Return the list of dogs entries for the user."""
        return self.__dogs


class Datastore(object):

    def __init__(self):
        """Initialize the Datastore object."""
        self.__users = {}
        self.__uid = 0 # user ID

    def __is_valid_entry(self, data):
        if data[1] == 'redcap_event_name':
            return False # header
        elif data[1] == 'event_2_arm_1':
            return False # phase 2
        else:
            return True

    def add_entry(self, data):
        """Add an entry to the user database."""
        if self.__is_valid_entry(data):
            user = data[8]
            if user in self.__users:
                self.__users[user].update(data)
            else:
                # Increment the uid and add the new entry.
                self.__uid += 1
                self.__users[user] = UserEntry(self.__uid, data)

    def get_users(self):
        """Return the stored user entries."""
        return self.__users


def main():
    """
    Runs data processing scripts to turn raw data from (../raw) into
    cleaned data ready to be analyzed (saved in ../processed).
    """
    logger = logging.getLogger(__name__)

    if os.path.exists(db_path):
        logger.info('removing existing processed database')
        os.remove(db_path)

    logger.info('locating the input data file')
    infile = get_data_file()

    logger.info('constructing an sqlite database')
    manager = Manager(infile)
    manager.display_metrics()
    logger.info('construction of database complete')


if __name__ == '__main__':
    log_fmt = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    logging.basicConfig(level=logging.INFO, format=log_fmt)

    # store necessary paths
    project_dir = os.path.join(os.path.dirname(__file__), os.pardir, os.pardir)
    data_dir = os.path.join(project_dir, 'data')
    raw_path = os.path.join(data_dir, 'raw', 'raw.csv')
    db_path = os.path.join(data_dir, 'processed', 'processed.db')

    main()

"""
FILTER CRITERIA

Incompletes:

    Criteria for incompleteness:
        - incomplete welcome survey
        or
        - less than one complete dog-specific survey

    Criteria for partial completeness:
        - complete welcome survey
        - at least one complete dog-specific survey [not implemented]
        - incomplete feedback survey

Duplicates:

    Criteria for updating existing dog entry:
        - Only a complete dog entry may replace an existing dog entry.

    Criteria for updating existing user entry:
        - Only a complete user entry may replace an existing user entry.
          [not implemented]
        - The updated user entry must add to, not subtract from, the existing
          user entry. [not implemented]
"""
