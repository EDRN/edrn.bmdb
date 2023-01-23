# encoding: utf-8

from functools import total_ordering
import pymysql, argparse, getpass, sys, csv


_phasing = {
    'One': 1,
    'Two': 2,
    'Three': 3,
    'Four': 4,
    'Five': 5
}


@total_ordering
class BiomarkerDetail(object):
    def __init__(self, name, organ, protocolID, phase, pi):
        self.name, self.organ, self.protocolID = name, organ, protocolID
        self.phase, self.pi = phase, pi
    def __hash__(self):
        return hash(self.name) ^ hash(self.organ) ^ hash(self.protocolID)
    def __lt__(self, other):
        if self.name < other.name:
            return True
        elif self.organ < other.organ:
            return True
        elif self.protocolID < other.protocolID:
            return True
        else:
            return False
    def __eq__(self, other):
        return self.name == other.name and self.organ == other.organ and self.protocolID == other.protocolID
    def __repr__(self):
        return f'<{self.__class__.__name__}({self.name},{self.organ},{self.protocolID})>'
    def row(self):
        return [self.name, self.organ, self.protocolID, self.phase, self.pi]


def quicklyCorrelate(connection, maureenFile):
    # study_data has organ_data_id and study_id
    # studies has id and EDRNID
    # organ_data has biomarker_id

    cursor = connection.cursor()
    cursor.execute("SET CHARACTER_SET_RESULTS='latin1'")

    notFoundInDB = set()
    maureenDumpReader = csv.reader(maureenFile)
    for row in maureenDumpReader:
        if row[0] == 'Biomarker Name' and row[1] == 'Organ' and row[2] == 'Protocol ID': continue
        name, organ, protocolID = row[0].strip(), row[1].strip(), row[2].strip()
        phase, pi = int(row[3][6]), row[4].strip()
        try:
            intProtocolID = int(protocolID)
        except ValueError:
            intProtocolID = -1
        bd = BiomarkerDetail(name, organ, protocolID, phase, pi)

        # First, see if the name can be found
        number = None
        cursor.execute('SELECT id FROM biomarkers WHERE name = %s or shortName = %s', (name, name))
        if cursor.rowcount == 0:
            cursor.execute('SELECT biomarker_id FROM biomarker_names WHERE name = %s', (name,))
            if cursor.rowcount != 0:
                number = cursor.fetchall()[0][0]
        else:
            number = cursor.fetchall()[0][0]
        if number is None:
            notFoundInDB.add(bd)
            continue

        # Okay, got a name, find the organ and protocol
        cursor.execute('''
            SELECT
                study_data.id
            FROM
                study_data,
                organs,
                organ_data,
                studies
            WHERE
                organs.name = %s AND
                organs.id = organ_data.organ_id AND
                study_data.organ_data_id = organ_data.id AND
                studies.id = study_data.study_id AND
                organ_data.biomarker_id = %s AND
                (studies.FHCRC_ID = %s OR studies.DMCC_ID = %s)
        ''', (organ, number, intProtocolID, protocolID))
        if cursor.rowcount == 0:
            notFoundInDB.add(bd)

    # Write the missing
    with open('in-spreadsheet-not-in-db.csv', 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(['Name', 'Organ', 'Protocol ID', 'Phase', 'PI'])
        for bd in notFoundInDB:
            writer.writerow(bd.row())


def correlate(connection, danFile, maureenFile):
    # inDumpNotInDB: just a set of biomarker names
    # inDumpButDifferentOrgans: biomarker name to set of organs
    # inDumpButDifferentPhases: biomarker name to organ to phase
    inDumpNotInDB, inDumpButDifferentOrgans, inDumpButDifferentPhases = set(), {}, {}

    danDump = {}
    danDumpReader = csv.reader(danFile)
    for row in danDumpReader:
        if 'Biomarker' in row[0] and 'Organ' in row[1] and 'Protocol' in row[2]:
            # It's the header, skip it
            continue
        # Save a double of the biomarker name and the organ
        name, organ = row[0].strip().lower(), row[1].strip().lower()
        organs = danDump.get(name, set())
        organs.add(organ)
        danDump[name] = organs

    maureenDump = {}
    maureenDumpReader = csv.reader(maureenFile)
    for row in maureenDumpReader:
        if 'Biomarker Name' in row[0] and 'Organ' in row[1] and 'Protocol' in row[2]: continue
        name, organ, phase = row[0].strip().lower(), row[1].strip().lower(), int(row[6].split(' ')[1])
        organPhases = maureenDump.get(name, set())
        organPhases.add((organ, phase))
        maureenDump[name] = organPhases

    # Okay, first check dump names versus db names
    cursor = connection.cursor()
    cursor.execute("SET CHARACTER_SET_RESULTS='latin1'")
    for dumpName, dumpOrgans in danDump.items():
        maureenOrgansPlusPhases = maureenDump[dumpName]
        number = None
        cursor.execute('''
            SELECT biomarkers.id FROM biomarkers WHERE biomarkers.name LIKE %s OR biomarkers.shortName LIKE %s
        ''', (dumpName, dumpName))
        if cursor.rowcount:
            number = cursor.fetchone()[0]
        else:
            cursor.execute('SELECT biomarker_names.biomarker_id FROM biomarker_names WHERE name LIKE %s', (dumpName,))
            if cursor.rowcount:
                number = cursor.fetchone()[0]
        if number is None:
            inDumpNotInDB.add(dumpName)
        else:
            # Now check if the organs are represented
            subcursor = connection.cursor()
            subcursor.execute("SET CHARACTER_SET_RESULTS='latin1'")
            subcursor.execute('''
                SELECT organs.name FROM organs, organ_data
                WHERE organs.id = organ_data.organ_id AND organ_data.biomarker_id = %s
            ''', (number, ))
            dbOrgans = set([i[0].strip().lower() for i in subcursor.fetchall()])
            onlyInDump, onlyInDB = dumpOrgans - dbOrgans, dbOrgans - dumpOrgans
            if len(onlyInDump) > 0 or len(onlyInDB) > 0:
                inDumpButDifferentOrgans[dumpName] = (dumpOrgans, dbOrgans)

            # Now check if th phases of the organs are different
            subcursor.execute('''
                SELECT organs.name, organ_data.phase FROM organs, organ_data
                WHERE organs.id = organ_Data.organ_id AND organ_data.biomarker_id = %s
            ''', (number,))
            dbOrganPhases = set()
            for row in subcursor.fetchall():
                organ, phase = row[0].strip().lower(), _phasing.get(row[1], '«no phase»')
                dbOrganPhases.add((organ, phase))
            onlyInDump, onlyInDB = maureenOrgansPlusPhases - dbOrganPhases, dbOrgans - maureenOrgansPlusPhases
            if len(onlyInDump) > 0 or len(onlyInDB) > 0:
                inDumpButDifferentPhases[dumpName] = (maureenOrgansPlusPhases, dbOrganPhases)

    # Now the other direction
    allDBNames = set()
    cursor.execute('SELECT name, shortName FROM biomarkers')
    for name, shortName in cursor.fetchall():
        name, shortName = name.strip(), shortName.strip()
        allDBNames.add(name.strip().lower())
        allDBNames.add(shortName.strip().lower())
    cursor.execute('SELECT name FROM biomarker_names')
    allDBNames |= set([i[0].strip().lower() for i in cursor.fetchall()])
    allDumpNames = set(danDump.keys())
    inDBNotInDump = allDBNames - allDumpNames

    # Make reports
    with open('in-dump-not-in-db.csv', 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(['Found in dump but missing in BMDB'])
        for name in sorted(list(inDumpNotInDB)):
            writer.writerow([name])
    with open('in-dump-but-differing-organs.csv', 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(['Found in Dump and BMDB', 'Dump Organs', 'DB Organs'])
        for name in sorted(inDumpButDifferentOrgans.keys()):
            dumpOrgans, dbOrgans = inDumpButDifferentOrgans[name]
            dumpOrgans = '|'.join(sorted(list(dumpOrgans)))
            dbOrgans = '|'.join(sorted(list(dbOrgans)))
            writer.writerow([name, dumpOrgans, dbOrgans])
    with open('in-db-not-in-dump.csv', 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(['Found in BMDB but not in dump'])
        for name in sorted(list(inDBNotInDump)):
            writer.writerow([name])


def main():
    parser = argparse.ArgumentParser(description="Correlate Focus BMDB with Dan's file")
    parser.add_argument('-H', '--host', default='localhost', help='MySQL host; default %(default)s')
    parser.add_argument('-D', '--database', default='cbmdb', help='MySQL database, default %(default)s')
    parser.add_argument('-u', '--user', default='cbmdb', help='MySQL user; default %(default)s')
    parser.add_argument('-p', '--password', help='MySQL password; will be prompted if not given')
    parser.add_argument('-d', '--danfile', help="Dan's file", type=argparse.FileType('r', encoding='utf-8'))
    parser.add_argument('maureenfile', help="Maureen's file", type=argparse.FileType('r', encoding='utf-8'))
    args = parser.parse_args()
    user = args.user
    password = args.password if args.password else getpass.getpass(u'Password for MySQL user "{}": '.format(user))
    connection = pymysql.connect(host=args.host, user=user, password=password, database=args.database)
    if args.danfile is not None:
        correlate(connection, args.danfile, args.maureenfile)
    else:
        quicklyCorrelate(connection, args.maureenfile)
    sys.exit(0)


if __name__ == '__main__':
    main()
