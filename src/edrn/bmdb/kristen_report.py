import pymysql, argparse, getpass, sys, csv


def generate_report(connection):
    with open('kristen.csv', 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(['BM ID', 'HGNC name', 'Def name', 'Organ', 'Organs→Protocol Phase', 'Protocol ID', 'Protocol Title'])
        cursor = connection.cursor()

        cursor.execute('SELECT biomarkers.id FROM biomarkers ORDER BY biomarkers.id')
        for bmid in cursor.fetchall():
            bmid = bmid[0]
            # Get the hgnc name
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

            # Get all the organs
            cursor2.execute('''
                SELECT
                    organs.name, organ_data.id
                FROM
                    organs, organ_data
                WHERE
                    organ_data.biomarker_id = %s
                ''', (bmid,))
            for organ_name, organ_data_id in cursor2.fetchall():
                cursor3 = connection.cursor()
                cursor3.execute('''
                    SELECT
                        study_data.phase, studies.FHCRC_ID, studies.title
                    FROM
                        study_data, studies
                    WHERE
                        study_data.organ_data_id = %s AND
                        study_data.study_id = studies.id
                ''', (organ_data_id,))
                for phase, protocol_id, protocol_title in cursor3.fetchall():
                    writer.writerow([
                        bmid, hgnc_name, default_name, organ_name, phase, protocol_id, protocol_title
                    ])  


def main():
    parser = argparse.ArgumentParser(description="Kristen's Report")
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

