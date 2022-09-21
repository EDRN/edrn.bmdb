# encoding: utf-8

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


@total_ordering
class Triple(object):
    def __init__(self, name, protocol, phase):
        self.name, self.protocol, self.phase = name, protocol, phase
    def __hash__(self):
        return hash(self.name.lower()) ^ hash(self.protocol) ^ hash(self.phase)
    def __lt__(self, other):
        if self.name.lower() < other.name.lower():
            return True
        elif self.name.lower == other.name.lower():
            if self.protocol < other.protocol:
                return True
            elif self.protocol == other.protocol:
                return self.phase < other.phase
        return False
    def __eq__(self, other):
        return self.name.lower() == other.name.lower() and self.protocol == other.protocol and self.phase == other.phase
    def __repr__(self):
        return f'<{self.__class__.__name__}(name={self.name},protocol={self.protocol},phase={self.phase})>'


def _getBiomarkerDetail(connection, name):
    '''Given a potential ``name`` of a biomarker, look it up n the DB ``connection``
    and return a triple of its biomarker ID number, its description, and a sequence
    of doubles of (protocol ID, phase)
    '''
    cursor = connection.cursor()
    cursor.execute("SET CHARACTER_SET_RESULTS='latin1'")
    cursor.execute('''SELECT id, description FROM biomarkers WHERE name = %s''', (name,))
    if cursor.rowcount == 0:
        cursor.execute('''SELECT biomarker_id FROM biomarker_names WHERE name = %s''', (name,))
        if cursor.rowcount == 0:
            return None
        else:
            number = cursor.fetchone()[0]
            cursor.execute('''SELECT description FROM biomarkers WHERE id = %s''', (number,))
            description = cursor.fetchone()[0].strip()
    else:
        number, description = cursor.fetchone()
        description = description.strip()
    cursor.execute('''
        SELECT
            studies.FHCRC_ID,
            biomarker_study_data.phase
        FROM
            biomarkers,
            studies,
            biomarker_study_data
        WHERE
            biomarkers.id = %s AND
            biomarker_study_data.biomarker_id = biomarkers.id AND
            studies.id = biomarker_study_data.study_id
    ''', (number,))
    return number, description, [(i[0], _dbPhases.get(i[1], 0)) for i in cursor.fetchall()]


def _getDatabaseMarkers(connection):
    cursor = connection.cursor()
    cursor.execute("SET CHARACTER_SET_RESULTS='latin1'")
    # Make a table of all (biomaker name, protocol ID, phase) from the database
    markers = set()
    cursor.execute('''SELECT id, name FROM biomarkers''')
    for number, name in cursor.fetchall():
        name = name.strip()
        names = {name}
        subcursor = connection.cursor()
        subcursor.execute("SET CHARACTER_SET_RESULTS='latin1'")
        subcursor.execute('''SELECT name FROM biomarker_names WHERE biomarker_id = %s''', (number,))
        names |= set([i[0].strip() for i in subcursor.fetchall()])
        subcursor.execute('''
            SELECT
                studies.FHCRC_ID,
                biomarker_study_data.phase
            FROM
                studies,
                biomarker_study_data
            WHERE
                biomarker_study_data.study_id = studies.id AND
                biomarker_study_data.biomarker_id = %s
        ''', (number,))
        for protocolID, phase in subcursor.fetchall():
            phase = _dbPhases.get(phase, 0)
            for name in names:
                markers.add(Triple(name, protocolID, phase))
    return markers


def _getCSVMarkers(maureenfile):
    markers = set()
    reader = csv.reader(maureenfile)
    lineno = 0
    for name, organ, protocolID, pi, phase in reader:
        lineno += 1
        if 'Jackie' in name and 'Jackie' in organ: continue
        try:
            protocolID = int(protocolID)
        except ValueError:
            pass
        name = name.strip()
        phase = _csvPhases[phase]
        markers.add(Triple(name, protocolID, phase))
    return markers


def generateReport34(connection, maureenfile):
    databaseMarkers = _getDatabaseMarkers(connection)
    csvMarkers = _getCSVMarkers(maureenfile)
    diffs = csvMarkers - databaseMarkers
    with open('triples-correlation.csv', 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow([
            'CSV triple: name',
            'CSV triple: protocol ID',
            'CSV triple: phase',
            'What we have in BMDB: #',
            'What we have in BMDB: protocols + phases',
            'What we have in BMDB: description'
        ])
        for t in diffs:  # t = Triple
            details = _getBiomarkerDetail(connection, t.name)
            if details is None:
                writer.writerow([t.name, t.protocol, t.phase, 'not found', 'not found', 'not found'])
            else:
                number, desc, protocols = details
                protocols = '; '.join([f'{i[0]} @ phase {i[1]}' for i in protocols])
                writer.writerow([t.name, t.protocol, t.phase, number, protocols, desc])


def main():
    parser = argparse.ArgumentParser(description="Maureen's 'Report 34' correlation")
    parser.add_argument('-H', '--host', default='localhost', help='MySQL host; default %(default)s')
    parser.add_argument('-D', '--database', default='cbmdb', help='MySQL database, default %(default)s')
    parser.add_argument('-u', '--user', default='cbmdb', help='MySQL user; default %(default)s')
    parser.add_argument('-p', '--password', help='MySQL password; will be prompted if not given')
    parser.add_argument('maureenfile', help="Maureen's file", type=argparse.FileType('r', encoding='utf-8'))
    args = parser.parse_args()
    user = args.user
    password = args.password if args.password else getpass.getpass(u'Password for MySQL user "{}": '.format(user))
    connection = pymysql.connect(host=args.host, user=user, password=password, database=args.database)
    generateReport34(connection, args.maureenfile)
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
