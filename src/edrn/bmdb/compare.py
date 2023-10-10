# encoding: utf-8

'''RDF comparisons'''

import rdflib, argparse, logging, sys
from rdflib.compare import similar

_logger = logging.getLogger(__name__)


def main():
    logging.basicConfig(level=logging.INFO, format='%(levelname)-8s %(message)s')
    parser = argparse.ArgumentParser(description="Compare two RDF graphs for equality")
    parser.add_argument('graph1', help='First graph', type=argparse.FileType('r'))
    parser.add_argument('graph2', help='Second graph', type=argparse.FileType('r'))
    parser.add_argument('-f', '--format', default='xml', help='Type of the graphs; default %(default)s')
    args = parser.parse_args()
    graph1 = rdflib.Graph().parse(args.graph1, format=args.format)
    graph2 = rdflib.Graph().parse(args.graph2, format=args.format)
    are_similar = similar(graph1, graph2)
    print('similar' if are_similar else 'not similar')
    sys.exit(0 if are_similar else -1)
    breakpoint()


if __name__ == '__main__':
    main()
