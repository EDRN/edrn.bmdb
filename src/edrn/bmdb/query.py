# encoding: utf-8
#
# Do generic query of some sort

import pymysql, argparse, getpass, sys, logging, csv, codecs


_argParser = argparse.ArgumentParser(description='Fix genenames.org links in the biomarker database')
_argParser.add_argument('-H', '--host', default='localhost', help='MySQL host; default %(default)s')
_argParser.add_argument('-D', '--database', default='cbmdb', help='MySQL database, default %(default)s')
_argParser.add_argument('-u', '--user', default='cbmdb', help='MySQL user; default %(default)s')
_argParser.add_argument('-p', '--password', help='MySQL password; will be prompted if not given')


def datasets(connection):
    cursor = connection.cursor()
    cursor.execute("SET CHARACTER_SET_RESULTS='latin1'")
    cursor.execute('''
        SELECT
            biomarkers.id,
            biomarkers.name,
            biomarker_datasets.dataset_id
        FROM
            biomarkers,
            biomarker_datasets
        WHERE
            biomarkers.id = biomarker_datasets.biomarker_id
    ''')
    with open('results.csv', 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['biomarker id', 'biomarker name', 'dataset ID'])
        for row in cursor.fetchall():
            writer.writerow([str(i) for i in row])


def query(connection):
    cursor = connection.cursor()
    cursor.execute("SET CHARACTER_SET_RESULTS='latin1'")
    cursor.execute('''
        SELECT
            biomarkers.id,
            biomarkers.name,
            organ_data.phase,
            organs.name,
            studies.FHCRC_ID,
            studies.title
        FROM
            biomarker_study_data,
            biomarkers,
            organ_data,
            organs,
            studies
        WHERE
            biomarkers.id = organ_data.biomarker_id AND
            biomarkers.id = biomarker_study_data.biomarker_id AND
            studies.id = biomarker_study_data.study_id AND
            organs.id = organ_data.organ_id
        ORDER BY
            biomarkers.id,
            organs.name,
            studies.title
    ''')
    with open('results.csv', 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow([
            'biomarkers.id',
            'biomarkers.name',
            'biomarker_names.name',
            'biomarkers.phase',
            'organ_data.phase',
            'organs.name',
            'studies.FHCRC_ID',
            'studies.title'
        ])
        for row in cursor.fetchall():
            writer.writerow([str(i) for i in row])


class Study(object):
    def __init__(self, number, name):
        self.number, self.name = number, name
    def __repr__(self):
        return '{}(number={},name={})'.format(self.__class__.__name__, self.number, self.name)


class Organ(object):
    def __init__(self, name, phase, studies):
        self.name, self.phase, self.studies = name, phase, studies
    def __repr__(self):
        return '{}(name={},phase={},studies={})'.format(self.__class__.__name__, self.name, self.phase, self.studies)


class Biomarker(object):
    def __init__(self, number, name, organs):
        self.number, self.name, self.organs = number, name, organs
    def __repr__(self):
        return '{}(number={},name={},organs={})'.format(self.__class__.__name__, self.number, self.name, self.organs)


class ExpandedBiomarker(Biomarker):
    def __init__(self, number, name, hgncName, organs, members):
        self.number, self.name, self.hgncName, self.organs, self.members = number, name, hgncName, organs, members


def maureen(connection):
    cursor = connection.cursor()
    cursor.execute("SET CHARACTER_SET_RESULTS='latin1'")
    biomarkers = {}
    cursor.execute('SELECT biomarkers.id, biomarkers.name FROM biomarkers')
    for biomarkerRow in cursor.fetchall():
        number, name = biomarkerRow[0], biomarkerRow[1]
        subcursor = connection.cursor()
        subcursor.execute("SET CHARACTER_SET_RESULTS='latin1'")
        subcursor.execute('SELECT name from biomarker_names WHERE biomarker_id = %s and isHgnc = 1', (number,))
        if subcursor.rowcount:
            name = subcursor.fetchone()[0]
        subcursor.execute('''
            SELECT
                organ_data.id, organs.name, organ_data.phase
            FROM
                organs, organ_data
            WHERE
                organs.id = organ_data.organ_id AND
                organ_data.biomarker_id = %s
        ''', (number,))
        organs = []
        for organRow in subcursor.fetchall():
            organNumber, organName, organPhase = organRow[0], organRow[1], organRow[2]
            studies = []
            subsubcursor = connection.cursor()
            subsubcursor.execute("SET CHARACTER_SET_RESULTS='latin1'")
            subsubcursor.execute('''
                SELECT
                    studies.FHCRC_ID, studies.title
                FROM
                    studies, study_data
                WHERE
                    study_data.organ_data_id = %s AND
                    studies.id = study_data.study_id
            ''', (organNumber,))
            for studyRow in subsubcursor.fetchall():
                studyNumber, studyName = studyRow[0], studyRow[1]
                study = Study(studyNumber, studyName)
                studies.append(study)
            organ = Organ(organName, organPhase, studies)
            organs.append(organ)
        biomarker = Biomarker(number, name, organs)
        biomarkers[number] = biomarker
    with open('results.csv', 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        biomarkerNumbers = sorted(biomarkers.keys())
        writer.writerow([
            'Biomarker ID Number',
            'HGNC name (if available)',
            'Organ',
            'Organ Phase',
            'Protocol ID',
            'Protocol Name'
        ])
        for number in biomarkerNumbers:
            biomarker = biomarkers[number]
            for organ in biomarker.organs:
                studies = organ.studies
                if len(studies) == 0:
                    writer.writerow([str(number), biomarker.name, organ.name, organ.phase, '«N/A»', '«No studies found»'])
                else:
                    for study in studies:
                        writer.writerow([str(number), biomarker.name, organ.name, organ.phase, str(study.number), study.name])


def inventory(connection):
    cursor = connection.cursor()
    cursor.execute("SET CHARACTER_SET_RESULTS='latin1'")
    biomarkers = {}
    cursor.execute('SELECT biomarkers.id, biomarkers.name, biomarkers.isPanel FROM biomarkers')
    for biomarkerRow in cursor.fetchall():
        number, name, isPanel = biomarkerRow[0], biomarkerRow[1], biomarkerRow[2]
        subcursor = connection.cursor()
        subcursor.execute("SET CHARACTER_SET_RESULTS='latin1'")
        subcursor.execute('SELECT name from biomarker_names WHERE biomarker_id = %s and isHgnc = 1', (number,))
        hgncName = subcursor.fetchone()[0] if subcursor.rowcount else '«unknown»'

        subcursor.execute('''
            SELECT
                organ_data.id, organs.name, organ_data.phase
            FROM
                organs, organ_data
            WHERE
                organs.id = organ_data.organ_id AND
                organ_data.biomarker_id = %s
        ''', (number,))
        organs = []
        for organRow in subcursor.fetchall():
            organNumber, organName, organPhase = organRow[0], organRow[1], organRow[2]
            studies = []
            subsubcursor = connection.cursor()
            subsubcursor.execute("SET CHARACTER_SET_RESULTS='latin1'")
            subsubcursor.execute('''
                SELECT
                    studies.FHCRC_ID, studies.title
                FROM
                    studies, study_data
                WHERE
                    study_data.organ_data_id = %s AND
                    studies.id = study_data.study_id
            ''', (organNumber,))
            for studyRow in subsubcursor.fetchall():
                studyNumber, studyName = studyRow[0], studyRow[1]
                study = Study(studyNumber, studyName)
                studies.append(study)
            organ = Organ(organName, organPhase, studies)
            organs.append(organ)

        if isPanel:
            subcursor.execute('''
                SELECT biomarkers.id, biomarkers.name FROM biomarkers, paneldata
                WHERE biomarkers.id = paneldata.biomarker_id AND paneldata.panel_id = %s
            ''', (number,))
            members = ', '.join([f'{member[0]} ({member[1]})' for member in subcursor.fetchall()])
        else:
            members = ''

        biomarker = ExpandedBiomarker(f'{number:05}', name, hgncName, organs, members)
        biomarkers[f'{number:05}'] = biomarker

    with open('inventory.csv', 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        biomarkerNumbers = sorted(biomarkers.keys())
        writer.writerow([
            'Biomarker Num',
            'DB Name',
            'HGNC name',
            'Organ',
            'Organ Phase',
            'Protocol ID',
            'Protocol Name',
            'Panel Members'
        ])
        for number in biomarkerNumbers:
            biomarker = biomarkers[number]
            for organ in biomarker.organs:
                studies = organ.studies
                if len(studies) == 0:
                    writer.writerow([
                        biomarker.number, biomarker.name, biomarker.hgncName,
                        organ.name, organ.phase, '«N/A»', '«No studies found»', biomarker.members
                    ])
                else:
                    for study in studies:
                        writer.writerow([
                            biomarker.number, biomarker.name, biomarker.hgncName,
                            organ.name, organ.phase, str(study.number), study.name, biomarker.members
                        ])


def main():
    args = _argParser.parse_args()
    user = args.user
    password = args.password if args.password else getpass.getpass(u'Password for MySQL user "{}": '.format(user))
    connection = pymysql.connect(host=args.host, user=user, password=password, database=args.database)
    # query(connection)
    # maureen(connection)
    # datasets(connection)
    inventory(connection)
    sys.exit(0)


if __name__ == '__main__':
    main()
