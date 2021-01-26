# encoding: utf-8

import argparse, getpass, pymysql, sys, csv


def generateDescriptionReport(connection):
    cursor = connection.cursor()
    cursor.execute("SET CHARACTER_SET_RESULTS='latin1'")
    cursor.execute('''SELECT biomarkers.id, biomarkers.name, biomarkers.description FROM biomarkers''')
    with open('results.csv', 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['ID', 'Name', 'HGNC', 'Alternative Facts', 'Description'])

        for biomarkerRow in cursor.fetchall():
            number, name, description = biomarkerRow

            # HGNC name
            subCursor = connection.cursor()
            subCursor.execute("SET CHARACTER_SET_RESULTS='latin1'")
            subCursor.execute('''
                SELECT
                    biomarker_names.name
                FROM
                    biomarker_names
                WHERE
                    biomarker_names.biomarker_id = %s AND
                    biomarker_names.isHgnc = 1
            ''', (number,))
            hgnc = 'unknown' if subCursor.rowcount == 0 else subCursor.fetchall()[0][0]

            # Aliases
            subCursor.execute('''
                SELECT
                    biomarker_names.name
                FROM
                    biomarker_names
                WHERE
                    biomarker_names.biomarker_id = %s AND
                    biomarker_names.isHgnc = 0
                ORDER BY
                    biomarker_names.name
            ''', (number,))
            aliases = [i[0] for i in subCursor.fetchall()]
            writer.writerow([str(number), name, hgnc, ', '.join(sorted(list(aliases))), description])


def main():
    parser = argparse.ArgumentParser(description="Make description report")
    parser.add_argument('-H', '--host', default='localhost', help='MySQL host; default %(default)s')
    parser.add_argument('-D', '--database', default='cbmdb', help='MySQL database, default %(default)s')
    parser.add_argument('-u', '--user', default='cbmdb', help='MySQL user; default %(default)s')
    parser.add_argument('-p', '--password', help='MySQL password; will be prompted if not given')
    args = parser.parse_args()
    user = args.user
    password = args.password if args.password else getpass.getpass(u'Password for MySQL user "{}": '.format(user))
    connection = pymysql.connect(host=args.host, user=user, password=password, database=args.database)
    generateDescriptionReport(connection)
    sys.exit(0)
