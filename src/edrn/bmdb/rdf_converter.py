# encoding: utf-8

import argparse
import csv
import json
import sys
import logging
from rdflib import Graph, URIRef

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')


def load_rdf_data():
    # Create a new RDF graph
    g = Graph()
    
    # Define the RDF data sources
    urls = [
        'https://bmdb.jpl.nasa.gov/rdf/biomarkers',
        'https://bmdb.jpl.nasa.gov/rdf/biomarker-organs'
    ]
    
    # Load RDF data from each source
    for url in urls:
        logging.info(f'Loading RDF data from {url}…')
        g.parse(url, format='xml')  # Assuming RDF/XML format
    
    logging.info(f'Loaded {len(g)} triples into the RDF graph.')
    return g


def filter_triples_by_predicates(graph, predicate_short_names, predicate_map):
    filtered_triples = []
    for name in predicate_short_names:
        if name not in predicate_map:
            logging.warning('Ignoring unknown short name %s', name)
            continue
        predicate_uri = predicate_map[name]
        filtered_triples.extend([(s, p, o) for s, p, o in graph if p == predicate_uri])
    return filtered_triples


def get_predicate_map(graph):
    predicate_map = {}
    for _, p, _ in graph:
        if isinstance(p, URIRef):
            short_name = graph.namespace_manager.qname(p).split(':', 1)[-1]  # Extract local part
            predicate_map[short_name] = p
    return predicate_map


def write_output(statements, output_format):
    if output_format == 'csv':
        writer = csv.writer(sys.stdout)
        writer.writerow(['Subject', 'Predicate', 'Object'])
        writer.writerows(statements)
    elif output_format == 'json':
        json.dump([{'subject': str(s), 'predicate': str(p), 'object': str(o)} for s, p, o in statements], sys.stdout, indent=4)
        sys.stdout.write('\n')


def main():
    parser = argparse.ArgumentParser(description='Load RDF data and filter by predicate.')
    parser.add_argument('predicate', type=str, nargs='*', help='Filter statements by this predicate short name.')
    parser.add_argument('--output', type=str, choices=['csv', 'json'], default='csv', help='Output format: csv or json (default: csv).')
    args = parser.parse_args()
    
    rdf_graph = load_rdf_data()
    predicate_map = get_predicate_map(rdf_graph)
    
    filtered_statements = filter_triples_by_predicates(rdf_graph, args.predicate, predicate_map)
    if args.output:
        write_output(filtered_statements, args.output)
    else:
        logging.info(f'Filtered Statements for predicate {args.predicate}:')
        for stmt in filtered_statements:
            logging.info(stmt)


if __name__ == '__main__':
    main()
