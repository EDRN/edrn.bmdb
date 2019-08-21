# encoding: utf-8
#
# Standalone RDF extractor for the Biomarker Database

import MySQLdb, argparse, getpass, sys, rdflib, logging


# Get logging going
logging.basicConfig(level=logging.INFO, format='%(levelname)-8s %(message)s')

# RDF Namespaces
_bmdb = rdflib.Namespace(u'http://edrn.nci.nih.gov/rdf/rdfs/bmdb-1.0.0#')
_edrnTypes = rdflib.Namespace(u'http://edrn.nci.nih.gov/rdf/types.rdf#')
_edrnSchema = rdflib.Namespace(u'http://edrn.nci.nih.gov/rdf/schema.rdf#')

# Convenient predicates
_type = rdflib.namespace.RDF.type

# URI bases
_edrnSubjectBase = u'http://edrn.nci.nih.gov/data/'
_biomarkerBase = u'http://edrn.jpl.nasa.gov/bmdb/'
_genBase = u'http://www.w3.org/1999/02/22-rdf-syntax-ns#'


# Functions
# =========


def _publications(connection, graph, public):
    rdfType = rdflib.URIRef(_edrnTypes.Publication)
    cursor = connection.cursor()
    cursor.execute(u'SELECT id, pubmed_id FROM publications')
    for subject, pmid in cursor.fetchall():
        subject, pmid = rdflib.URIRef(_edrnSubjectBase + u'pubs/' + unicode(subject)), rdflib.Literal(unicode(pmid))
        graph.add((subject, _type, rdfType))
        graph.add((subject, _edrnSchema.pmid, pmid))


def _biomarkers(connection, graph, public):
    bioType, bsdType = rdflib.URIRef(_bmdb.Biomarker), rdflib.URIRef(_bmdb.BiomarkerStudyData)
    query = u'SELECT id, name, shortName, description, qastate, phase, security, type, isPanel, panelID, curatorNotes FROM biomarkers'
    if public:
        query += " WHERE qastate != 'Under Review'"
    biocursor = connection.cursor()
    biocursor.execute(query)
    # TODO: get created & modified datetimes?
    for dbid, name, shortName, desc, qaState, phase, security, btype, isPanel, panelID, curatorNotes in biocursor.fetchall():
        isPublicBiomaker = qaState == u'Accepted'

        subject  = rdflib.URIRef(u'{}biomarkers/view/{}'.format(_biomarkerBase, dbid))
        urn      = rdflib.Literal(u'urn:edrn:bmdb:biomarker:{}'.format(dbid))
        desc     = rdflib.Literal(desc.strip())
        qaState  = rdflib.Literal(qaState)
        phase    = rdflib.Literal(phase)
        security = rdflib.Literal(security)
        btype    = rdflib.Literal(btype)
        isPanel  = bool(isPanel)

        # OK, let's go
        graph.add((subject, _type, bioType))

        # there are better ways of doing this, but this duplicate's bmdb's logic:
        bmName, hgncName = rdflib.Literal(u'Unknown'), None
        cursor = connection.cursor()
        cursor.execute(u'SELECT id, name, isPrimary, isHgnc FROM biomarker_names WHERE biomarker_id = %s', (dbid,))
        for nameid, name, isPrimary, isHgnc in cursor.fetchall():
            name = rdflib.Literal(name.strip())
            if isPrimary: bmName = name
            if isHgnc: hgncName = name
            graph.add((subject, _bmdb.Alias, name))
        if hgncName is None: hgncName = rdflib.Literal(u'')  # Better to just leave out the predicate; but bmdb is crap

        graph.add((subject, _bmdb.Title, rdflib.Literal(bmName)))
        graph.add((subject, _bmdb.HgncName, rdflib.Literal(hgncName)))
        graph.add((subject, _bmdb.URN, urn))
        graph.add((subject, _bmdb.Description, desc))
        graph.add((subject, _bmdb.QAState, qaState))
        graph.add((subject, _bmdb.Phase, phase))
        graph.add((subject, _bmdb.Security, security))
        graph.add((subject, _bmdb.Type, btype))

        # If it's a panel, show its composition
        if isPanel:
            graph.add((subject, _bmdb.IsPanel, rdflib.Literal(u'1')))
            cursor.execute(u'SELECT biomarker_id FROM paneldata WHERE panel_id = %s', (dbid,))
            for i in cursor.fetchall():
                memberURI = rdflib.URIRef(u'{}biomarkers/view/{}'.format(_biomarkerBase, i[0]))
                graph.add((subject, _bmdb.hasBiomarker, memberURI))
        else:
            graph.add((subject, _bmdb.IsPanel, rdflib.Literal(u'0')))

        # If it's composed, show panels it belongs to
        cursor.execute(u'SELECT panel_id FROM paneldata WHERE biomarker_id = %s', (dbid,))
        for i in cursor.fetchall():
            panelURI = rdflib.URIRef(u'{}biomarkers/view/{}'.format(_biomarkerBase, i[0]))
            graph.add((subject, _bmdb.memberOfPanel, panelURI))

        # ACL
        cursor.execute(u"SELECT ldapGroup FROM acl WHERE objectType = 'biomarker' AND objectId = %s", (dbid,))
        for i in cursor.fetchall():
            graph.add((subject, _bmdb.AccessGrantedTo, rdflib.Literal(i[0])))

        # Datasets
        cursor.execute(u'SELECT dataset_id FROM biomarker_datasets WHERE biomarker_id = %s', (dbid,))
        for i in cursor.fetchall():
            datasetURI = rdflib.URIRef(u'https://edrn.jpl.nasa.gov/ecas/data/dataset/urn:edrn:{}'.format(i[0]))
            graph.add((subject, _bmdb.AssociatedDataset, datasetURI))

        # Publications
        cursor.execute(u'SELECT publication_id FROM biomarkers_publications WHERE biomarker_id = %s', (dbid,))
        for i in cursor.fetchall():
            pubURI = rdflib.URIRef(u'{}publications/view/{}'.format(_biomarkerBase, i[0]))
            graph.add((subject, _bmdb.referencedInPublication, pubURI))

        # Resources
        cursor.execute(u'SELECT URL FROM biomarker_resources WHERE biomarker_id = %s', (dbid,))
        for i in cursor.fetchall():
            graph.add((subject, _bmdb.referencesResource, rdflib.URIRef(i[0].strip())))

        # Include organ & study details only on Accepted biomarkers; if we're doing the private stuff
        # too, then include organ details as well.
        if isPublicBiomaker or not public:
            # Organs; note the portal doesn't even use this; does anyone?
            cursor.execute(u'SELECT id FROM organ_datas WHERE biomarker_id = %s', (dbid,))
            for i in cursor.fetchall():
                organURI = rdflib.URIRef(u'{}biomarkers/view/{}'.format(_biomarkerBase, i[0]))
                graph.add((subject, _bmdb.indicatorForOrgan, organURI))

            # Studies
            cursor.execute(
                u'SELECT biomarker_study_datas.id, studies.FHCRC_ID FROM biomarker_study_datas JOIN studies'
                u' ON biomarker_study_datas.study_id = studies.id'
                u' WHERE biomarker_study_datas.biomarker_id = %s',
                (dbid,)
            )
            if cursor.rowcount > 0:
                bag = rdflib.BNode()
                graph.add((bag, _type, rdflib.RDF.Bag))
                graph.add((subject, _bmdb.hasBiomarkerStudyDatas, bag))
                for li, (bsdID, fhcrcID) in zip(range(1, cursor.rowcount + 1), cursor.fetchall()):
                    bsdURI = rdflib.URIRef(u'{}biomarkers/studies/{}/{}'.format(_biomarkerBase, dbid, bsdID))
                    graph.add((bag, rdflib.URIRef(u'{}_{}'.format(_genBase, li)), bsdURI))
                    studyURI = rdflib.URIRef(u'{}protocols/{}'.format(_edrnSubjectBase, fhcrcID))
                    graph.add((bsdURI, _bmdb.referencesStudy, studyURI))
                    graph.add((bsdURI, _type, bsdType))


def _organs(connection, graph, public):
    bmoType, bmoStudyDataType = rdflib.URIRef(_bmdb.BiomarkerOrganData), rdflib.URIRef(_bmdb.BiomarkerOrganStudyData)
    bmoCursor = connection.cursor()
    bmoCursor.execute(
        u'SELECT biomarker_id, organ_datas.id, description, performance_comment, organs.name, phase, qastate,'
        u' clinical_translation'
        u' from organ_datas, organs WHERE organ_datas.organ_id = organs.id'
    )
    for bmID, bmoID, desc, perfCom, organName, phase, qastate, clinTran in bmoCursor.fetchall():
        bmoSubject = rdflib.URIRef(u'{}biomarkers/organs/{}/{}'.format(_biomarkerBase, bmID, bmoID))
        graph.add((bmoSubject, _type, bmoType))
        # Silly URN field, should be an RDF resource, not a literal
        graph.add((bmoSubject, _bmdb.URN, rdflib.Literal(u'urn:edrn:bmdb:biomarkerorgan:{}'.format(bmoID))))
        # Reference to our biomarker
        biomarkerSubject = rdflib.URIRef(u'{}biomarkers/view/{}'.format(_biomarkerBase, bmID))
        graph.add((bmoSubject, _bmdb.Biomarker, biomarkerSubject))

        # Basic predicates
        graph.add((bmoSubject, _bmdb.Description, rdflib.Literal(desc.strip())))
        graph.add((bmoSubject, _bmdb.PerformanceComment, rdflib.Literal(perfCom.strip())))
        graph.add((bmoSubject, _bmdb.Organ, rdflib.Literal(organName.strip())))
        graph.add((bmoSubject, _bmdb.Phase, rdflib.Literal(phase.strip())))
        graph.add((bmoSubject, _bmdb.QAState, rdflib.Literal(qastate.strip())))

        # Slight computation for clinical_translation
        clinTran = clinTran.strip()
        if clinTran in (u'CLIA', u'Both'):
            clia = rdflib.URIRef(u'http://www.cms.gov/Regulations-and-Guidance/Legislation/CLIA/index.html')
            graph.add((bmoSubject, _bmdb.certification, clia))
        if clinTran in (u'FDA', u'Both'):
            fda = rdflib.URIRef(u'http://www.fda.gov/regulatoryinformation/guidances/ucm125335.htm')
            graph.add((bmoSubject, _bmdb.certification, fda))

        # LDAP groups
        cursor = connection.cursor()
        cursor.execute(u"SELECT ldapGroup FROM acl WHERE objectType = 'biomarkerorgan' AND objectId = %s", (bmoID,))
        for i in cursor.fetchall():
            graph.add((bmoSubject, _bmdb.AccessGrantedTo, rdflib.Literal(i[0])))

        # Study data; and save them up for later use
        cursor.execute(
            u'SELECT study_datas.id, studies.FHCRC_ID, study_datas.decision_rule FROM study_datas, studies'
            u' WHERE studies.id = study_datas.study_id AND study_datas.organ_data_id = %s', (bmoID,)
        )
        if cursor.rowcount > 0:
            bag = rdflib.BNode()
            graph.add((bag, _type, rdflib.RDF.Bag))
            graph.add((bmoSubject, _bmdb.hasBiomarkerOrganStudyDatas, bag))
            for li, (studyID, fhcrcID, decision) in zip(range(1, cursor.rowcount + 1), cursor.fetchall()):
                bosdURI = rdflib.URIRef(u'{}#{}'.format(bmoSubject, studyID))
                graph.add((bag, rdflib.URIRef(u'{}_{}'.format(_genBase, li)), bosdURI))
                # Now about that study, specifically
                graph.add((bosdURI, _type, bmoStudyDataType))
                graph.add((bosdURI, _bmdb.DecisionRule, rdflib.Literal(decision.strip())))
                # Sensitivity/specificity computation
                sensSpecBag = rdflib.BNode()
                graph.add((sensSpecBag, _type, rdflib.RDF.Bag))
                graph.add((bosdURI, _bmdb.SensitivityDatas, sensSpecBag))

                c = connection.cursor()

                # TODO: later
                # c.execute(
                #     u'SELECT sensitivity, specificity, prevalence, specificAssayType, notes'
                #     u' FROM sensitivities WHERE study_id = %s', (studyID,)
                # )
                # for sli, (sens, spec, prev, assay, notes) in zip(range(1, c.rowcont + 1)) in cursor.fetchall():
                #     pass

                # Publications for this relationship
                c.execute(
                    u'SELECT publication_id FROM biomarker_study_datas_publications'
                    u' WHERE biomarker_study_data_id = %s', (studyID,)
                )
                for i in c.fetchall():
                    pubURI = rdflib.URIRef(u'{}publications/view/{}'.format(_biomarkerBase, i[0]))
                    graph.add((bosdURI, _bmdb.referencedInPublication, pubURI))
                c .execute(
                    u'SELECT URL FROM biomarker_study_data_resources WHERE biomarker_study_data_id = %s', ((studyID,))
                )
                for i in c.fetchall():
                    graph.add((bosdURI, _bmdb.referencesResource, rdflib.URIRef(i[0].strip())))

        # Publications
        cursor.execute(u'SELECT publication_id FROM organ_datas_publications WHERE organ_data_id = %s', (bmoID,))
        for i in cursor.fetchall():
            pubURI = rdflib.URIRef(u'{}publications/view/{}'.format(_biomarkerBase, i[0]))
            graph.add((bmoSubject, _bmdb.referencedInPublication, pubURI))

        # Resources
        cursor.execute(u'SELECT URL FROM organ_data_resources WHERE organ_data_id = %s', (bmoID,))
        for i in cursor.fetchall():
            graph.add((bmoSubject, _bmdb.referencesResource, rdflib.URIRef(i[0].strip())))


def _resources(connection, graph, public):
    rdfType = rdflib.URIRef(_bmdb.ExternalResource)
    cursor = connection.cursor()
    for tableName in (
        u'biomarker_resources', u'biomarker_study_data_resources', u'organ_data_resources', u'study_data_resources',
        u'study_resources'
    ):
        cursor.execute(u'SELECT URL, description FROM {}'.format(tableName))
        for subject, obj in cursor.fetchall():
            subject = rdflib.URIRef(subject.strip())
            graph.add((rdflib.URIRef(subject), _type, rdfType))
            graph.add((rdflib.URIRef(subject), _bmdb.Description, rdflib.Literal(obj.strip())))


_rdfFlavors = {
    'pub': _publications,
    'bio': _biomarkers,
    'org': _organs,
    'res': _resources,
}
_validFlavors = u', '.join(_rdfFlavors.keys())


def validFlavor(s):
    if s not in _rdfFlavors:
        raise argparse.ArgumentTypeError(u'"{}" not one of {}'.format(s, _validFlavors))
    return s


_argParser = argparse.ArgumentParser(description=u'Generate RDF from the biomarker database')
_argParser.add_argument('-H', '--host', default=u'localhost', help=u'MySQL host; default %(default)s')
_argParser.add_argument('-D', '--database', default=u'cbmdb', help=u'MySQL database, default %(default)s')
_argParser.add_argument('-u', '--user', default=u'cbmdb', help=u'MySQL user; default %(default)s')
_argParser.add_argument('-p', '--password', help=u'MySQL password; will be prompted if not given')
_argParser.add_argument('-f', '--format', default='pretty-xml', help=u'RDF format; default %(default)s')
_argParser.add_argument('-a', '--all', default=False, help=u'All objects; default: only public', action='store_true')
_argParser.add_argument(
    '-d', '--document', default=u'res', type=validFlavor,
    help=u'RDF document to produce: {}; default %(default)s'.format(_validFlavors)
)


def main():
    args = _argParser.parse_args()
    user = args.user
    password = args.password if args.password else getpass.getpass(u'Password for MySQL user "{}": '.format(user))
    connection = MySQLdb.connect(host=args.host, user=user, passwd=password, db=args.database)
    graph, generator = rdflib.Graph(), _rdfFlavors[args.document]
    generator(connection, graph, not args.all)
    print(graph.serialize(format=args.format))
    sys.exit(0)


if __name__ == '__main__':
    main()
