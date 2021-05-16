from shapely.geometry import shape


def esri_geometry_polygon_to_shapely(geometry):
    coordinates = [[tuple(i) for i in geometry["rings"]]]
    return shape(
        {
            "coordinates": coordinates,
            "type": "MultiPolygon",
        }
    )
