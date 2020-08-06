# encoding: utf-8
#
# Fix genenames.org links in the Biomarker Database.
#
# Old format: http://www.genenames.org/data/hgnc_data.php?hgnc_id=N
# New format: https://www.genenames.org/data/gene-symbol-report/#!/hgnc_id/HGNC:N
# where N is a numeric ID.

import pymysql, argparse, getpass, sys, logging, re


# Get logging going
logging.basicConfig(level=logging.INFO, format='%(levelname)-8s %(message)s')


# Get a handy regexp
_urlMatcher = re.compile(r'http://www\.genenames\.org/data/hgnc_data\.php\?hgnc_id=(\d+)')


# New URL looks like this
_newURL = 'https://www.genenames.org/data/gene-symbol-report/#!/hgnc_id/HGNC:'


# Functions
# =========

_argParser = argparse.ArgumentParser(description='Fix genenames.org links in the biomarker database')
_argParser.add_argument('-H', '--host', default='localhost', help='MySQL host; default %(default)s')
_argParser.add_argument('-D', '--database', default='cbmdb', help='MySQL database, default %(default)s')
_argParser.add_argument('-u', '--user', default='cbmdb', help='MySQL user; default %(default)s')
_argParser.add_argument('-p', '--password', help='MySQL password; will be prompted if not given')


def fix(connection):
    '''Fix genenames.org links. There is probably a fancy single line of SQL that can
    do this but I am terrible at SQL.'''
    cursor = connection.cursor()
    cursor.execute("SET CHARACTER_SET_RESULTS='latin1'")
    for tableName in (
        'biomarker_resources',
        'biomarker_study_data_resources',
        'organ_data_resources',
        'study_data_resources',
        'study_resources',
    ):
        logging.info('Querying %s for URLs', tableName)
        cursor.execute('SELECT `id`, `URL` FROM {}'.format(tableName))
        for entryID, url in cursor.fetchall():
            match = _urlMatcher.match(url)
            if match:
                geneID = match.group(1)
                logging.info('Found an old URL for resource %d, gene %s', entryID, geneID)
                sql = u"UPDATE {} SET `URL` = '{}{}' WHERE `id` = %s".format(tableName, _newURL, geneID)
                logging.debug('SQL to execute: %s (with %%s as entry ID)', sql)
                updater = connection.cursor()
                updater.execute("SET CHARACTER_SET_RESULTS='latin1'")
                updater.execute(sql, (entryID,))


def main():
    args = _argParser.parse_args()
    user = args.user
    password = args.password if args.password else getpass.getpass('Password for MySQL user "{}": '.format(user))
    connection = pymysql.connect(host=args.host, user=user, passwd=password, db=args.database)
    fix(connection)
    sys.exit(0)


if __name__ == '__main__':
    main()
