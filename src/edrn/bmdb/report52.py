# encoding: utf-8
#
# See https://github.com/EDRN/biomarker-database/issues/52

import pymysql, argparse, getpass, sys, csv


def generate_report(connection):
    with open('report52.csv', 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(['BM ID', 'HGNC name', 'Def name', 'Organ', 'Protocol ID', 'Basic QA', 'Organ QA', 'Protocol Phase'])
        cursor = connection.cursor()

        cursor.execute('SELECT biomarkers.id, biomarkers.qastate FROM biomarkers ORDER BY biomarkers.id')
        for bmid, basic_qa in cursor.fetchall():
            # Get hgnc name
            cursor2 = connection.cursor()
            cursor2.execute('SELECT name FROM biomarker_names WHERE biomarker_id = %s and isHgnc = 1', (bmid,))
            if cursor2.rowcount > 0:
                hgnc_name = cursor2.fetchone()[0]
            else:
                hgnc_name = '«unknown»'

            # Get default name
            cursor2 = connection.cursor()
            cursor2.execute('SELECT name FROM biomarker_names WHERE biomarker_id = %s and isPrimary = 1', (bmid,))
            if cursor2.rowcount > 0:
                default_name = cursor2.fetchone()[0]
            else:
                default_name = '«unknown»'

            # From biomarker → organ it's organ_data.biomarker_id via biomarker.biomarker.id
            # Organ name comes from organs.name via organ_data.organ_id to organs.id
            # study_data has organ_data_id → organ_data.id and has study_id → studies.id

            cursor2 = connection.cursor()
            cursor2.execute('''
                SELECT
                    organs.name, studies.FHCRC_ID, organ_data.qastate, study_data.phase
                FROM
                    organs, organ_data, studies, study_data
                WHERE
                    organs.id = organ_data.organ_id AND
                    organ_data.biomarker_id = %s AND
                    study_data.organ_data_id = organ_data.id AND
                    study_data.study_id = studies.id
                ORDER BY organs.name, studies.FHCRC_ID
            ''', (bmid,))
            for organ, protocol_id, organ_qa, protocol_phase in cursor2.fetchall():
                writer.writerow([bmid, hgnc_name, default_name, organ, protocol_id, basic_qa, organ_qa, protocol_phase])


def main():
    parser = argparse.ArgumentParser(description="Maureen's 'Report 51'")
    parser.add_argument('-H', '--host', default='localhost', help='MySQL host; default %(default)s')
    parser.add_argument('-D', '--database', default='cbmdb', help='MySQL database, default %(default)s')
    parser.add_argument('-u', '--user', default='cbmdb', help='MySQL user; default %(default)s')
    parser.add_argument('-p', '--password', help='MySQL password; will be prompted if not given')
    args = parser.parse_args()
    user = args.user
    password = args.password if args.password else getpass.getpass(u'Password for MySQL user "{}": '.format(user))
    connection = pymysql.connect(host=args.host, user=user, password=password, database=args.database)
    generate_report(connection)
    sys.exit(0)


if __name__ == '__main__':
    main()
