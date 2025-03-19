# encoding: utf-8
#
# Turn the BMDB RDF into more-or-less plain English

import argparse, logging
from rdflib import Graph, URIRef
import rdflib

_logger = logging.getLogger(__name__)

# Map RDF predicate URI to an English predicate and boolean literal (or reference) and boolean plural (or not)
_predicates = {
    URIRef('http://edrn.nci.nih.gov/rdf/rdfs/bmdb-1.0.0#Title'): ('It is titled', True, False),
    URIRef('http://edrn.nci.nih.gov/rdf/rdfs/bmdb-1.0.0#HgncName'): ('It has a canonical HGNC name of', True, False),
    URIRef('http://edrn.nci.nih.gov/rdf/rdfs/bmdb-1.0.0#Alias'): ('It is also known as', True, True),
    URIRef('http://edrn.nci.nih.gov/rdf/rdfs/bmdb-1.0.0#Description'): ('Here is its description:', True, False),
    URIRef('http://edrn.nci.nih.gov/rdf/rdfs/bmdb-1.0.0#QAState'): ('The quality assurance state of it is:', True, False),
    URIRef('http://edrn.nci.nih.gov/rdf/rdfs/bmdb-1.0.0#Phase'): ('According to the five-phase model of biomarker research, it is in phase', True, False),
    URIRef('http://edrn.nci.nih.gov/rdf/rdfs/bmdb-1.0.0#Type'): ('It is of type', True, False),
    URIRef('http://edrn.nci.nih.gov/rdf/rdfs/bmdb-1.0.0#referencedInPublication'): ('It is referenced in publications at these locations', False, True),
    URIRef('http://edrn.nci.nih.gov/rdf/rdfs/bmdb-1.0.0#AccessGrantedTo'): ('The following groups have access to it:', True, True),
    URIRef('http://edrn.nci.nih.gov/rdf/rdfs/bmdb-1.0.0#referencesResource'): ('It refers to external resources at these URLs:', False, True),
}

_biomarker_type = URIRef('http://edrn.nci.nih.gov/rdf/rdfs/bmdb-1.0.0#Biomarker')
_preamble = '''Let's talk about the biomarker defined at {url}.'''


def load_rdf_knowledge():
    '''Load the BMDB RDF and return a graph.'''
    g = Graph()
    
    # RDF data sources for BMDB
    urls = [
        # 'https://bmdb.jpl.nasa.gov/rdf/biomarkers',
        # 'https://bmdb.jpl.nasa.gov/rdf/biomarker-organs'
        # ‼️ for local testing and speed
        'file:/tmp/bio.rdf',  # 'file:/tmp/bio-org.rdf'
    ]
    
    # Load RDF data from each source
    for url in urls:
        _logger.info('Loading RDF data from %s', url)
        g.parse(url, format='xml')
    
    _logger.info(f'Loaded {len(g)} triples into the RDF graph.')
    return g


def structure(graph) -> dict:
    '''Convert an RDF graph into a structure as follows:

    A dict of key "subject URI" and value "dict", which has key "predicate URI" and value "list",
    which may be a sequence of literal values or URI references.
    '''
    statements = {}
    for s, p, o in graph:
        predicates = statements.get(s, {})
        objects = predicates.get(p, [])
        objects.append(o)
        predicates[p] = objects
        statements[s] = predicates
    return statements


def express(structured):
    '''Express the `structured` dict in English to stdout.'''
    for s, p in structured.items():
        kind = p.get(rdflib.RDF.type, [None])[0]
        # Skip anything that's not a biomarker
        if kind != _biomarker_type: continue
        print(_preamble.format(url=s))
        for p_uri, expression in _predicates.items():
            english, literal, multi = expression
            values = p.get(p_uri, None)
            if not values or str(values[0]) == '': continue
            if literal:
                if multi:
                    print(english, ', '.join(values) + '.')
                else:
                    print(english, values[0] + '.')
            else:
                # Do we need to do something special here?
                if multi:
                    print(english, ', '.join(values) + '.')
                else:
                    print(english, values[0] + '.')
        print()


def main():
    '''Do it.'''
    parser = argparse.ArgumentParser(description='Convert BMDB RDF into English')
    logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
    _ = parser.parse_args()

    express(structure(load_rdf_knowledge()))


if __name__ == '__main__':
    main()
