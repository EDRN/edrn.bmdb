# encoding: utf-8
#
# See https://github.com/EDRN/biomarker-database/issues/50

from functools import total_ordering
import pymysql, argparse, getpass, sys, csv


_dbPhases = {
    'One': 1,
    'Two': 2,
    'Three': 3,
    'Four': 4,
    'Five': 5
}
_csvPhases = {
    'Phase 1': 1,
    'Phase 2': 2,
    'Phase 3': 3,
    'Phase 4': 4,
    'Phase 5': 5
}


def generateReport50(connection):
    with open('report50.csv', 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(['BM ID', 'BM Name', 'Organ', 'Prot ID', 'Prot Title', 'Phase'])
        cursor = connection.cursor()

        cursor.execute('''
            SELECT
                biomarkers.id, biomarkers.name, organs.name, studies.FHCRC_ID, studies.TITLE, organ_data.phase
            FROM
                biomarkers, organ_data, organs, study_data, studies
            WHERE
                organ_data.biomarker_id = biomarkers.id AND
                organs.id = organ_data.organ_id AND
                study_data.organ_data_id = organ_data.id AND
                studies.id = study_data.study_id
            ORDER BY
                biomarkers.id,
                organs.name,
                studies.FHCRC_ID
        ''')

        for bmid, bm_name, organ_name, study_id, study_title, phase in cursor.fetchall():
            phase = _dbPhases.get(phase, '0')
            cursor2 = connection.cursor()
            cursor2.execute('SELECT name FROM biomarker_names WHERE biomarker_id = %s AND isHgnc = 1', (bmid,))
            if cursor2.rowcount > 0:
                bm_name = cursor2.fetchone()[0]
            writer.writerow([bmid, bm_name, organ_name, study_id, study_title, phase])


def main():
    parser = argparse.ArgumentParser(description="Maureen's 'Report 50'")
    parser.add_argument('-H', '--host', default='localhost', help='MySQL host; default %(default)s')
    parser.add_argument('-D', '--database', default='cbmdb', help='MySQL database, default %(default)s')
    parser.add_argument('-u', '--user', default='cbmdb', help='MySQL user; default %(default)s')
    parser.add_argument('-p', '--password', help='MySQL password; will be prompted if not given')
    args = parser.parse_args()
    user = args.user
    password = args.password if args.password else getpass.getpass(u'Password for MySQL user "{}": '.format(user))
    connection = pymysql.connect(host=args.host, user=user, password=password, database=args.database)
    generateReport50(connection)
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
