import csv
import logging
import os
import shutil
import tempfile


def get_data_file():
    """Verify the input data file."""
    if os.path.isfile(raw_path):
        return raw_path
    else:
        print('Error: no scrubbable data file exists.')
        quit()


def get_temp_file():
    """Generate a temporary output file."""
    return tempfile.NamedTemporaryFile(mode='w', dir=data_dir, delete=True)


class Dog(object):

    def __init__(self, data):
        """Initialize a Dog object."""
        self.__name = data[0]
        self.__data = data

    def get_name(self):
        """Return the dog name."""
        return self.__name

    def get_data(self):
        """Return the dog data."""
        return self.__data


class User(object):

    def __init__(self, data, uid):
        """Initialize a User object."""
        # demographic status: 10, feedback status: 688 
        # incomplete: row[10]=0, partial: row[688]=0
        self.__hash = data[8]
        self.__demographics = data[1:9]
        self.__uid = uid
        self.__feedback = data[685:687]
        self.__indices = []
        self.__add_index(data[0])
        self.__dogs = []
        self.__update_dogs(data)

    def __add_index(self, index):
        """Add the index to the list of user entry indices."""
        self.__indices.append(int(index))

    def __update_dogs(self, data):
        """Update dog data for the user."""
        dog_cols = [
            {'status': 145, 'start': 11, 'end': 144},
            {'status': 280, 'start': 146, 'end': 279},
            {'status': 415, 'start': 281, 'end': 414},
            {'status': 550, 'start': 416, 'end': 549},
            {'status': 684, 'start': 551, 'end': 683}
            ]
        for entry in dog_cols:
            replacement = False
            if int(data[entry['status']]) == 2:
                dog_data = data[entry['start']:entry['end']]
                for counter, dog in enumerate(self.__dogs):
                    if dog.get_name().lower() == dog_data[0].lower():
                        # If a complete entry for the dog already exists, update
                        # it with the newest data.
                        replacement = True
                        self.__dogs[counter] = Dog(dog_data)
                        break
                if not replacement:
                    # If an entry for the dog does not exist, create one.
                    self.__dogs.append(Dog(dog_data))

    def update(self, data):
        """Update the user with new entry data."""
        self.__add_index(data[0])
        self.__update_dogs(data)

    def get_hash(self):
        """Return the email hash for the user."""
        return self.__hash

    def get_indices(self):
        """Return the entry indicies for the user."""
        return self.__indices

    def get_dogs(self):
        """Return the list of dogs for the user."""
        return self.__dogs

    def __get_single_entry(self, dog):
        """Return a single dog specific user entry."""
        entry = [self.__uid]
        entry += self.__demographics
        entry += dog.get_data()
        entry += self.__feedback
        return entry

    def get_entries(self):
        """Return a list of dog specific user entries."""
        entries = []
        for dog in self.__dogs:
            entries.append(self.__get_single_entry(dog))
        return entries

    def get_metrics(self):
        """Return the user metrics."""
        metrics = {
            'entries': len(self.__indices),
            'dogs': len(self.__dogs)
            }
        return metrics


class UserDatabase(object):

    def __init__(self):
        """Initialize the UserDatabase object."""
        self.__users = {}
        self.__header_recorded = False
        self.__header = []
        self.__user_uid = 0
        self.__metrics = {
            'users': 0,
            'dogs': 0,
            'entries': 0,
            'phase2': 0,
            'partial': 0,
            'incomplete': 0,
            'complete': 0
            }

    def __parse_header(self, data):
        """Parse the user database header from the given data."""
        if not self.__header_recorded:
            self.__header = data[0:9]
            self.__header += data[11:144]
            self.__header += data[685:687]
            self.__header_recorded = True

    def __is_valid_entry(self, data):
        if data[1] != 'event_1_arm_1':
            self.__metrics['phase2'] += 1
            return False
        elif int(data[10]) != 2 or int(data[145]) != 2:
            self.__metrics['incomplete'] += 1
            return False
        else:
            if int(data[688]) != 2:
                self.__metrics['partial'] += 1
            else:
                self.__metrics['complete'] += 1
            return True

    def add_entry(self, data):
        """Add an entry to the user database."""
        hash = data[8]
        if data[8] == 'email':
            self.__parse_header(data)
        elif self.__is_valid_entry(data):
            if hash in self.__users:
                self.__users[hash].update(data)
            else:
                self.__user_uid += 1
                self.__users[hash] = User(data, self.__user_uid)

    def get_database(self):
        """Return the user database."""
        return self.__users

    def get_header(self):
        """Return the user database header."""
        return self.__header

    def get_metrics(self):
        """Return the user database metrics."""
        for user, entry in self.__users.items():
            self.__metrics['users'] += 1
            e_metrics = entry.get_metrics()
            self.__metrics['dogs'] += e_metrics['dogs']
            self.__metrics['entries'] += e_metrics['entries']
        return self.__metrics


class Scribe(object):

    def __init__(self, userdb):
        """Initialize Scribe object."""
        self.__db = userdb.get_database()
        self.__header = userdb.get_header()

    def write_database(self, outfile):
        """Write the user database to an output file."""
        with get_temp_file() as temp:
            writer = csv.writer(temp, delimiter=',', lineterminator='\n')
            writer.writerow(self.__header)
            for user, user_entry in self.__db.items():
                dog_entries = user_entry.get_entries()
                for dog_entry in dog_entries:
                    writer.writerow(dog_entry)
                    temp.flush()
            shutil.copy2(temp.name, outfile)


def main():
    """ Runs data processing scripts to turn raw data from (../raw) into
        cleaned data ready to be analyzed (saved in ../processed).
    """
    logger = logging.getLogger(__name__)

    logger.info('locate the input data file')
    infile = get_data_file()

    logger.info('building the user database')
    db = UserDatabase()
    with open(infile, 'r') as fin:
        for row in csv.reader(fin, delimiter=','):
            db.add_entry(row)
    logger.info('calculating response metrics')
    metrics = db.get_metrics()
    print('phase2: %d' % metrics['phase2'])
    print('partial: %d, complete: %d, incomplete: %d'
          %(metrics['partial'], metrics['complete'], metrics['incomplete']))
    print('users: %d, dogs: %d, entries: %d'
          %(metrics['users'], metrics['dogs'], metrics['entries']))
    logger.info('recording the processed data')
    scribe = Scribe(db)
    scribe.write_database(processed_path)


if __name__ == '__main__':
    log_fmt = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    logging.basicConfig(level=logging.INFO, format=log_fmt)

    # store necessary paths
    project_dir = os.path.join(os.path.dirname(__file__), os.pardir, os.pardir)
    data_dir = os.path.join(project_dir, 'data')
    raw_path = os.path.join(data_dir, 'raw', 'raw.csv')
    processed_path = os.path.join(data_dir, 'processed', 'processed.csv')

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
