"""
Scrubs incompletes from raw data.

Criteria for incompleteness:
    - incomplete welcome survey
    - less than one complete dog-specific survey

Criteria for partial completeness:
    - complete welcome survey
    - at least one complete dog-specific survey
    - incomplete feedback survey
"""

import argparse
import csv
import os
import shutil


# Parse the input file from the command-line arguments.
parser = argparse.ArgumentParser(description='Scrub duplicates from raw data.')
parser.add_argument('filename')
args = parser.parse_args()
infile = args.filename

# Verify the file to be scrubbed.
if not os.path.isfile(infile):
    print('Error: entered file does not exist')
    quit()

# Make a copy of the input file.
base = os.path.splitext(os.path.basename(infile))[0]
outfile = base + '.data'
bakfile = base + '.bak'
shutil.copy(infile, bakfile)

# Parse the raw data with relevant filters.
partial_cnt = 0
complete_cnt = 0
incomplete_cnt = 0
with open(bakfile, 'r') as fin:
    with open(outfile, 'w') as fout:
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

# Delete copy of input file.
os.remove(bakfile)

# Let the user know the script has finished.
print('Partial: %d, Complete: %d, Incomplete: %d'
      %(partial_cnt, complete_cnt, incomplete_cnt))
print('Incompletes scrubbing complete.')
