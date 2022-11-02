# encoding: utf-8
#
# See https://github.com/EDRN/biomarker-database/issues/51

import pymysql, argparse, getpass, sys, csv


def generate_report(connection):
    with open('report51.csv', 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(['BM ID', 'HGNC name', 'Default name', 'Description', 'Publication', 'Resource'])
        cursor = connection.cursor()

        cursor.execute('SELECT biomarkers.id, biomarkers.description FROM biomarkers ORDER BY biomarkers.id')
        for bmid, description in cursor.fetchall():
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

            # Get publications
            #
            # -   biomarkers_publications links a single biomarker_id with publication_ids
            # -   biomarker_study_data_publications links a single biomarker_study_data_id with publication_ids 
            #     -   and biomarker_study_data links to a biomarker_id
            # -   organ_data_publications links a single organ_data_id with publication_ids
            #     -   and organ_data links to a biomarker_id
            # -   And publications has pubmed_id, title

            bmdb_pub_ids = set()
            cursor2.execute('SELECT publication_id FROM biomarkers_publications WHERE biomarker_id = %s''', (bmid,))
            for i in cursor2.fetchall():
                bmdb_pub_ids.add(i[0])

            cursor2 = connection.cursor()
            cursor2.execute('''
                SELECT
                    biomarker_study_data_publications.publication_id
                FROM
                    biomarker_study_data_publications, biomarker_study_data
                WHERE
                    biomarker_study_data.biomarker_id = %s
            ''', (bmid,))
            for i in cursor2.fetchall():
                bmdb_pub_ids.add(i[0])

            cursor2 = connection.cursor()
            cursor2.execute('''
                SELECT
                    organ_data_publications.publication_id
                FROM
                    organ_data_publications, organ_data
                WHERE
                    organ_data.biomarker_id = %s
            ''', (bmid,))
            for i in cursor2.fetchall():
                bmdb_pub_ids.add(i[0])

            # Now output all the pubs
            cursor2 = connection.cursor()
            cursor2.execute('SELECT title, pubmed_id FROM publications WHERE id in %s ORDER BY title', bmdb_pub_ids)
            for title, pubmed_id in cursor2.fetchall():
                writer.writerow([bmid, hgnc_name, default_name, description, f'{title} ({pubmed_id})', '…'])

            # Get resources
            #
            # -   biomarker_resources has biomarker_id and URL
            # -   biomarker_study_data_resources has URL and biomarker_study_data_id
            #     -   and biomarker_study_data links to a biomarker_id
            # -   organ_data_resources has URL and organ_data_id
            #     -   and organ_data links to a biomarker_id

            urls = set()
            cursor2 = connection.cursor()
            cursor2.execute('SELECT URL from biomarker_resources WHERE biomarker_id = %s', (bmid,))
            for i in cursor2.fetchall():
                urls.add(i[0])

            cursor2 = connection.cursor()
            cursor2.execute('''
                SELECT biomarker_study_data_resources.URL
                FROM biomarker_study_data_resources, biomarker_study_data
                WHERE biomarker_study_data_resources.biomarker_study_data_id = biomarker_study_data.id
                AND biomarker_study_data.biomarker_id = %s
            ''', (bmid,))
            for i in cursor2.fetchall():
                urls.add(i[0])

            cursor2 = connection.cursor()
            cursor2.execute('''
                SELECT organ_data_resources.URL
                FROM organ_data_resources, organ_data
                WHERE organ_data_resources.organ_data_id = organ_data.id
                AND organ_data.biomarker_id = %s
            ''', (bmid,))
            for i in cursor2.fetchall():
                urls.add(i[0])
            urls = sorted(list(urls))
            for url in urls:
                writer.writerow([bmid, hgnc_name, default_name, description, '…', url])


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


# biomarkers id ("number"), name … ignore "shortName" it's blank for all
# bimarker_names biomarker_id ("number"), name … bonus names to include

# BIOMARKERS
# | id           | int(10) unsigned | NO   | PRI | NULL    | auto_increment |
# | name         | varchar(200)     | NO   |     | NULL    |                |
# | shortName    | varchar(20)      | NO   |     | NULL    |                |
# | created      | datetime         | NO   |     | NULL    |                |
# | modified     | datetime         | NO   |     | NULL    |                |
# | description  | text             | NO   |     | NULL    |                |
# | qastate      | varchar(25)      | NO   |     | NULL    |                |
# | phase        | varchar(25)      | NO   |     | NULL    |                |
# | security     | varchar(25)      | NO   |     | NULL    |                |
# | type         | varchar(25)      | NO   |     | NULL    |                |
# | isPanel      | int(10) unsigned | NO   |     | 0       |                |
# | panelID      | int(10) unsigned | NO   |     | NULL    |                |
# | curatorNotes | text             | NO   |     | NULL    |                |
#
#
# BIOMARKER_NAMES
# | id           | int(10) unsigned    | NO   | PRI | NULL    | auto_increment |
# | biomarker_id | int(10) unsigned    | NO   | MUL | NULL    |                |
# | name         | varchar(255)        | NO   |     | NULL    |                |
# | isPrimary    | int(10) unsigned    | NO   | MUL | NULL    |                |
# | isHgnc       | tinyint(3) unsigned | NO   |     | 0       |                |
#
#
# BIOMARKER_STUDY_DATA (use phase, study_id link to studies, biomarker_id link to "number")
# | id             | int(10) unsigned | NO   | PRI | NULL    | auto_increment |
# | phase          | varchar(25)      | NO   |     | NULL    |                |
# | sensitivity    | int(11)          | NO   |     | NULL    |                |
# | specificity    | int(11)          | NO   |     | NULL    |                |
# | sensspecdetail | text             | NO   |     | NULL    |                |
# | npv            | int(11)          | NO   |     | NULL    |                |
# | ppv            | int(11)          | NO   |     | NULL    |                |
# | prevalence     | float            | NO   |     | NULL    |                |
# | assay          | varchar(80)      | NO   |     | NULL    |                |
# | technology     | varchar(80)      | NO   |     | NULL    |                |
# | biomarker_id   | int(10) unsigned | NO   | MUL | NULL    |                |
# | study_id       | int(10) unsigned | NO   | MUL | NULL    |                |
#
#
# STUDIES (use FHCRC_ID)
# | id                  | int(10) unsigned    | NO   | PRI | NULL         | auto_increment |
# | EDRNID              | int(10) unsigned    | NO   | MUL | NULL         |                |
# | FHCRC_ID            | int(10) unsigned    | NO   | MUL | NULL         |                |
# | DMCC_ID             | varchar(80)         | NO   | MUL | NULL         |                |
# | isEDRN              | tinyint(3) unsigned | NO   | MUL | 1            |                |
# | title               | varchar(200)        | NO   | UNI | NULL         |                |
# | studyAbstract       | text                | NO   |     | NULL         |                |
# | studyObjective      | text                | NO   |     | NULL         |                |
# | studySpecificAims   | text                | NO   |     | NULL         |                |
# | studyResultsOutcome | text                | NO   |     | NULL         |                |
# | collaborativeGroups | varchar(200)        | NO   |     | NULL         |                |
# | bioPopChar          | varchar(30)         | NO   |     | NULL         |                |
# | BPCDescription      | text                | NO   |     | NULL         |                |
# | design              | varchar(30)         | NO   |     | NULL         |                |
# | designDescription   | text                | NO   |     | NULL         |                |
# | biomarkerStudyType  | varchar(30)         | NO   |     | Unregistered |                |
# | altName             | varchar(200)        | NO   |     | NULL         |                |
