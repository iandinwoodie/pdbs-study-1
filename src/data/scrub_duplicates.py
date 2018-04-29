import csv
import logging
import os
import re
import shutil
import tempfile


def get_data_file():
    """Determine the data file to be scrubbed."""
    if os.path.isfile(interim_path):
        return interim_path
    elif os.path.isfile(raw_path):
        return raw_path
    else:
        print('Error: no scrubbable data file exists.')
        quit()


def get_temp_file():
    """Generate a temporary output file."""
    return tempfile.NamedTemporaryFile(mode='w', dir=interim_dir, delete=True)


class Response(object):

    def __init__(self, row):
        """Initializes Response object for a given row."""
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


def get_response_log(infile):
    """Generate a dictionary of user hashes with duplicate entries."""
    response_log = {}
    with open(infile, 'r') as fin:
        for row in csv.reader(fin, delimiter=','):
            if row[0] != 'record_id':
                # Fetch the relevant information from the entry row.
                entry = Response(row)
                if entry.hash not in response_log:
                    response_log[entry.hash] = {}
                response_log[entry.hash][entry.uid] = {}
                response_log[entry.hash][entry.uid]['entry'] = entry
                response_log[entry.hash][entry.uid]['remove'] = False
                if len(response_log[entry.hash]) > 1:
                    if entry.status[6] == 0:
                        # Mark the current entry if it is incomplete.
                        response_log[entry.hash][entry.uid]['remove'] = True
                    else:
                        # Loop through existing entries.
                        for key, value in response_log[entry.hash].items():
                            # Do not compare the current entry with itself.
                            if key != entry.uid:
                                past_entry = response_log[entry.hash][key]['entry']
                                if past_entry.status[6] == 0:
                                    # Mark the past entry if it was incomplete.
                                    response_log[entry.hash][key]['remove'] = True
                                else:
                                    pdogs = past_entry.dogs
                                    cdogs = entry.dogs
                                    if not bool(pdogs.symmetric_difference(cdogs)):
                                        if past_entry.status_sum <= entry.status_sum:
                                            # Old entry for same list of dogs is less
                                            # complete, mark it.
                                            response_log[entry.hash][key]['remove'] = True
                                    elif bool(cdogs.intersection(pdogs)):
                                        if past_entry.status_sum <= entry.status_sum:
                                            # Old entry shares at least one dog, but is
                                            # less complete, mark it.
                                            response_log[entry.hash][key]['remove'] = True
                                    else:
                                        response_log[entry.hash][entry.uid]['remove'] = True

    return response_log


def main():
    """
    Scrubs duplicates from raw data.

    Criteria to update existing response:
        - The updated response must not replace a complete entry for a specific dog
          with an incomplete entry.
        - The updated response must not replace a complete entry for a specific dog
          with an entry for a different dog.
        - The updated response must not detract from the existing data of a complete
          entry for a specific dog.

    Criteria to dispose subsequent response:
        - The updated response replaces a complete entry for a specific dog with an
          incomplete entry.
        - The updated response replaces a complete entry for a specific dog with an
          entry for a different dog.
        - The updated response detracts from the existing data of a complete entry
          for a specific dog.

    Criteria to keep existing and subsequent responses:
        - Both the existing and updated responses contain complete dog-specific
          entries.
        - No complete entry for the same specific dog is shared in both responses.
    """
    logger = logging.getLogger(__name__)

    # Determine the input and output files.
    infile = get_data_file()

    # Get response log.
    logger.info('generating response log')
    response_log = get_response_log(infile)

    # Scrub Phase 1 duplicate responses.
    counts = {
        'original': 0,
        'duplicate': 0
        }
    logger.info('scrubbing duplicate results')
    cnt = 0
    with get_temp_file() as temp:
        with open(infile, 'r') as fin:
            writer = csv.writer(temp, delimiter=',', lineterminator='\n')
            for row in csv.reader(fin, delimiter=','):
                if row[0] != 'record_id':
                    if response_log[row[8]][int(row[0])]['remove']:
                        counts['duplicate'] += 1
                    else:
                        writer.writerow(row)
                        counts['original'] += 1
        print('originals: %d, duplicates: %d'
              %(counts['original'], counts['duplicate']))
        logger.info('discarding temp data file')


if __name__ == "__main__":
    log_fmt = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    logging.basicConfig(level=logging.INFO, format=log_fmt)

    # store necessary paths
    project_dir = os.path.join(os.path.dirname(__file__), os.pardir, os.pardir)
    interim_dir = os.path.join(project_dir, 'data', 'interim')
    interim_path = os.path.join(interim_dir, 'interim.csv')
    raw_path = os.path.join(project_dir, 'data', 'raw', 'raw.csv')

    main()
