# encoding: utf-8

import argparse, getpass, pymysql, sys


def copyStudies(connection):
    cursor = connection.cursor()
    cursor.execute("SET CHARACTER_SET_RESULTS='latin1'")
    cursor.execute('''
        SELECT
            study_data.phase,
            study_data.sensitivity,
            study_data.specificity,
            study_data.sensspecdetail,
            study_data.npv,
            study_data.ppv,
            study_data.prevalence,
            study_data.assay,
            study_data.technology,
            study_data.study_id,
            organ_data.biomarker_id
        FROM
            study_data,
            organ_data
        WHERE
            study_data.organ_data_id = organ_data.id
    ''')
    for row in cursor:
        phase, sens, spec, det, npv, ppv, prev, assay, tech, studyID, number = row
        subCursor = connection.cursor()
        subCursor.execute("SET CHARACTER_SET_RESULTS='latin1'")
        subCursor.execute('''
            SELECT biomarker_study_data.id
            FROM biomarker_study_data
            WHERE biomarker_study_data.biomarker_id = %s AND biomarker_study_data.study_id = %s
        ''', ((number, studyID)))
        if subCursor.rowcount == 0:
            print(f'Adding study {studyID} to biomarker {number}')
            subCursor.execute('''
                INSERT INTO biomarker_study_data (
                        phase, sensitivity, specificity, sensspecdetail, npv, ppv, prevalence,
                        assay, technology, biomarker_id, study_id
                ) VALUES (
                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                )
            ''', (phase, sens, spec, det, npv, ppv, prev, assay, tech, number, studyID))


def main():
    parser = argparse.ArgumentParser(description="Copy studies from organ level to biomarker level")
    parser.add_argument('-H', '--host', default='localhost', help='MySQL host; default %(default)s')
    parser.add_argument('-D', '--database', default='cbmdb', help='MySQL database, default %(default)s')
    parser.add_argument('-u', '--user', default='cbmdb', help='MySQL user; default %(default)s')
    parser.add_argument('-p', '--password', help='MySQL password; will be prompted if not given')
    args = parser.parse_args()
    user = args.user
    password = args.password if args.password else getpass.getpass(u'Password for MySQL user "{}": '.format(user))
    connection = pymysql.connect(host=args.host, user=user, password=password, database=args.database)
    copyStudies(connection)
    sys.exit(0)
