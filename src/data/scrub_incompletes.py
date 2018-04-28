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


def main():
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
            first_row = True
            for row in csv.reader(fin, delimiter=','):
                if not first_row:
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
                else:
                    first_row = False
                writer.writerow(row)
        print('partial: %d, complete: %d, incomplete: %d'
              %(counts['partial'], counts['complete'], counts['incomplete']))
        logger.info('saving scrubbed data file')
        shutil.copy2(temp.name, interim_path)


if __name__ == "__main__":
    log_fmt = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    logging.basicConfig(level=logging.INFO, format=log_fmt)

    # store necessary paths
    project_dir = os.path.join(os.path.dirname(__file__), os.pardir, os.pardir)
    interim_dir = os.path.join(project_dir, 'data', 'interim')
    interim_path = os.path.join(interim_dir, 'interim.csv')
    raw_path = os.path.join(project_dir, 'data', 'raw', 'raw.csv')

    main()
