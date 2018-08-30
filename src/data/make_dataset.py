import csv
import logging
import os
import re
import shutil
import sqlite3


def get_data_file():
    """Verify that the input data file exists."""
    if os.path.isfile(raw_filepath):
        return raw_filepath
    else:
        print('Error: no scrubbable data file exists.')
        quit()


class Age(object):

    def __init__(self, string, unit):
        self.__orig = string
        self.__age = ''
        self.__string = string.lower()
        self.__unit = unit
        self.__unit_cnt = 0

    def parse_age(self):
        try:
            age = float(self.__string)
            if self.__unit == 'y':
                age = age * 12
            elif self.__unit == 'w':
                age = age / 4
            self.__age = age
            return True
        except ValueError:
            return False

    def parse_unit(self):
        self.__string = self.__string.replace('old', '')
        unit_dict = {
            'months': 'm', 'mos': 'm', 'years': 'y', 'weeks': 'w', 'yrs': 'y'}
        for key in unit_dict:
            if key in self.__string:
                self.__string = self.__string.replace(key, '')
                self.__unit = unit_dict[key]
                self.__unit_cnt += 1
        if self.__unit_cnt > 1:
            print("Error: multiple units for \"%s\"" %self.__orig)
            self.__string = self.__orig

    def get_age(self):
        return self.__age

    def failed_conversion(self):
        print('failed to convert (mod: %s, orig: %s)' %(self.__string, self.__orig))
        return ''


def convert_age_string(age_string, unit):
    """Covert a given age string to an age in months."""
    age = Age(age_string, unit)
    if age.parse_age():
        return age.get_age()
    age.parse_unit()
    if age.parse_age():
        return age.get_age()
    return age.failed_conversion()


def get_breed_dict():
    with open(data_dictionary, newline='', encoding='latin1') as csvfile:
        csvreader = csv.reader(csvfile, delimiter=',')
        for row in csvreader:
            if row[0] == 'purebred_breed_1a':
                combo_list = list(row[5].split("|"))
                break
    breeds = {}
    for combo in combo_list:
        sep = list(combo.split(", "))
        breeds[sep[0].strip()] = sep[1].strip()
    return breeds


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
        self.__cursor.execute(query)
        return self.__cursor.fetchone()[0]

    def create_table(self, table, header):
        """Create a table in the database."""
        fields = ' TEXT, '.join(header)
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
        self.__db = Database(processed_filepath)
        self.__path = path
        self.__headers = {}
        self.__parse_headers()
        self.__data = {}
        self.__parse_data()

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

    def create_tables(self):
        """Generate tables with the generated headers."""
        self.__db.create_table('users', self.__headers['users'])
        self.__db.create_table('dogs', self.__headers['dogs'])
        self.__db.create_table('feedback', self.__headers['feedback'])

    def populate_tables(self):
        """Populate the generated tables with the raw data."""
        for user, user_entry in self.__data.items():
            self.__db.insert_record('users', user_entry.get_user_info())
            self.__db.insert_record('feedback', user_entry.get_feedback())
            dog_entries = user_entry.get_dogs()
            for dog_entry in dog_entries:
                self.__db.insert_record('dogs', dog_entry.get_data())
        self.__db.commit()

    def update_tables(self):
        """Update the generated tables with the raw data."""
        for user, user_entry in self.__data.items():
            self.__db.insert_record('users', user_entry.get_user_info())
            self.__db.insert_record('feedback', user_entry.get_feedback())
            dog_entries = user_entry.get_dogs()
            for dog_entry in dog_entries:
                self.__db.update_record('dogs', dog_entry.get_data())
        self.__db.commit()

    def write_metrics(self):
        """Write the database metrics."""
        offset = '  '
        with open(metrics_filepath, 'w') as fout:
            fout.write('users:\n')
            fout.write('%s- total: %d\n'
                       %(offset, self.__db.get_count('users')))
            mod = 'WHERE phase_1_welcome_complete="0"'
            fout.write('%s- invalid: %d\n'
                       %(offset, self.__db.get_count('users', mod)))
            join = 'JOIN feedback ON users.record_id=feedback.record_id'
            mod = '%s WHERE phase_1_feedback_complete="2"' %join
            fout.write('%s- complete: %d\n'
                       %(offset, self.__db.get_count('users', mod)))
            fout.write('dogs:\n')
            fout.write('%s- total: %d\n'
                       %(offset, self.__db.get_count('dogs')))


class DogEntry(object):

    def __init__(self, uid, data):
        """Initialize a DogEntry object."""
        self.__name = data[0]
        self.__data = data
        self.__verify_data()
        self.__data.insert(0, uid)
        # Convert breed reference index to breed.
        if data[4]:
            data[4] = BREED_REFERENCE[data[4]]
        if data[8] == '4':
            data[8] = '1'
        # 13 = months, 14 = years
        if data[13]:
            age = data[13]
            unit = 'm'
            data[13] = convert_age_string(age, unit)
        elif data[14]:
            age = data[14]
            unit = 'y'
            data[13] = convert_age_string(age, unit)

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
        self.__user_info = data[1:11] # start at one to discard redcap ID
        self.__feedback = data[685:689]
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

    def __update_user_info(self, data):
        """Update user info for the user."""
        if data[10] == '2':
            self.__user_info = data[1:11]

    def __update_feedback(self, data):
        """Update feedback for the user."""
        if data[688] == '2':
            self.__feedback = data[685:689]

    def update(self, data):
        """Update the user with new entry data."""
        # We do not currently update user info or feedback
        self.__update_dogs(data)
        self.__update_user_info(data)
        self.__update_feedback(data)

    def get_user_info(self):
        """Return the user info."""
        user_info = self.__user_info[:]
        user_info.insert(0, self.__uid)
        return user_info

    def get_feedback(self):
        """Return the feedback for the user."""
        feedback = self.__feedback[:]
        feedback.insert(0, self.__uid)
        return feedback

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


class DatabaseModifier(object):

    def __init__(self):
        """Initialize a DatabaseModifier object."""
        self.__conn = sqlite3.connect(processed_filepath)
        self.__cursor = self.__conn.cursor()
        self.__modifySoilTypes()

    def __getValues(self, field):
        query = 'SELECT record_id, %s FROM dogs;' %(field)
        self.__cursor.execute(query)
        return self.__cursor.fetchall()

    def __addColumn(self, field):
        query = 'ALTER TABLE dogs ADD COLUMN %s TEXT DEFAULT 0;' %(field)
        self.__cursor.execute(query)

    def __addValue(self, record_id, field, value):
        query = ('UPDATE dogs SET  %s=%s WHERE record_id=%s;'
                 %(field, value, record_id))
        self.__cursor.execute(query)

    def __modifySoilTypes(self):
        field = 'q06_soil_type'
        values = self.__getValues(field)
        for i in range(1, 4):
            self.__addColumn(field + '_%s'%i)
        for pair in values:
            if pair[1]:
                self.__addValue(pair[0], field + '_%s'%pair[1], 1)
        self.__conn.commit()


def main():
    """
    Runs data processing scripts to turn raw data from (../raw) into
    cleaned data ready to be analyzed (saved in ../processed).
    """
    logger = logging.getLogger(__name__)

    if os.path.exists(processed_filepath):
        logger.info('remove existing processed dataset')
        os.remove(processed_filepath)

    manager = Manager(get_data_file())
    logger.info('creating tables')
    manager.create_tables()
    logger.info('populating the database')
    manager.populate_tables()
    logger.info('recording metrics')
    manager.write_metrics()

    logger.info('modifying database')
    modifier = DatabaseModifier()

    logger.info('dataset generation complete')


if __name__ == '__main__':
    log_fmt = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    logging.basicConfig(level=logging.INFO, format=log_fmt)

    # store necessary paths and variables
    project_dir = os.path.join(os.path.dirname(__file__), os.pardir, os.pardir)
    data_dir = os.path.join(project_dir, 'data')
    raw_filepath = os.path.join(data_dir, 'raw', 'raw.csv')
    processed_filepath = os.path.join(data_dir, 'processed', 'processed.db')
    metrics_filepath = os.path.join(project_dir, 'reports', 'metrics.txt')
    data_dictionary = os.path.join(project_dir, 'references', 'data_dictionary.csv')
    BREED_REFERENCE=get_breed_dict()

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
