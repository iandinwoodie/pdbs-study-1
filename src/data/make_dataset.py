from itertools import combinations
import csv
import logging
import os
import re
import shutil
import tempfile


def get_data_file():
    """Determine the data file to be scrubbed."""
    if os.path.isfile(processed_path):
        return processed_path
    elif os.path.isfile(raw_path):
        return raw_path
    else:
        print('Error: no scrubbable data file exists.')
        quit()


def get_temp_file():
    """Generate a temporary output file."""
    return tempfile.NamedTemporaryFile(mode='w', dir=data_dir, delete=True)


class User(object):

    def __init__(self, row):
        """Initializes User object for a given row."""
        self.uid = int(row[0])
        self.hash = row[8]
        self.status = self.get_statuses(row)
        self.status_sum = sum(self.status)
        self.dogs = self.get_dogs(row)

    def get_statuses(self, row):
        """Generate a list of survey statuses for a given row."""
        status_list = [int(row[10]), int(row[145]), int(row[280]),
                       int(row[415]), int(row[550]), int(row[684]),
                       int(row[688])
        ]
        return status_list

    def get_dogs(self, row):
        """Generate a list of dogs for a given row."""
        dog_list = [row[11], row[146], row[281], row[416], row[551]]
        dog_list = [x for x in dog_list if x != '']
        return set(dog_list)


def add_user_to_log(log, user):
    """Add a user to the user log."""
    if user.hash not in log:
        log[user.hash] = {}
    log[user.hash][user.uid] = {}
    log[user.hash][user.uid]['user'] = user
    log[user.hash][user.uid]['remove'] = False
    return log


def get_user_log(infile):
    """Generate a dictionary of user hashes with duplicate entries."""
    log = {}
    with open(infile, 'r') as fin:
        for row in csv.reader(fin, delimiter=','):
            if row[0] != 'record_id':
                # Fetch the relevant information from the entry row.
                user = User(row)
                log = add_user_to_log(log, user)
    for user, users in log.items():
        if len(users) > 1:
            combos = list(map(dict, combinations(users.items(), 2)))
            for combo in combos:
                r1 = combo[list(combo)[0]]['user']
                r2 = combo[list(combo)[1]]['user']
                if (not bool(r1.dogs.symmetric_difference(r2.dogs)) or
                    bool(r1.dogs.intersection(r2.dogs))):
                    # Same or shared list of dogs.
                    if r1.status_sum > r2.status_sum:
                        combo[list(combo)[1]]['remove'] = True
                    elif r1.status_sum < r2.status_sum:
                        combo[list(combo)[0]]['remove'] = True
                    else:
                        combo[list(combo)[1]]['remove'] = True
                else:
                    # Different list of dogs.
                    pass
    return log


def scrub_duplicates():
    """
    Scrubs duplicates from raw data.

    Criteria to update existing user:
        - The updated user must not replace a complete entry for a specific dog
          with an incomplete entry.
        - The updated user must not replace a complete entry for a specific dog
          with an entry for a different dog.
        - The updated user must not detract from the existing data of a complete
          entry for a specific dog.

    Criteria to dispose subsequent user:
        - The updated user replaces a complete entry for a specific dog with an
          incomplete entry.
        - The updated user replaces a complete entry for a specific dog with an
          entry for a different dog.
        - The updated user detracts from the existing data of a complete entry
          for a specific dog.

    Criteria to keep existing and subsequent users:
        - Both the existing and updated users contain complete dog-specific
          entries.
        - No complete entry for the same specific dog is shared in both users.
    """
    logger = logging.getLogger(__name__)

    # Determine the input and output files.
    infile = get_data_file()

    # Get user log.
    logger.info('generating user log')
    log = get_user_log(infile)

    # Scrub Phase 1 duplicate users.
    counts = {
        'original': 0,
        'duplicate': 0
        }
    logger.info('scrubbing duplicate results')
    with get_temp_file() as temp:
        with open(infile, 'r') as fin:
            writer = csv.writer(temp, delimiter=',', lineterminator='\n')
            for row in csv.reader(fin, delimiter=','):
                if row[0] != 'record_id':
                    if log[row[8]][int(row[0])]['remove']:
                        # Do not record duplicates.
                        counts['duplicate'] += 1
                    else:
                        # Record duplicates.
                        writer.writerow(row)
                        counts['original'] += 1
                else:
                    # Record the header.
                    writer.writerow(row)
        print('originals: %d, duplicates: %d'
              %(counts['original'], counts['duplicate']))
        logger.info('saving scrubbed data file')
        shutil.copy2(temp.name, processed_path)


def scrub_phase_2():
    """
    Scrub Phase 2 results from the raw data.
    """
    logger = logging.getLogger(__name__)

    # Determine the input and output files.
    infile = get_data_file()

    # Scrub the Phase 2 results.
    counts = {
        'phase_1': 0,
        'phase_2': 0
        }
    logger.info('scrubbing phase 2 results')
    with get_temp_file() as temp:
        with open(infile, 'r') as fin:
            writer = csv.writer(temp, delimiter=',', lineterminator='\n')
            for row in csv.reader(fin, delimiter=','):
                if row[1] != 'event_2_arm_1':
                    writer.writerow(row)
                    counts['phase_1'] += 1
                else:
                    counts['phase_2'] += 1
        print('phase 1: %d, phase 2: %d'
              %(counts['phase_1'], counts['phase_2']))
        logger.info('saving scrubbed data file')
        shutil.copy2(temp.name, processed_path)


def scrub_incompletes():
    """
    Scrub incomplete records from the raw data.

    Criteria for incompleteness:
        - incomplete welcome survey
        - less than one complete dog-specific survey

    Criteria for partial completeness:
        - complete welcome survey
        - at least one complete dog-specific survey
        - incomplete feedback survey
    """
    logger = logging.getLogger(__name__)

    # Determine the input and output files.
    infile = get_data_file()

    # Scrub incomplete Phase 1 results.
    counts = {
        'partial': 0,
        'complete': 0,
        'incomplete': 0
        }
    logger.info('scrubbing incomplete results')
    with get_temp_file() as temp:
        with open(infile, 'r') as fin:
            writer = csv.writer(temp, delimiter=',', lineterminator='\n')
            for row in csv.reader(fin, delimiter=','):
                if row[0] != 'record_id':
                    status_sum = (int(row[10]) + int(row[145]) + int(row[280])
                                  + int(row[415]) + int(row[550]) + int(row[684]))
                    if status_sum > 2:
                        if int(row[688]) == 0:
                            # Users who answered at least one behavior form, but
                            # terminated the survey before the last form.
                            counts['partial'] += 1
                        else:
                            # Users who answered the survey through the last form.
                            counts['complete'] += 1
                    else:
                        # Users who did not answer at least one behavior form.
                        counts['incomplete'] += 1
                        continue
                writer.writerow(row)
        print('partial: %d, complete: %d, incomplete: %d'
              %(counts['partial'], counts['complete'], counts['incomplete']))
        logger.info('saving scrubbed data file')
        shutil.copy2(temp.name, processed_path)


def main():
    """ Runs data processing scripts to turn raw data from (../raw) into
        cleaned data ready to be analyzed (saved in ../processed).
    """
    logger = logging.getLogger(__name__)
    logger.info('making final data set from raw data')
    # Scrub Phase 2 results.
    scrub_phase_2()
    # Scrub incomplete results.
    scrub_incompletes()
    # Scrub duplicate results.
    scrub_duplicates()
    logger.info('data set created')


if __name__ == '__main__':
    log_fmt = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    logging.basicConfig(level=logging.INFO, format=log_fmt)

    # store necessary paths
    project_dir = os.path.join(os.path.dirname(__file__), os.pardir, os.pardir)
    data_dir = os.path.join(project_dir, 'data')
    raw_path = os.path.join(project_dir, 'data', 'raw', 'raw.csv')
    processed_path = os.path.join(project_dir, 'data', 'processed', 'processed.csv')

    main()
