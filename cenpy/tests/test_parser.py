import geopandas as gpd
import pandas as pd
import numpy
from unittest import TestCase, skip, main
import os
from ..geoparser import parse_polygon_to_shapely,parse_polygon_to_pysal
from ..base import Connection

DIRPATH = os.path.dirname(__file__)

class Geoparser_Test(TestCase):

    def setUp(self):
        answers = gpd.read_file(DIRPATH + '/answers.geojson')
        tests = pd.read_json(DIRPATH + '/tests.json')
        hard_tests = pd.read_json(DIRPATH + '/degenerate.json')
        self.all = answers.merge(tests, on='names').merge(hard_tests, on='names')
        self.conn = Connection('DECENNIALSF12010')
        self.conn.set_mapservice('tigerWMS_Census2010')

    def test_shapely_conversion(self):
        for i,row in self.all.iterrows():
            name, answer, test, degenerate = row
            converted = parse_polygon_to_shapely(dict(coordinates=test))
            approx = answer.almost_equals(converted)
            exact = answer.equals(converted)
            self.assertTrue(approx or exact, 
                            msg="Conversion fails on test shape {}".format(name))
            if degenerate is not None:
                converted2 = parse_polygon_to_shapely(dict(coordinates=degenerate))
                approx = answer.almost_equals(converted2)
                exact = answer.equals(converted2)
                self.assertTrue(approx or exact, 
                                msg="Conversion fails on degenerate test shape "
                                    "{}".format(name))

    def test_pysal_conversion(self):
        for i,row in self.all.iterrows():
            name, answer, test, degenerate = row
            converted = parse_polygon_to_pysal(dict(coordinates=test))
            testset = set([tuple([tuple(pt) for pt in ring]) for ring in test])
            #print(name)
            #print('test: {}'.format(test))
            try:
                converted.parts[0][0][0] # is it multi or single?
                pssingle = False
                allrings = converted.parts # multi, since you can reach in rings -> ring -> point
            except TypeError:
                allrings = [converted.parts] # single, since you can only go ring -> point
                pssingle = True
            unholey = converted._holes == [[]]
            if not unholey:
                allrings = allrings + converted._holes
            #print('pysal: {} ({}, {})'.format(allrings, unholey, pssingle))
            allset = set([tuple([tuple(pt) for pt in ring]) for ring in allrings])
            revset = set([tuple(reversed([tuple(pt) for pt in ring]))
                          for ring in allrings])
            self.assertTrue(testset.issubset(allset.union(revset)), 
                             msg="Conversion fails on test shape {}".format(name))

    def test_pysal_polygon(self):
        # Isla Vista CDP, Polygon
        geodata = self.conn.mapservice.query(layer=36, where='PLACE=36868')
        numpy.testing.assert_allclose(geodata.total_bounds, numpy.array([-13345123.4905,
                                                                         4083187.9895,
                                                                         -13340209.9595,
                                                                         4085919.385 ]))

    def test_pysal_multi_polygon(self):
        # East Rancho Dominguez CDP, MultiPolygon
        geodata = self.conn.mapservice.query(layer=36, where='PLACE=21034')
        numpy.testing.assert_allclose(geodata.total_bounds, numpy.array([-13158648.204 ,
                                                                         4012917.1367,
                                                                         -13156433.948 ,
                                                                         4016243.6976]))

    def test_pysal_holed_polygon(self):
        # West Modesto CDP, Polygon with Holes
        geodata = self.conn.mapservice.query(layer=36, where='PLACE=84578')
        numpy.testing.assert_allclose(geodata.total_bounds, numpy.array([-13476102.0034,
                                                                         4523871.6742,
                                                                         -13471164.8727,
                                                                         4527488.4349]))

    def test_pysal_holed_multi_polygon(self):
        # East Porterville CDP, MultiPolygon with Holes
        geodata = self.conn.mapservice.query(layer=36, where='PLACE=21012')
        numpy.testing.assert_allclose(geodata.total_bounds, numpy.array([-13247907.9566,
                                                                         4307142.6093,
                                                                         -13238473.741 ,
                                                                         4310175.0494]))

if __name__ == '__main__':
    main()
