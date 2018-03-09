"""Scrubs incompletes from raw data."""

import os
import shutil
import csv


# Verify the file to be scrubbed.
print(os.listdir(os.getcwd()))
filename = str(input('Enter file to be scrubbed of incompletes: '))
if not os.path.isfile(filename):
    print('Error: entered filename does not exist')
    quit()

# Create a backup of the original file if does not exist.
backup = filename + '.bak'
if not os.path.isfile(backup):
    print('Creating a backup of the the original file ...')
    shutil.copy(filename, backup)

# Parse the raw data with relevant filters.
partial_cnt = 0
complete_cnt = 0
incomplete_cnt = 0
with open(backup, 'r') as fin:
    with open(filename, 'w') as fout:
        writer = csv.writer(fout, delimiter=',', lineterminator='\n')
        first_row = True
        for row in csv.reader(fin, delimiter=','):
            if not first_row:
                status_sum = (int(row[10]) + int(row[145]) + int(row[280])
                              + int(row[415]) + int(row[550]) + int(row[688]))
                if status_sum > 2:
                    if int(row[688]) == 0:
                        # Users who answered at least one behavior form, but
                        # terminated the survey before the last form.
                        partial_cnt += 1
                    else:
                        # Users who answered the survey through the last form.
                        complete_cnt += 1
                else:
                    # Users who did not answer at least one behavior form.
                    incomplete_cnt += 1
                    continue
            else:
                first_row = False
            writer.writerow(row)

# Let the user know the script has finished.
print('Partial: %d, Complete: %d, Incomplete: %d'
      %(partial_cnt, complete_cnt, incomplete_cnt))
print('Scrubbing of %s is complete.' %filename)
