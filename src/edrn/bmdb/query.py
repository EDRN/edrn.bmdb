# encoding: utf-8
#
# Do generic query of some sort

import MySQLdb, argparse, getpass, sys, logging, csv, cStringIO, codecs



_argParser = argparse.ArgumentParser(description=u'Fix genenames.org links in the biomarker database')
_argParser.add_argument('-H', '--host', default=u'localhost', help=u'MySQL host; default %(default)s')
_argParser.add_argument('-D', '--database', default=u'cbmdb', help=u'MySQL database, default %(default)s')
_argParser.add_argument('-u', '--user', default=u'cbmdb', help=u'MySQL user; default %(default)s')
_argParser.add_argument('-p', '--password', help=u'MySQL password; will be prompted if not given')


class UnicodeWriter:
    """
    A CSV writer which will write rows to CSV file "f",
    which is encoded in the given encoding.
    """

    def __init__(self, f, dialect=csv.excel, encoding="utf-8", **kwds):
        # Redirect output to a queue
        self.queue = cStringIO.StringIO()
        self.writer = csv.writer(self.queue, dialect=dialect, **kwds)
        self.stream = f
        self.encoder = codecs.getincrementalencoder(encoding)()

    def writerow(self, row):
        self.writer.writerow([s.encode("utf-8") for s in row])
        # Fetch UTF-8 output from the queue ...
        data = self.queue.getvalue()
        data = data.decode("utf-8")
        # ... and reencode it into the target encoding
        data = self.encoder.encode(data)
        # write to the target stream
        self.stream.write(data)
        # empty queue
        self.queue.truncate(0)

    def writerows(self, rows):
        for row in rows:
            self.writerow(row)


def query(connection):
    cursor = connection.cursor()
    cursor.execute('''SELECT biomarkers.id, biomarkers.name, biomarkers.phase, organ_data.phase, studies.FHCRC_ID,
        studies.title FROM biomarkers, organ_data, biomarker_study_data, studies 
        WHERE biomarkers.id = organ_data.biomarker_id AND biomarkers.id = biomarker_study_data.biomarker_id
        AND studies.id = biomarker_study_data.study_id
    ''')
    with open('results.csv', 'wb') as f:
        writer = UnicodeWriter(f)
        for row in cursor.fetchall():
            writer.writerow([unicode(i) for i in row])


def main():
    args = _argParser.parse_args()
    user = args.user
    password = args.password if args.password else getpass.getpass(u'Password for MySQL user "{}": '.format(user))
    connection = MySQLdb.connect(host=args.host, user=user, passwd=password, db=args.database)
    query(connection)
    sys.exit(0)


if __name__ == '__main__':
    main()
