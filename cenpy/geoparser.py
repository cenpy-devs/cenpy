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
    for k,v in diter(egpt):
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
        from pysal.cg.shapes import Polygon, Chain, Point, asShape
        try:
            df['geometry'] = pd.Series([asShape(e) for e in df['geometry']])
        except:
            if 'Polygon' in first['type']:
                df['geometry'] = pd.Series([Polygon(e['coordinates'][0])\
                                            for e in df['geometry']])
            elif 'Line' in first['type']:
                df['geometry'] = pd.Series([Chain(e['coordinates'][0])\
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
                df['geometry'] = pd.Series([g.Polygon(e['coordinates'][0])\
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
