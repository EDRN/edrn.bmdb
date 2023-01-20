import pymysql, argparse, getpass, sys, csv


# mysql --user=cbmdb --password --batch --execute='
# SELECT
#     biomarkers.id, biomarkers.name, organs.name, study_data.phase, studies.FHCRC_ID, studies.title
# FROM
#     biomarkers, organs, organ_data, studies, study_data
# WHERE
#     organ_data.organ_id = organs.id AND
#     organ_data.biomarker_id = biomarkers.id AND
#     study_data.organ_data_id = organ_data.id AND
#     study_data.study_id = studies.id
# ;' cbmdb | sed -e ""s/'/\'/"" | sed -e 's/\t/"",""/g;s/^/""/;s/$/""/;s/\n//g'


def generate_report(connection):
    with open('zombie.csv', 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(['BM ID', 'HGNC name', 'Def name', 'Organ', 'Organs→Protocol Phase', 'Protocol ID', 'Protocol Title'])
        cursor = connection.cursor()

        cursor.execute('''
            SELECT
                biomarkers.id, organs.name, study_data.phase, studies.FHCRC_ID, studies.title
            FROM
                biomarkers, organs, organ_data, studies, study_data
            WHERE
                organ_data.organ_id = organs.id AND
                organ_data.biomarker_id = biomarkers.id AND
                study_data.organ_data_id = organ_Data.id AND
                study_data.study_id = studies.id
        ''')
        for bmid, organ, phase, prot_id, prot_title in cursor.fetchall():
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
            writer.writerow([bmid, hgnc_name, default_name, organ, phase, prot_id, prot_title])


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
