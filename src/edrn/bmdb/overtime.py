# encoding: utf-8

import pymysql, argparse, getpass, sys, csv


def writeCSV(connection):
    cursor = connection.cursor()
    cursor.execute("SET CHARACTER_SET_RESULTS='latin1'")
    cursor.execute('SELECT created FROM biomarkers ORDER BY created')
    buckets = {}
    for row in cursor.fetchall():
        created = row[0].date()
        count = buckets.get(created, 0)
        count += 1
        buckets[created] = count
    dates = sorted(list(buckets.keys()))
    with open('overtime.csv', 'w', newline='') as csvio:
        writer = csv.writer(csvio)
        writer.writerow(['Date', 'Number of Biomarkers Created'])
        for date in dates:
            writer.writerow([date, buckets[date]])


def main():
    parser = argparse.ArgumentParser(description="Generate ")
    parser.add_argument('-H', '--host', default='localhost', help='MySQL host; default %(default)s')
    parser.add_argument('-D', '--database', default='cbmdb', help='MySQL database, default %(default)s')
    parser.add_argument('-u', '--user', default='cbmdb', help='MySQL user; default %(default)s')
    parser.add_argument('-p', '--password', help='MySQL password; will be prompted if not given')
    args = parser.parse_args()
    user = args.user
    password = args.password if args.password else getpass.getpass(u'Password for MySQL user "{}": '.format(user))
    connection = pymysql.connect(host=args.host, user=user, password=password, database=args.database)
    writeCSV(connection)
    sys.exit(0)


if __name__ == '__main__':
    main()


# {
#    "Bladder" : {
#       "" : 2,
#       "Gene" : 3,
#       "Genetic" : 12,
#       "Genomic" : 2,
#       "Protein" : 9
#    },
#    "Breast" : {
#       "" : 2,
#       "Gene" : 6,
#       "Genetic" : 1,
#       "Genomic" : 6,
#       "Metabolomic" : 9,
#       "Protein" : 219,
#       "Proteomic" : 91
#    },
#    "Colon" : {
#       "Epigenetic" : 1,
#       "Genetic" : 4,
#       "Protein" : 14,
#       "Proteomic" : 10
#    },
#    "Esophagus" : {
#       "Epigenetic" : 1,
#       "Genomic" : 9
#    },
#    "Head and Neck" : {
#       "Gene" : 6,
#       "Protein" : 2
#    },
#    "Liver" : {
#       "" : 2,
#       "Genetic" : 1,
#       "Protein" : 13,
#       "Proteomic" : 1
#    },
#    "Lung" : {
#       "" : 59,
#       "Gene" : 41,
#       "Genomic" : 24,
#       "Glycomic" : 4,
#       "Protein" : 128,
#       "Proteomic" : 30
#    },
#    "Ovary" : {
#       "Gene" : 1,
#       "Genetic" : 1,
#       "Genomic" : 6,
#       "Protein" : 204,
#       "Proteomic" : 21
#    },
#    "Pancreas" : {
#       "" : 3,
#       "Gene" : 7,
#       "Genetic" : 1,
#       "Glycomic" : 3,
#       "Metabolomic" : 1,
#       "Protein" : 24,
#       "Proteomic" : 35
#    },
#    "Prostate" : {
#       "" : 12,
#       "Epigenetic" : 8,
#       "Gene" : 351,
#       "Genomic" : 12,
#       "Metabolomic" : 1,
#       "Protein" : 42,
#       "Proteomic" : 6
#    }
# }
