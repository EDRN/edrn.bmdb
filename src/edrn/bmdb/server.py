# encoding: utf-8

'''RDF server'''

from .rdf import publications, biomarkers, organs, resources
from datetime import datetime
from pyramid.config import Configurator
from pyramid.response import Response
from pyramid.view import view_config
from wsgiref.simple_server import make_server
import os, pymysql, rdflib, sys


# Map from an RDF serialization format to a corresponding MIME content type

_serializationContentTypes = {
    'n3': 'text/n3',
    'xml': 'application/rdf+xml',
    'turtle': 'text/turtle',
    'trig': 'text/plain',
    'nt': 'application/n-triples',
    'nt11': 'text/plain',
    'pretty-xml': 'application/rdf+xml',
}


class _View(object):
    '''An abstract Pyramid web framework view'''
    def __init__(self, request):
        '''Initialize this view with the given HTTP request'''
        self.request = request

    def database(self):
        '''Tell what database connection to use for this view'''
        return pymysql.connect(
            host=self.request.registry['database.host'],
            user=self.request.registry['database.user'],
            passwd=self.request.registry['database.passwd'],
            db=self.request.registry['database.db'],
            charset='utf8mb4'
        )


class PingView(_View):
    '''A view that just tells uptime or other basic statistics'''
    @view_config(route_name='ping', renderer='json')
    def __call__(self):
        '''Give up a JSON dict with uptime in seconds plus total biomarkers'''
        with self.database().cursor() as cursor:
            cursor.execute('SELECT COUNT(*) FROM `biomarkers`')
            count = int(cursor.fetchone()[0])
            uptime = datetime.utcnow() - self.request.registry['start_time']
            return {'biomarkers': count, 'uptime': uptime.total_seconds()}


class _RDFView(_View):
    '''An abstract view that yields RDF'''
    def __init__(self, request):
        '''Initialize this with an HTTP request and also a blank RDF graph'''
        super(_RDFView, self).__init__(request)
        self.graph = rdflib.Graph()

    def includePrivate(self):
        '''Return true if the request for this view wants *all* entities or False if just the public ones'''
        supplied, expected = self.request.params.get('all'), os.getenv('TOKEN')
        rc = supplied == expected
        return rc

    def serialize(self, graph):
        '''Serialize the given RDF ``graph`` into an HTTP response'''
        serializationFormat = self.request.params.get('format', 'pretty-xml')
        if serializationFormat not in _serializationContentTypes:
            valids = [', '.join(_serializationContentTypes.keys())]
            raise ValueError('Unknown serialization format; valid formats are ' + valids)
        body = graph.serialize(format=serializationFormat)
        return Response(body, content_type=_serializationContentTypes[serializationFormat])


class ExampleView(_RDFView):
    '''An RDF view for demonstration purposes.'''
    @view_config(route_name='example')    
    def __call__(self):
        graph = rdflib.Graph()
        subj1 = rdflib.URIRef('urn:example:subjects:1')
        type_rdf = rdflib.namespace.RDF.type
        kind = rdflib.URIRef('urn:example:types:indicator')
        pred = rdflib.URIRef('urn:example:predicates:side')
        graph.add((subj1, pred, rdflib.Literal('left')))
        graph.add((subj1, type_rdf, kind))
        if self.request.params.get('all') == 'right':
            subj2 = rdflib.URIRef('urn:example:subjects:2')
            graph.add((subj2, pred, rdflib.Literal('right')))
            graph.add((subj2, type_rdf, kind))
        return self.serialize(graph)


class PublicationsRDFView(_RDFView):
    '''An RDF view for publications'''
    @view_config(route_name='pub')
    def __call__(self):
        publications(self.database(), self.graph, not self.includePrivate())
        return self.serialize(self.graph)


class ResourcesRDFView(_RDFView):
    '''An RDF view for resources'''
    @view_config(route_name='res')
    def __call__(self):
        resources(self.database(), self.graph, not self.includePrivate())
        return self.serialize(self.graph)


class BiomarkersRDFView(_RDFView):
    '''An RDF view for biomarkers'''
    @view_config(route_name='bio')
    def __call__(self):
        biomarkers(self.database(), self.graph, not self.includePrivate())
        return self.serialize(self.graph)


class BiomarkerOrgansView(_RDFView):
    '''An RDF view for biomarker-organ information'''
    @view_config(route_name='bio-organ')
    def __call__(self):
        organs(self.database(), self.graph, not self.includePrivate())
        return self.serialize(self.graph)


def main():
    '''Run a small WSGI server to serve up RDF from Focus BMDB'''

    if not os.getenv('TOKEN'):
        print(
            'The TOKEN environment variable must be set to the security token to reveal private information',
            file=sys.stderr
        )
        sys.exit(-1)

    with Configurator() as config:
        config.registry['database.host'] = os.environ.get('BMDB_HOST', 'localhost')
        config.registry['database.user'] = os.environ.get('BMDB_USER', 'cbmdb')
        config.registry['database.passwd'] = os.environ.get('BMDB_PASSWORD', 'cbmdb')
        config.registry['database.db'] = os.environ.get('BMDB_DB', 'cbmdb')
        config.registry['start_time'] = datetime.utcnow()

        config.add_route('ping', '/ping')
        config.add_route('pub', '/publications')
        config.add_route('res', '/resources')
        config.add_route('bio', '/biomarkers')
        config.add_route('bio-organ', '/biomarker-organs')
        config.add_route('example', '/example')

        config.scan()
        app = config.make_wsgi_app()
        server = make_server('0.0.0.0', 6543, app)
        server.serve_forever()


if __name__ == '__main__':
    main()
