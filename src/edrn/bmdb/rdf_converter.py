# encoding: utf-8

import argparse, csv, sys, logging
from rdflib import Graph, URIRef
from collections import defaultdict
from urllib.parse import urlparse

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')


def load_rdf_data():
    # Create a new RDF graph
    g = Graph()
    
    # Define the RDF data sources
    urls = [
        'https://bmdb.jpl.nasa.gov/rdf/biomarkers',
        # 'https://bmdb.jpl.nasa.gov/rdf/biomarker-organs'
        # ‼️ for local testing and speed
        # 'file:/tmp/bio.rdf',  # 'file:/tmp/bio-org.rdf'
    ]
    
    # Load RDF data from each source
    for url in urls:
        logging.info('Loading RDF data from %s', url)
        g.parse(url, format='xml')  # Assuming RDF/XML format
    
    logging.info(f'Loaded {len(g)} triples into the RDF graph.')
    return g


def get_predicate_map(graph):
    predicate_map = {}
    for _, p, _ in graph:
        if isinstance(p, URIRef):
            short_name = graph.namespace_manager.qname(p).split(':', 1)[-1]  # Extract local part
            predicate_map[short_name] = p
    return predicate_map


def short_predicate(uri):
    return urlparse(uri).fragment


def write_output(statements, predicate_map):
    writer = csv.writer(sys.stdout)
    header = [key for key in predicate_map.keys() if not key.startswith('_')]
    writer.writerow(['ID'] + header)

    biomarkers = defaultdict(list)
    for s, p, o in statements:
        if '/view/' in str(s):
            biomarkers[s].append((p, o))

    for biomarker, predicates in biomarkers.items():
        values = defaultdict(list)
        for predicate in predicates:
            short, value = short_predicate(predicate[0]), predicate[1]
            position = header.index(short)
            values[position].append(value)
        row = [biomarker]
        for i in range(len(values)):
            row.append('|'.join(values[i]))
        writer.writerow(row)


def main():
    parser = argparse.ArgumentParser(description='Convert RDF data to CSV')
    _ = parser.parse_args()
    
    rdf_graph = load_rdf_data()
    predicate_map = get_predicate_map(rdf_graph)
    
    write_output(rdf_graph, predicate_map)


if __name__ == '__main__':
    main()
