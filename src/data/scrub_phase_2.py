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
