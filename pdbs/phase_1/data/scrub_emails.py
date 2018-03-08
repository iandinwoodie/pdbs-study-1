import csv
import hashlib

m = hashlib.md5()
filename = 'pdbs_phase_1_raw_labels.csv'
with open('pre_'+filename, 'r', encoding='latin-1') as fin, open(filename, 'w') as fout:
    writer = csv.writer(fout, delimiter=',')
    first_row = True
    for row in csv.reader(fin, delimiter=','):
        if first_row == False:
            m.update(row[8].encode('utf-8'))
            row[8] = m.hexdigest()
        else:
            first_row = False
        writer.writerow(row)
