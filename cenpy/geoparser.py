
from shapely.geometry import shape


def esri_geometry_polygon_to_shapely(geometry):
    coordinates = [[tuple(i) for i in geometry['rings']]]
    return shape({
        'coordinates': coordinates,
        'type': 'MultiPolygon',
    })


if __name__ == '__main__':

    from src import ACS
    acs = ACS(2019)
    df = acs.query('B01001_001E', 'county:071', 'state:06')
    geometry = df['geometry'][0]
