import os
import csv


def main():
    with open(data_dictionary, newline='', encoding='latin1') as csvfile:
        csvreader = csv.reader(csvfile, delimiter=',')
        for row in csvreader:
            if row[0] == 'purebred_breed_1a':
                combo_list = list(row[5].split("|"))
                break

    breeds = {}
    for combo in combo_list:
        sep = list(combo.split(", "))
        breeds[int(sep[0])] = sep[1].rstrip()

    with open(breed_list, 'w') as f:
        f.write("BREED_REFERENCE = {\n")
        for key, value in breeds.items():
            f.write('    "{}": "{}",\n'.format(key, value))
        f.write("}")

    print("Breed list generated.")


if __name__ == '__main__':
    # store necessary paths
    project_dir = os.path.join(os.path.dirname(__file__), os.pardir, os.pardir)
    reference_dir = os.path.join(project_dir, 'references')
    data_dictionary = os.path.join(reference_dir, 'data_dictionary.csv')
    breed_list = os.path.join(reference_dir, 'breed_list.py')

    main()
