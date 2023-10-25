# encoding: utf-8
#
# 

import pymysql, argparse, getpass, sys, csv


def _get_names(connection, bmid):
    # Get hgnc name
    cursor = connection.cursor()
    cursor.execute('SELECT name FROM biomarker_names WHERE biomarker_id = %s and isHgnc = 1', (bmid,))
    if cursor.rowcount > 0:
        hgnc_name = cursor.fetchone()[0]
    else:
        hgnc_name = '«unknown»'

    # Get default name
    cursor = connection.cursor()
    cursor.execute('SELECT name FROM biomarker_names WHERE biomarker_id = %s and isPrimary = 1', (bmid,))
    if cursor.rowcount > 0:
        default_name = cursor.fetchone()[0]
    else:
        default_name = '«unknown»'
    return hgnc_name, default_name


def generate_publications_report(connection):
    with open('organ-pubs.csv', 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(['BM ID', 'HGNC name', 'Default name', 'Organ', 'PubMed ID', 'Pub title'])
        cursor = connection.cursor()

        cursor.execute('''
            SELECT organ_data_publications.publication_id, organ_data_publications.organ_data_id
            FROM organ_data_publications
        ''')
        for publication_id, organ_data_id in cursor.fetchall():
            cursor2 = connection.cursor()
            cursor2.execute('''
                SELECT
                    organ_data.biomarker_id,
                    organs.name,
                    publications.pubmed_id,
                    publications.title
                FROM
                    organs, publications, organ_data
                WHERE
                    publications.id = %s AND
                    organ_data.id = %s AND
                    organ_data.organ_id = organs.id
            ''', (publication_id, organ_data_id))
            for bmid, organ_name, pubmed, pub_title in cursor2.fetchall():
                hgnc_name, default_name = _get_names(connection, bmid)
                writer.writerow([bmid, hgnc_name, default_name, organ_name, pubmed, pub_title])


def generate_reports(connection):
    generate_publications_report(connection)
    # No need for this one, there's only 1
    # generate_resources_report(connection)


def main():
    parser = argparse.ArgumentParser(description="Show organ-specifics'")
    parser.add_argument('-H', '--host', default='localhost', help='MySQL host; default %(default)s')
    parser.add_argument('-D', '--database', default='cbmdb', help='MySQL database, default %(default)s')
    parser.add_argument('-u', '--user', default='cbmdb', help='MySQL user; default %(default)s')
    parser.add_argument('-p', '--password', help='MySQL password; will be prompted if not given')
    args = parser.parse_args()
    user = args.user
    password = args.password if args.password else getpass.getpass(u'Password for MySQL user "{}": '.format(user))
    connection = pymysql.connect(host=args.host, user=user, password=password, database=args.database)
    generate_reports(connection)
    sys.exit(0)


if __name__ == '__main__':
    main()
