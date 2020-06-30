#!/bin/sh

# Check exec
# ----------

if [ \! -x $PWD/bin/generate-bmdb-rdf ]; then
    echo "The file bin/generate-bmdb-rdf is missing or isn't executable" 1>&2
    exit 1
fi


# Get password
# ------------

edrn_mysql_cbmdb_password="unknown"
[ -f $HOME/.secrets/passwords.sh ] && . $HOME/.secrets/passwords.sh


# Here we go
# ----------

$PWD/bin/generate-bmdb-rdf --password "$edrn_mysql_cbmdb_password" --all --document bio > biomarkers.rdf
$PWD/bin/generate-bmdb-rdf --password "$edrn_mysql_cbmdb_password" --all --document res > bmdb-resources.rdf
$PWD/bin/generate-bmdb-rdf --password "$edrn_mysql_cbmdb_password" --all --document pub > bmdb-pubs.rdf
$PWD/bin/generate-bmdb-rdf --password "$edrn_mysql_cbmdb_password" --all --document org > bio-organ.rdf

echo "Generated fresh rdf" 1>&2

exit 0
