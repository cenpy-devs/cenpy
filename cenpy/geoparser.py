import pandas as pd

def esriGeometryPolygon(egpoly):
    feature = {'type':'Feature'}
    egpoly['geometry']['coordinates'] = egpoly['geometry'].pop('rings', [])
    egpoly['geometry']['type'] = 'MultiPolygon'
    feature['properties'] = egpoly.pop('attributes', {})
    feature['crs'] = egpoly.pop('spatialReference', {})
    feature['geometry'] = egpoly.pop('geometry', {})
    return feature

def esriGeometryPolyLine(egpline):
    feature = {'type':'Feature'}
    egpline['geometry']['coordinates'] = egpline['geometry'].pop('paths', [])
    egpline['geometry']['type'] = 'MultiLineString'
    feature['properties'] = egpline.pop('attributes', {})
    feature['crs'] = egpline.pop('spatialReference', {})
    feature['geometry'] = egpline.pop('geometry', {})
    return feature

def esriGeometryPoint(egpt):
    feature = {'type':'Feature', 'properties':{}}
    address = [None, None, None, None]
    for k,v in egpt.items():
        try:
            address['xyzm'.index(k)] = v
        except ValueError:
            if k == 'spatialReference':
                feature['crs'] = v
            else:
                feature['properties'].update({k:v})
    address = [co for co in address if co is not None]
    feature['properties'].update(egpt.pop('attributes', {}))
    feature['geometry'] = {'coordinates':address, 'type':'Point'}
    return feature

def esriMultiPoint(egmpt):
    feature = {'type':'Feature', 'properties':{}}
    feature['geometry'] = {'coordinates':egmpt.pop('points', [])}
    feature['crs'] = egmpt.pop('spatialReference', {})
    feature['properties'].update(egmpt.pop('attributes', {}))
    feature['properties'].update({'hasM':egmpt.pop('hasM', False),
                                  'hasZ':egmpt.pop('hasZ', False)})
    return feature

def convert_geometries(df, pkg='pysal'):
    first = df['geometry'].head(1).tolist()[0]
    if pkg.lower() == 'pysal':
        from pysal.cg.shapes import Chain, Point, asShape
        try:
            df['geometry'] = pd.Series([asShape(e) for e in df['geometry']])
        except:
            if 'Polygon' in first['type']:
                df['geometry'] = pd.Series([parse_polygon_to_pysal(e)\
                                            for e in df['geometry']])
            elif 'Line' in first['type']:
                df['geometry'] = pd.Series([Chain(e['coordinates'])\
                                            for e in df['geometry']])
            elif 'MultiPoint' in first['type']:
                df['geometry'] = pd.Series([[Point(c) for c in e['coordinates']]\
                                            for e in df['geometry']])
            elif 'Point' in first['type']:
                df['geometry'] = pd.Series([Point(e['coordinates'][0])\
                                            for e in df['geometry']])
    elif pkg.lower() == 'shapely':
        from shapely import geometry as g
        try:
            df['geometry'] = pd.Series([g.__dict__[e['type']](e) for e in df['geometry']])
        except:
            if 'Polygon' in first['type']:
                df['geometry'] = pd.Series([parse_polygon_to_shapely(e)\
                                            for e in df['geometry']])
            elif 'MultiLine' in first['type']:
                df['geometry'] = pd.Series([g.MultiLineString(e['coordinates'])\
                                            for e in df['geometry']])
            elif 'MultiPoint' in first['type']:
                df['geometry'] = pd.Series([g.MultiPoint(e['coordinates']) 
                                            for e in df['geometry']])
            elif 'Point' in first['type']:
                df['geometry'] = pd.Series([g.Point(e['coordinates'][0])\
                                            for e in df['geometry']])
    return df

from pysal.cg import is_clockwise as _is_cw
def parse_polygon_to_pysal(raw_feature):
    """
    get an OGC polygon from an input ESRI ring array.
    """
    pgon_type, ogc_nest = _get_polygon_type(raw_feature)
    from pysal.cg import Polygon
    if pgon_type in ('Polygon', 'MultiPolygon'):
        return Polygon(ogc_nest)
    elif pgon_type == 'Polygon with Holes':
        return Polygon(ogc_nest[0], holes=ogc_nest[1:])
    elif pgon_type == 'MultiPolygon with Holes':
        return Polygon(vertices = [ring[0] for ring in ogc_nest], 
                       holes = [ring[1:] for ring in ogc_nest])
    else:
        raise Exception('Unexpected Polygon kind {} provided to'
                        ' parse_polygon_to_pysal'.format(pgon_type)) 

def parse_polygon_to_shapely(raw_feature):
    pgon_type, ogc_nest = _get_polygon_type(raw_feature)
    from shapely.geometry import Polygon, MultiPolygon
    if pgon_type == 'Polygon':
        return Polygon(ogc_nest)
    elif pgon_type == 'Polygon with Holes':
        return Polygon(shell=ogc_nest[0], holes=ogc_nest[1:])
    elif pgon_type == 'MultiPolygon':
        return MultiPolygon(Polygon(s, holes=None) for s in ogc_nest)
    elif pgon_type == 'MultiPolygon with Holes':
        return MultiPolygon(polygons=[Polygon(shell=ring[0], holes=ring[1:]) 
                                      for ring in ogc_nest])
    else:
        raise Exception('Unexpected Polygon kind {} provided to'
                        ' parse_polygon_to_shapely'.format(pgon_type))

def _get_polygon_type(raw_feature):
    """
    Return an indication of what kind of polygon the raw feature is as well as a representation of the internal/external ring nestings. Polygons (by the OGC) can be:
    Polygon
    Polygon with holes
    Multipolygon
    Multipolygon with holes

    I'm going to assume that the ESRI rings are ordered such that they at least attempt to mimick an OGC nested ordering:

    (((External, ring, vertices), (Optional, hole, ring, vertices), ...), 
      ((Optional second, external, ring, vertices), (Optional hole, ring, vertices), ...))

    Since ESRI Rings are directional, clockwise rings are exterior and holes are counterclockwise. So, I'm assuming that the ESRI polygons returned from the census buereau nest their potential holes such that:

    [[Clockwise, ring, vertices], [Optional, counterclockwise, hole, vertices], ..., 
     [New, optional, clockwise, external, ring, vertices], 
     [Optional, counterclockwise, hole, vertices], ...]

    Which means that when you pass over them as "is clockwise" you only get patterns like:

    Exterior Clockwise() == True
        Hole Clockwise() == False 
        Hole Clockwise() == False 
        Hole Clockwise() == False 
    Exterior Clockwise() == True 
        Hole Clockwise() == False 
    Exterior Clockwise() == True 
        Hole Clockwise() == False

    where all non-clockwise rings after a clockwise ring are "owned" by the last seen preceeding clockwise ring. 

    If this does not hold, the polygons will not be valid OGC multipolygons without testing which rings nest other rings, a potentially expensive GIS operation. 
    """
    ring_array = raw_feature['coordinates']
    if len(ring_array) <= 1:
        return "Polygon", ring_array[0]
    else:
        clockwise_sequence = list(map(_is_cw, ring_array))
        if sum(clockwise_sequence) == 1: #only one ring is clockwise (external)
            return "Polygon with Holes", ring_array
        else:
            if sum(clockwise_sequence) == len(clockwise_sequence): #all rings are clockwise (external)
                return "MultiPolygon", ring_array
            else:

                return "MultiPolygon with Holes", _parse_clockwise_sequence(ring_array, 
                                                                            clockwise_sequence) 

def _parse_clockwise_sequence(ring_array, clockwise_sequence=None):
    """
    Assign a set of mixed interior/exterior rings to their exterior ring assuming
    the rings are ordered:

    Exterior Clockwise() == True
        Hole Clockwise() == False 
        Hole Clockwise() == False 
        Hole Clockwise() == False 
    Exterior Clockwise() == True 
        Hole Clockwise() == False 
    Exterior Clockwise() == True 
        Hole Clockwise() == False

    where all non-clockwise rings after a clockwise ring are "owned" by the last seen preceeding clockwise ring. 

    If this does not hold, the polygons will not be valid OGC multipolygons without testing which rings nest other rings, a potentially expensive GIS operation. 
    """
    if clockwise_sequence is None:
        clockwise_sequence = list(map(_is_cw, ring_array))
    OGC_nest = []
    for ring, is_cw in zip(ring_array, clockwise_sequence):
        if is_cw:
            OGC_nest.append([ring])
        else:
            OGC_nest[-1].append(ring)
    return OGC_nest
