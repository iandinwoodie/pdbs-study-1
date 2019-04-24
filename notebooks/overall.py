# General imports.
import sqlite3
import pandas as pd
from matplotlib_venn import venn2, venn3
import scipy.stats as scs
import textwrap
import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns
from  itertools import combinations
import os
from matplotlib.colors import ListedColormap
from matplotlib import ticker
from scipy.stats import ttest_ind
import math

# Imports from neighbor directories.
import sys
sys.path.append("..")
from src.utilities import field_registry as fieldreg

# Data Globals
FR = fieldreg.FieldRegistry()
TOTAL_USERS = 0
REMAINING_USERS = 0
TOTAL_DOGS = 0
REMAINING_DOGS = 0
PREVALENCE = lambda x: (x / REMAINING_DOGS) * 100
CATEGORY_MATRIX = pd.DataFrame()
NITER = 10000

# Database Globals
USER_TABLE = 'users'
DOG_TABLE = 'dogs'
BIAS_FILTER = '''
    USING (record_id)
    WHERE question_reason_for_part_3 = 0
    OR (question_reason_for_part_3 = 1 AND q01_main != 1)'''
CON = sqlite3.connect('../data/processed/processed.db')


# Helper Functions
def createStringDataFrame(table, fields, labels, filtered=True):
    query = 'SELECT ' + fields + ' FROM ' + table
    if filtered:
        table2 = USER_TABLE if table == DOG_TABLE else DOG_TABLE
        query += ' JOIN ' + table2 + ' ' + BIAS_FILTER
    df = pd.read_sql_query(query, CON)
    df.columns = labels
    return df


def convertToNumeric(df):
    df = df.apply(pd.to_numeric, errors='coerce')
    return df


def createNumericDataFrame(table, fields, labels, filtered=True):
    df = createStringDataFrame(table, fields, labels, filtered)
    return convertToNumeric(df)


def replaceFields(df, column, replacement_dict):
    df[column].replace(replacement_dict, inplace=True)


def getValueCountAndPrevalence(df, field):
    s = df[field].value_counts()
    p = s.apply(PREVALENCE).round().astype(int)
    rv = pd.concat([s, p], axis=1)
    rv.columns = ['frequency', 'prevalence']
    return rv


def createCategoryMatrix():
    fields = []
    labels = []
    counter = 1
    for cat, subdict in FR.labels.items():
        for key, value in  subdict.items():
            if counter == 11:
                counter += 1;
            fields.append('q02_main_{}'.format(counter))
            labels.append(key[0])
            break
        counter += 1
    fields = ', '.join(fields)
    df = createNumericDataFrame(DOG_TABLE, fields, labels, filtered=True)
    cols = []
    pvalue = {}
    for col in df:
        cols.append(col)
        pvalue[col] = {}
    pairs = list(combinations(df.columns, 2))
    for pair in pairs:
        contingency = pd.crosstab(df[pair[0]], df[pair[1]])
        c, p, dof, expected = scs.chi2_contingency(contingency, correction=False)
        pvalue[pair[0]][pair[1]] = p
        pvalue[pair[1]][pair[0]] = p
    df = pd.DataFrame(pvalue).sort_index(ascending=True)
    return df


def createQuestionMatrix():
    fields = ''
    for cat, sublist in FR.fields.items():
        for field in sublist:
            fields += '{}, '.format(field)
    fields = fields[:-2]
    labels = []
    for cat, subdict in FR.labels.items():
        for key, value in  subdict.items():
            labels.append(key)
    df = createNumericDataFrame(DOG_TABLE, fields, labels, filtered=True)
    cols = []
    pvalue = {}
    for col in df:
        cols.append(col)
        pvalue[col] = {}
    pairs = list(combinations(df.columns, 2))
    for pair in pairs:
        contingency = pd.crosstab(df[pair[0]], df[pair[1]])
        c, p, dof, expected = scs.chi2_contingency(contingency, correction=False)
        pvalue[pair[0]][pair[1]] = p
        pvalue[pair[1]][pair[0]] = p
    df = pd.DataFrame(pvalue).sort_index(ascending=True)
    return df


def createCorrelationMatrix():
    fields = []
    labels = []
    counter = 1
    for cat, subdict in FR.labels.items():
        for key, value in  subdict.items():
            if counter == 11:
                counter += 1;
            fields.append('q02_main_{}'.format(counter))
            labels.append(key[0])
            break
        counter += 1
    fields = ', '.join(fields)
    df = createNumericDataFrame(DOG_TABLE, fields, labels, filtered=True)
    return df.corr()


def createOddsRatioMatrix():
    fields = []
    labels = []
    counter = 1
    for cat, subdict in FR.labels.items():
        for key, value in  subdict.items():
            if counter == 11:
                counter += 1;
            fields.append('q02_main_{}'.format(counter))
            labels.append(key[0])
            break
        counter += 1
    fields = ', '.join(fields)
    df = createNumericDataFrame(DOG_TABLE, fields, labels, filtered=True)
    cols = []
    pvalue = {}
    for col in df:
        cols.append(col)
        pvalue[col] = {}
    pairs = list(combinations(df.columns, 2))
    for pair in pairs:
        contingency = pd.crosstab(df[pair[0]], df[pair[1]])
        c, p, dof, expected = scs.chi2_contingency(contingency, correction=False)
        pvalue[pair[0]][pair[1]] = getOddsRatio(contingency)
        pvalue[pair[1]][pair[0]] = getOddsRatio(contingency)
    df = pd.DataFrame(pvalue).sort_index(ascending=True)
    return df


def displayOddsRatio(df):
    odds, ci_low, ci_high, tot = getOddsRatioAndConfidenceInterval(df)
    print('OR = %.2f, 95%% CI: %.2f-%.2f, n = %d'
          %(round(odds, 2), round(ci_low, 2), round(ci_high, 2), tot))


def getOddsRatio(df):
    return (df[1][1]/df[1][0])/(df[0][1]/df[0][0])


def getOddsRatioAndConfidenceInterval(df):
    odds = getOddsRatio(df)
    nl_or = math.log(odds)
    se_nl_or = math.sqrt((1/df[0][0])+(1/df[0][1])+(1/df[1][0])+(1/df[1][1]))
    ci_low = math.exp(nl_or - (1.96 * se_nl_or))
    ci_high = math.exp(nl_or + (1.96 * se_nl_or))
    tot = df[0][0] + df[0][1] + df[1][0] + df[1][1]
    return odds, ci_low, ci_high, tot


def get_significance_category(p):
    if np.isnan(p):
        return p
    elif p > 10**(-3):
        return -1
    elif p <= 10**(-3) and p > 10**(-6):
        return 0
    else:
        return 1


def displaySeriesMedian(s, units=""):
    print('MD = %.2f %s (SD = %.2f, min = %.2f, max = %.2f, n = %d)'
          %(round(s.median(), 2), units, round(s.std(), 2), round(s.min(), 2), round(s.max(), 2), s.count()))


def displaySeriesMean(s, units=""):
    print('M = %.2f %s (SD = %.2f, min = %.2f, max = %.2f, n = %d)'
          %(round(s.mean(), 2), units, round(s.std(), 2), round(s.min(), 2), round(s.max(), 2), s.count()))


def convert_to_binary_response(x, y=1):
    x = float(x)
    if x < y:
        return 0
    return 1


def exportTable(data, title):
    if not SAVE_OUTPUT:
        return
    file_ = os.path.join('..', 'reports', 'tables', title) + '.tex'
    with open(file_, 'w') as tf:
        tf.write(r'\documentclass[varwidth=\maxdimen]{standalone}\usepackage{booktabs}\begin{document}')
        tf.write(df.to_latex())
        tf.write(r'\end{document}')


def exportFigure(figure, title):
    if not SAVE_OUTPUT:
        return
    file_ = os.path.join('..', 'reports', 'figures', title) + '.pdf'
    figure.tight_layout()
    figure.savefig(file_, format='pdf')


def printTitle(title):
    print('\n{}\n{}\n'.format(('-'*80), title.upper()))


# Calculations
def number_of_participants():
    printTitle('number of participants')
    df = createNumericDataFrame(USER_TABLE, 'COUNT(*)', ['count'], filtered=False)
    # Assign value to global.
    global TOTAL_USERS
    TOTAL_USERS = df['count'][0]
    print('N = %d owners [unadjusted]' %TOTAL_USERS)


def number_of_participating_dogs():
    printTitle('number of participating dogs')
    df = createNumericDataFrame(DOG_TABLE, 'COUNT(*)', ['count'], filtered=False)
    # Assign value to global.
    global TOTAL_DOGS
    TOTAL_DOGS = df['count'][0]
    print('N = %d dogs [unadjusted]' %TOTAL_DOGS)


def adjusted_sample():
    printTitle('adjusted sample')
    fields = 'q02_score'
    labels = ['Score']
    df_adjusted_dogs = createNumericDataFrame(DOG_TABLE, fields, labels)
    global REMAINING_DOGS
    REMAINING_DOGS = len(df_adjusted_dogs.index)
    df_adjusted_users = createNumericDataFrame(USER_TABLE, 'COUNT(DISTINCT email)', ['count'])
    global REMAINING_USERS
    REMAINING_USERS = df_adjusted_users['count'][0]
    # Display the count results.
    print('N = %d owners (adjusted)' %REMAINING_USERS)
    print('N = %d dogs (adjusted)' %REMAINING_DOGS)


def impact_of_gender_on_house_soiling_w_fear_anxiety():
    printTitle('impact of gender on house soiling w/ fear/anxiety')
    # Of the dogs with fear/anxiety that exhibited inappropriate elimination,
    # there was no statistical difference between the sexes, although the
    # majority (56%) were female.
    fields = 'dog_sex, q02_main_4, q02_main_2' 
    labels = ['sex', 'house soiling', 'fear/anxiety']
    df = createStringDataFrame(DOG_TABLE, fields, labels)
    df = df[df[labels[0]] != '']
    df = df[df[labels[2]] == '1']
    df.drop(columns=labels[2], inplace=True)
    df = df.apply(pd.to_numeric)

    def gender_to_binary_response(x):
        x = int(x)
        if x != 1:
            return 0 # female
        return 1 # male

    df[labels[0]] = df[labels[0]].apply(lambda x: gender_to_binary_response(x))
    boot_df = df.copy()
    # Cross tabulate the relevant columns.
    contingency = pd.crosstab(df[labels[0]], df[labels[1]], margins=False)
    # Execute a chi-squared test of independence.
    c, p, dof, expected = scs.chi2_contingency(contingency, correction=False)
    print('Chi-square Test of Independence:')
    print('chi2 = %f, p = %.2E, dof = %d' %(c, p, dof))
    displayOddsRatio(contingency)

    def get_bootstrap_odds_ratio_ci(data, count=10, alpha=0.95):
        #start = timer()
        arr = np.array([])
        for i in range(count):
            df = data.sample(len(data.index), replace=True)
            contingency = pd.crosstab(df[labels[0]], df[labels[1]], margins=False)
            odds, ci_low, ci_high, tot = getOddsRatioAndConfidenceInterval(contingency)
            arr = np.append(arr, odds)
        arr = np.sort(arr)
        lower = (1-alpha)/2
        upper = alpha+lower
        print('95%% CI: %.2f-%.2f' %(arr[int(lower * len(arr))], arr[int(upper * len(arr))]))
        #end = timer()
        #print('\nbootstrap time: %.2f' %(end-start))

    get_bootstrap_odds_ratio_ci(boot_df, count=NITER)


def prevalence_of_biting():
    printTitle('prevalence of biting')
    fields = 'q03_form_5'
    labels = ['bites']
    df = createNumericDataFrame(DOG_TABLE, fields, labels, filtered=True)
    tot = df.sum()
    print('Dogs that bite: n = %d dogs (%d%%)' %(tot, round((tot/REMAINING_DOGS)*100, 0)))


def bite_people():
    printTitle('prevalence of biting people')
    fields = 'q03_form_5'
    labels = ['bites']
    df = createNumericDataFrame(DOG_TABLE, fields, labels, filtered=True)
    all_bites = df.sum()[0]
    fields = 'q03_person'
    labels = ['person']
    df = createNumericDataFrame(DOG_TABLE, fields, labels, filtered=True)
    tot = df.sum()
    print('Dogs that bit a person: n = %d dogs (%d%%)' %(tot, round((tot/all_bites)*100, 0)))
    fields = 'q03_person_freq'
    labels = ['person count']
    df = createNumericDataFrame(DOG_TABLE, fields, labels, filtered=True)
    print('Number of times the dog has bitten a person:')
    displaySeriesMedian(df[labels[0]], labels[0])


def bite_dogs():
    printTitle('prevalence of biting dogs')
    fields = 'q03_form_5'
    labels = ['bites']
    df = createNumericDataFrame(DOG_TABLE, fields, labels, filtered=True)
    all_bites = df.sum()[0]
    fields = 'q03_dog'
    labels = ['dog']
    df = createNumericDataFrame(DOG_TABLE, fields, labels, filtered=True)
    tot = df.sum()
    print('Dogs that bit a dog: n = %d dogs (%d%%)' %(tot, round((tot/all_bites)*100, 0)))
    fields = 'q03_dog_freq'
    labels = ['dog count']
    df = createNumericDataFrame(DOG_TABLE, fields, labels, filtered=True)
    print('Number of times the dog has bitten a dog:')
    displaySeriesMedian(df[labels[0]], labels[0])


def multiple_bites_per_incident():
    printTitle('prevalence of multiple bite incidents')
    fields = 'q03_form_5'
    labels = ['bites']
    df = createNumericDataFrame(DOG_TABLE, fields, labels, filtered=True)
    all_bites = df.sum()[0]
    fields = 'q03_bite_quantity'
    labels = ['multi']
    df = createNumericDataFrame(DOG_TABLE, fields, labels, filtered=True)
    tot = df.sum()
    print('Dogs with multi-bite incidents: n = %d dogs (%d%%)' %(tot, round((tot/all_bites)*100, 0)))


def bite_severity():
    printTitle('non-specific bite severity')
    print('Overall bite severity:')
    fields = 'q03_severity'
    labels = ['severity']
    df = createNumericDataFrame(DOG_TABLE, fields, labels, filtered=True)
    df = df.apply(pd.value_counts)
    df.rename(index=str, columns={labels[0]: 'count'}, inplace=True)
    df.columns.name = labels[0]
    teeth_contact = 0
    broke_skin = 0
    multiple_bites = 0
    for index, row in df.iterrows():
        level = float(index)
        if level > 1:
            teeth_contact += row[0]
        if level >= 3:
            broke_skin += row[0]
        if level == 5:
            multiple_bites += row[0]
    print('teeth contact: n = %d (%d%%)'
          %(teeth_contact,round((teeth_contact/df['count'].sum())*100, 0)))
    print('broke skin: n = %d (%d%%)'
          %(broke_skin,round((broke_skin/df['count'].sum())*100, 0)))
    print('multiple bites: n = %d (%d%%)'
          %(multiple_bites,round((multiple_bites/df['count'].sum())*100, 0)))


    print('\nBite severity (target=people):')
    fields = 'q03_severity, q03_person'
    labels = ['severity', 'person']
    df = createNumericDataFrame(DOG_TABLE, fields, labels, filtered=True)
    df = df[df[labels[1]] == 1]
    df.drop(columns=labels[1], inplace=True)
    df = df.apply(pd.value_counts)
    df.rename(index=str, columns={labels[0]: 'count'}, inplace=True)
    df.columns.name = labels[0]
    teeth_contact = 0
    broke_skin = 0
    multiple_bites = 0
    for index, row in df.iterrows():
        level = float(index)
        if level > 1:
            teeth_contact += row[0]
        if level >= 3:
            broke_skin += row[0]
        if level == 5:
            multiple_bites += row[0]
    print('teeth contact: n = %d (%d%%)'
          %(teeth_contact,round((teeth_contact/df['count'].sum())*100, 0)))
    print('broke skin: n = %d (%d%%)'
          %(broke_skin,round((broke_skin/df['count'].sum())*100, 0)))
    print('multiple bites: n = %d (%d%%)'
          %(multiple_bites,round((multiple_bites/df['count'].sum())*100, 0)))

    print('\nBite severity (target=dogs):')
    fields = 'q03_severity, q03_dog'
    labels = ['severity', 'dog']
    df = createNumericDataFrame(DOG_TABLE, fields, labels, filtered=True)
    df = df[df[labels[1]] == 1]
    df.drop(columns=labels[1], inplace=True)
    df = df.apply(pd.value_counts)
    df.rename(index=str, columns={labels[0]: 'count'}, inplace=True)
    df.columns.name = labels[0]
    teeth_contact = 0
    broke_skin = 0
    multiple_bites = 0
    for index, row in df.iterrows():
        level = float(index)
        if level > 1:
            teeth_contact += row[0]
        if level >= 3:
            broke_skin += row[0]
        if level == 5:
            multiple_bites += row[0]
    print('teeth contact: n = %d (%d%%)'
          %(teeth_contact,round((teeth_contact/df['count'].sum())*100, 0)))
    print('broke skin: n = %d (%d%%)'
          %(broke_skin,round((broke_skin/df['count'].sum())*100, 0)))
    print('multiple bites: n = %d (%d%%)'
          %(multiple_bites,round((multiple_bites/df['count'].sum())*100, 0)))


def bite_severity_by_behavior_problem():
    printTitle('bite severity by behavior problem')
    print('Overall bite severity:')
    fields = []
    labels = []
    for counter, cat in enumerate(FR.categories, 1):
        if counter > 10:
            counter += 1;
        fields.append('q02_main_{}'.format(counter))
        labels.append(cat)
    fields.append('q03_severity')
    labels.append('severity')
    fields = ', '.join(fields)
    df = createNumericDataFrame(DOG_TABLE, fields, labels, filtered=True)
    rngs = []
    rngs.append(df[df['severity'] < 3].drop(columns=['severity']))
    rngs.append(df[df['severity'] >= 3].drop(columns=['severity']))
    rngs.append(df[df['severity'] > 0].drop(columns=['severity']))

    def get_group_prevalence(df):
        df = df.sum().apply(lambda x: (x / len(df.index)) * 100)
        return df.round().astype(int)

    prevs = []
    prevs.append(get_group_prevalence(rngs[0]))
    prevs.append(get_group_prevalence(rngs[1]))
    prevs.append(get_group_prevalence(rngs[2]))

    df = pd.DataFrame(index=prevs[0].index, data={'superf.': prevs[0], 'broke skin': prevs[1],
                                                  'any': prevs[2]})
    df.columns.name = 'Behavior problem'
    print(df)

    print('\nBite severity (target=people):')
    fields = []
    labels = []
    for counter, cat in enumerate(FR.categories, 1):
        if counter > 10:
            counter += 1;
        fields.append('q02_main_{}'.format(counter))
        labels.append(cat)
    fields.append('q03_severity')
    labels.append('severity')
    fields.append('q03_person')
    labels.append('person')
    fields = ', '.join(fields)
    df = createNumericDataFrame(DOG_TABLE, fields, labels, filtered=True)
    df = df[df['person'] == 1]
    df.drop(columns='person', inplace=True)

    rngs = []
    rngs.append(df[df['severity'] < 3].drop(columns=['severity']))
    rngs.append(df[df['severity'] >= 3].drop(columns=['severity']))
    rngs.append(df[df['severity'] > 0].drop(columns=['severity']))

    prevs = []
    prevs.append(get_group_prevalence(rngs[0]))
    prevs.append(get_group_prevalence(rngs[1]))
    prevs.append(get_group_prevalence(rngs[2]))

    df = pd.DataFrame(index=prevs[0].index, data={'superf.': prevs[0], 'broke skin': prevs[1],
                                                  'any': prevs[2]})
    df.columns.name = 'Behavior problem'
    print(df)

    print('\nBite severity (target=dogs):')
    fields = []
    labels = []
    for counter, cat in enumerate(FR.categories, 1):
        if counter > 10:
            counter += 1;
        fields.append('q02_main_{}'.format(counter))
        labels.append(cat)
    fields.append('q03_severity')
    labels.append('severity')
    fields.append('q03_dog')
    labels.append('dog')
    fields = ', '.join(fields)
    df = createNumericDataFrame(DOG_TABLE, fields, labels, filtered=True)
    df = df[df['dog'] == 1]
    df.drop(columns='dog', inplace=True)
    rngs = []
    rngs.append(df[df['severity'] < 3].drop(columns=['severity']))
    rngs.append(df[df['severity'] >= 3].drop(columns=['severity']))
    rngs.append(df[df['severity'] > 0].drop(columns=['severity']))
    prevs = []
    prevs.append(get_group_prevalence(rngs[0]))
    prevs.append(get_group_prevalence(rngs[1]))
    prevs.append(get_group_prevalence(rngs[2]))
    df = pd.DataFrame(index=prevs[0].index, data={'superf.': prevs[0], 'broke skin': prevs[1],
                                                  'any': prevs[2]})
    df.columns.name = 'Behavior problem'
    print(df)


def bite_severity_fear_anxiety():
    printTitle('bite severity by fear/anxiety behavior problems')
    print('Overall bite severity:')
    fields = ', '.join(FR.fields[FR.categories[1]])
    labels = list(FR.labels[FR.categories[1]].values())
    fields += ', q03_severity'
    labels.append('severity')
    df = createNumericDataFrame(DOG_TABLE, fields, labels, filtered=True)

    rngs = []
    rngs.append(df[df['severity'] < 3].drop(columns=['severity']))
    rngs.append(df[df['severity'] >= 3].drop(columns=['severity']))
    rngs.append(df[df['severity'] > 0].drop(columns=['severity']))

    def get_group_prevalence(df):
        df = df.sum().apply(lambda x: (x / len(df.index)) * 100)
        return df.round().astype(int)

    prevs = []
    prevs.append(get_group_prevalence(rngs[0]))
    prevs.append(get_group_prevalence(rngs[1]))
    prevs.append(get_group_prevalence(rngs[2]))

    df = pd.DataFrame(index=prevs[0].index, data={'superf.': prevs[0], 'broke skin': prevs[1],
                                                  'any': prevs[2]})
    df.columns.name = 'Behavior problem'
    print(df)

    print('\nBite severity (target=people):')
    fields = ', '.join(FR.fields[FR.categories[1]])
    labels = list(FR.labels[FR.categories[1]].values())
    fields += ', q03_severity, q03_person'
    labels.append('severity')
    labels.append('person')
    df = createNumericDataFrame(DOG_TABLE, fields, labels, filtered=True)
    df = df[df['person'] == 1]
    df.drop(columns='person', inplace=True)

    rngs = []
    rngs.append(df[df['severity'] < 3].drop(columns=['severity']))
    rngs.append(df[df['severity'] >= 3].drop(columns=['severity']))
    rngs.append(df[df['severity'] > 0].drop(columns=['severity']))

    prevs = []
    prevs.append(get_group_prevalence(rngs[0]))
    prevs.append(get_group_prevalence(rngs[1]))
    prevs.append(get_group_prevalence(rngs[2]))

    df = pd.DataFrame(index=prevs[0].index, data={'superf.': prevs[0], 'broke skin': prevs[1],
                                                  'any': prevs[2]})
    df.columns.name = 'Behavior problem'
    print(df)

    print('\nBite severity (target=dogs):')
    fields = ', '.join(FR.fields[FR.categories[1]])
    labels = list(FR.labels[FR.categories[1]].values())
    fields += ', q03_severity, q03_dog'
    labels.append('severity')
    labels.append('dog')
    df = createNumericDataFrame(DOG_TABLE, fields, labels, filtered=True)
    df = df[df['dog'] == 1]
    df.drop(columns='dog', inplace=True)

    rngs = []
    rngs.append(df[df['severity'] < 3].drop(columns=['severity']))
    rngs.append(df[df['severity'] >= 3].drop(columns=['severity']))
    rngs.append(df[df['severity'] > 0].drop(columns=['severity']))

    prevs = []
    prevs.append(get_group_prevalence(rngs[0]))
    prevs.append(get_group_prevalence(rngs[1]))
    prevs.append(get_group_prevalence(rngs[2]))

    df = pd.DataFrame(index=prevs[0].index, data={'superf.': prevs[0], 'broke skin': prevs[1],
                                                  'any': prevs[2]})
    df.columns.name = 'Behavior problem'
    print(df)


def bite_prevalence_sex_and_neuter_status():
    printTitle('bite prevalence by sex and neuter status')
    fields = ['q03_form_5']
    labels = ['bites']
    fields.extend(('dog_sex', 'dog_spayed'))
    labels.extend(('Gender', 'Neutered'))
    fields = ', '.join(fields)
    df = createNumericDataFrame(DOG_TABLE, fields, labels, filtered=True)

    df_intact_male = df[(df['Gender'] == 1) & (df['Neutered'] == 0)].drop(
        columns=['Gender', 'Neutered'])
    df_neutered_male = df[(df['Gender'] == 1) & (df['Neutered'] == 1)].drop(
        columns=['Gender', 'Neutered'])
    df_intact_female = df[(df['Gender'] == 2) & (df['Neutered'] == 0)].drop(
        columns=['Gender', 'Neutered'])
    df_neutered_female = df[(df['Gender'] == 2) & (df['Neutered'] == 1)].drop(
        columns=['Gender', 'Neutered'])

    def get_group_prevalence(df):
        # We aren't doing anything here except the type conversion.
        df = df.sum().apply(lambda x: (x / 1))
        return df.round().astype(int)

    intact_male_p = get_group_prevalence(df_intact_male)
    neutered_male_p = get_group_prevalence(df_neutered_male)
    intact_female_p = get_group_prevalence(df_intact_female)
    neutered_female_p = get_group_prevalence(df_neutered_female)

    df = pd.DataFrame(index=intact_male_p.index, data={'intact males': intact_male_p,
                                                       'castrated males': neutered_male_p,
                                                       'intact females': intact_female_p,
                                                       'spayed females': neutered_female_p})
    for index, row in df.iterrows():
        for index2, row2 in row.iteritems():
            print('%s: n = %d (%d%%)' %(index2, (row2), round((row2/df.sum().sum())*100, 0)))


def impact_of_gender_on_biting():
    printTitle('impact of gender on biting')
    fields = 'dog_sex, q03_form_5'
    labels = ['sex', 'bites']
    df = createStringDataFrame(DOG_TABLE, fields, labels)
    df = df[df[labels[0]] != '']
    df = df.apply(pd.to_numeric)

    def gender_to_binary_response(x):
        x = int(x)
        if x != 1:
            return 0 # female
        return 1 # male

    df[labels[0]] = df[labels[0]].apply(lambda x: gender_to_binary_response(x))
    boot_df = df.copy()
    # Cross tabulate the relevant columns.
    contingency = pd.crosstab(df[labels[0]], df[labels[1]], margins=False)
    # Execute a chi-squared test of independence.
    c, p, dof, expected = scs.chi2_contingency(contingency, correction=False)
    print('Chi-square Test of Independence:')
    print('chi2 = %f, p = %.2E, dof = %d' %(c, p, dof))
    displayOddsRatio(contingency)

    def get_bootstrap_odds_ratio_ci(data, count=10, alpha=0.95):
        #start = timer()
        arr = np.array([])
        for i in range(count):
            df = data.sample(len(data.index), replace=True)
            contingency = pd.crosstab(df[labels[0]], df[labels[1]], margins=False)
            odds, ci_low, ci_high, tot = getOddsRatioAndConfidenceInterval(contingency)
            arr = np.append(arr, odds)
        arr = np.sort(arr)
        lower = (1-alpha)/2
        upper = alpha+lower
        print('95%% CI: %.2f-%.2f' %(arr[int(lower * len(arr))], arr[int(upper * len(arr))]))
        #end = timer()
        #print('\nbootstrap time: %.2f' %(end-start))

    get_bootstrap_odds_ratio_ci(boot_df, count=NITER)


def impact_of_neuter_status_on_biting():
    printTitle('impact of neuter status on biting')
    fields = 'dog_spayed, q03_form_5'
    labels = ['neutered', 'bites']
    df = createStringDataFrame(DOG_TABLE, fields, labels)
    df = df[df[labels[0]] != '']
    df = df.apply(pd.to_numeric)

    def gender_to_binary_response(x):
        x = int(x)
        if x != 1:
            return 0 # female
        return 1 # male

    df[labels[0]] = df[labels[0]].apply(lambda x: gender_to_binary_response(x))
    boot_df = df.copy()
    # Cross tabulate the relevant columns.
    contingency = pd.crosstab(df[labels[0]], df[labels[1]], margins=False)
    # Execute a chi-squared test of independence.
    c, p, dof, expected = scs.chi2_contingency(contingency, correction=False)
    print('Chi-square Test of Independence:')
    print('chi2 = %f, p = %.2E, dof = %d' %(c, p, dof))
    displayOddsRatio(contingency)

    def get_bootstrap_odds_ratio_ci(data, count=10, alpha=0.95):
        #start = timer()
        arr = np.array([])
        for i in range(count):
            df = data.sample(len(data.index), replace=True)
            contingency = pd.crosstab(df[labels[0]], df[labels[1]], margins=False)
            odds, ci_low, ci_high, tot = getOddsRatioAndConfidenceInterval(contingency)
            arr = np.append(arr, odds)
        arr = np.sort(arr)
        lower = (1-alpha)/2
        upper = alpha+lower
        print('95%% CI: %.2f-%.2f' %(arr[int(lower * len(arr))], arr[int(upper * len(arr))]))
        #end = timer()
        #print('\nbootstrap time: %.2f' %(end-start))

    get_bootstrap_odds_ratio_ci(boot_df, count=NITER)


def main():
    number_of_participants()
    number_of_participating_dogs()
    adjusted_sample()
    impact_of_gender_on_house_soiling_w_fear_anxiety()
    prevalence_of_biting()
    bite_people()
    bite_dogs()
    multiple_bites_per_incident()
    bite_severity()
    bite_severity_by_behavior_problem()
    bite_severity_fear_anxiety()
    bite_prevalence_sex_and_neuter_status()
    impact_of_gender_on_biting()
    impact_of_neuter_status_on_biting()


if __name__ == "__main__":
    main()
