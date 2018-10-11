import geopandas as gpd
from warnings import warn
from gdal import osr, ogr
import shutil

from urllib.request import urlopen
from zipfile import ZipFile
import os
import tempfile


class FTPConnection(object):
    def __init__(self, year, statenum, stateabbr, county, geom='tract'):

        url = {
            2000:
            'https://www2.census.gov/geo/tiger/TIGER2003/{statenum}_{stateabbr}/tgr{statenum}{county}.zip'.
            format(statenum=statenum, stateabbr=stateabbr, county=county),
            1990:
            'https://www2.census.gov/geo/tiger/TIGER1992/{statenum}/{statenum}{county}.zip'.
            format(statenum=statenum, stateabbr=stateabbr, county=county)
        }

        self.url = url[year]
        self.statenum = statenum
        self.stateabbr = stateabbr
        self.county = county
        self.geom = geom

    def _tiger_to_tract(self, infile):
        """ Converts collection of Census Tiger files into a geopandas.GeoDataFrame of census tracts
            Modified from original at
            https://svn.osgeo.org/gdal/tags/1.4.3/gdal/pymod/samples/tigerpoly.py
        """

        class Module(object):
            def __init__(mod):
                mod.lines = {}
                mod.poly_line_links = {}

        outfile = 'tracts.shp'

        # Open the datasource to operate on.
        ds = ogr.Open(infile, update=0)
        poly_layer = ds.GetLayerByName('Polygon')

        # Create output file for the composed polygons.
        nad83 = osr.SpatialReference()
        nad83.SetFromUserInput('NAD83')

        shp_driver = ogr.GetDriverByName('ESRI Shapefile')
        shp_driver.DeleteDataSource(outfile)

        shp_ds = shp_driver.CreateDataSource(outfile)
        shp_layer = shp_ds.CreateLayer(
            'out', geom_type=ogr.wkbPolygon, srs=nad83)

        src_defn = poly_layer.GetLayerDefn()
        poly_field_count = src_defn.GetFieldCount()

        for fld_index in range(poly_field_count):
            src_fd = src_defn.GetFieldDefn(fld_index)

            fd = ogr.FieldDefn(src_fd.GetName(), src_fd.GetType())
            fd.SetWidth(src_fd.GetWidth())
            fd.SetPrecision(src_fd.GetPrecision())
            shp_layer.CreateField(fd)

        # Read all features in the line layer, holding just the geometry in a hash
        # for fast lookup by TLID.

        line_layer = ds.GetLayerByName('CompleteChain')
        line_count = 0

        modules_hash = {}

        feat = line_layer.GetNextFeature()
        geom_id_field = feat.GetFieldIndex('TLID')
        tile_ref_field = feat.GetFieldIndex('MODULE')
        while feat is not None:
            geom_id = feat.GetField(geom_id_field)
            tile_ref = feat.GetField(tile_ref_field)

            try:
                module = modules_hash[tile_ref]
            except:
                module = Module()
                modules_hash[tile_ref] = module

            module.lines[geom_id] = feat.GetGeometryRef().Clone()
            line_count = line_count + 1

            feat.Destroy()

            feat = line_layer.GetNextFeature()

        # Read all polygon/chain links and build a hash keyed by POLY_ID listing
        # the chains (by TLID) attached to it.

        link_layer = ds.GetLayerByName('PolyChainLink')

        feat = link_layer.GetNextFeature()
        geom_id_field = feat.GetFieldIndex('TLID')
        tile_ref_field = feat.GetFieldIndex('MODULE')
        lpoly_field = feat.GetFieldIndex('POLYIDL')
        rpoly_field = feat.GetFieldIndex('POLYIDR')

        link_count = 0

        while feat is not None:
            module = modules_hash[feat.GetField(tile_ref_field)]

            tlid = feat.GetField(geom_id_field)

            lpoly_id = feat.GetField(lpoly_field)
            rpoly_id = feat.GetField(rpoly_field)

            if lpoly_id == rpoly_id:
                feat.Destroy()
                feat = link_layer.GetNextFeature()
                continue

            try:
                module.poly_line_links[lpoly_id].append(tlid)
            except:
                module.poly_line_links[lpoly_id] = [tlid]

            try:
                module.poly_line_links[rpoly_id].append(tlid)
            except:
                module.poly_line_links[rpoly_id] = [tlid]

            link_count = link_count + 1

            feat.Destroy()

            feat = link_layer.GetNextFeature()

        # Process all polygon features.

        feat = poly_layer.GetNextFeature()
        tile_ref_field = feat.GetFieldIndex('MODULE')
        polyid_field = feat.GetFieldIndex('POLYID')

        degenerate_count = 0

        while feat is not None:
            module = modules_hash[feat.GetField(tile_ref_field)]
            polyid = feat.GetField(polyid_field)

            tlid_list = module.poly_line_links[polyid]

            link_coll = ogr.Geometry(type=ogr.wkbGeometryCollection)
            for tlid in tlid_list:
                geom = module.lines[tlid]
                link_coll.AddGeometry(geom)

            try:
                poly = ogr.BuildPolygonFromEdges(link_coll)

                if poly.GetGeometryRef(0).GetPointCount() < 4:
                    degenerate_count = degenerate_count + 1
                    poly.Destroy()
                    feat.Destroy()
                    feat = poly_layer.GetNextFeature()
                    continue

                feat2 = ogr.Feature(feature_def=shp_layer.GetLayerDefn())

                for fld_index in range(poly_field_count):
                    feat2.SetField(fld_index, feat.GetField(fld_index))

                feat2.SetGeometryDirectly(poly)

                shp_layer.CreateFeature(feat2)
                feat2.Destroy()

            except:
                warn('BuildPolygonFromEdges failed.')

            feat.Destroy()

            feat = poly_layer.GetNextFeature()

        if degenerate_count:
            warn('Discarded %d degenerate polygons.' % degenerate_count)

        # Cleanup

        shp_ds.Destroy()
        shp_ds = None
        ds.Destroy()
        ds = None

        # build a fully-qualified fips code and dissolve on it to create tract geographies
        gdf = gpd.read_file(outfile)

        if "CTBNA90" in gdf.columns:

            gdf = gdf.rename(columns={"CTBNA90": 'TRACT', "BLK90": "BLOCK"})

        gdf['STATE'] = gdf['STATE'].astype(str).str.rjust(2, "0")
        gdf['COUNTY'] = gdf['COUNTY'].astype(str).str.rjust(3, "0")
        gdf['TRACT'] = gdf['TRACT'].astype(str).str.rjust(6, "0")
        gdf['BLOCK'] = gdf['BLOCK'].astype(str).str.rjust(4, "0")
        gdf['fips'] = gdf.STATE + gdf.COUNTY + gdf.TRACT
        if self.geom == 'block':
            gdf['fips'] += gdf.BLOCK

        gdf = gdf.dropna(subset=['fips'])
        gdf.geometry = gdf.buffer(0)
        gdf = gdf.dissolve(by='fips')
        gdf.reset_index(inplace=True)

        shp_driver.DeleteDataSource(outfile)

        return gdf

    def query(self):

        with urlopen(self.url) as response:
            with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
                shutil.copyfileobj(response, tmp_file)
                with tempfile.TemporaryDirectory() as tempdir:
                    ZipFile(tmp_file, 'r').extractall(tempdir)
                    fn = os.path.join(
                        tempdir, "TGR{statenum}{county}".format(
                            statenum=self.statenum, county=self.county))
                    if os.path.exists(fn + ".RTA"):
                        tracts = self._tiger_to_tract(fn + ".RTA")
                    else:
                        tracts = self._tiger_to_tract(fn + ".F5A")

        return tracts
