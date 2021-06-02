# -*-coding: utf8 -*
"""
PAIA tests

Tox: tests CI
Jenkins: Open source automation server
Devpi: PyPI server and packaging/testing/release tool
"""
from typing import Any
from geopandas import GeoDataFrame
from PAIA.processing import get_distances, get_categories, get_pas_profiles
from PAIA.utils.utils import get_config_value
from PAIA.utils.vector import intersect, isin
from PAIA.utils.raster import raster_crop

# Really not important tho
# Use the qgis project to get the list of files and the list of legend files
# TODO Use a list of files to unpack rather than multiple line vars
# Appears to be impossible due to qgz project file being a binary type file

path_occsol = r'H:\Cours\M2\Cours\HGADU03 - Mémoire\Projet Impact PN Anophèles\Occupation du sol\Produit OS/' \
              r'ESACCI-LC-L4-LCCS-Map-300m-P1Y-1992_2015-v2.0.7/' \
              r'ESACCI-LC-L4-LCCS-Map-300m-P1Y-1992_2015-v2.0.7_AFRICA.tif'
path_population = r'H:\Cours\M2\Cours\HGADU03 - Mémoire\Projet Impact PN Anophèles\Population\population_dataset/' \
              r'gab_ppp_2020_UNadj_constrained.tif'
path_country_boundaries = r'H:\Cours\M2\Cours\HGADU03 - Mémoire\Projet Impact PN Anophèles\Administratif/' \
                          r'Limites administratives/african_countries_boundaries.shp'
path_decoupage = r'H:/Cours/M2/Cours/HGADU03 - Mémoire/Projet Impact PN Anophèles/Administratif/decoupe_3857.shp'


path_limites_gabon = r'H:\Cours\M2\Cours\HGADU03 - Mémoire\Projet Impact PN Anophèles\Administratif/' \
                     r'Limites administratives/gabon.shp'
path_pa_africa = r'H:/Cours/M2/Cours/HGADU03 - Mémoire/Projet Impact PN Anophèles/Occupation du sol/Aires protegees/' \
          r'WDPA_Mar2021_Public_AFRICA_Land.shp'
# Same as the population raster but the polygonization/Geometry fixing process were passed to speed up the process
# (you don't need to do it everytime)
path_urbain = r'H:\Cours\M2\Cours\HGADU03 - Mémoire\Projet Impact PN Anophèles\0/pop_polygonized_taille.shp'

path_occsol_degrade = r'H:\Cours\M2\Cours\HGADU03 - Mémoire\Projet Impact PN Anophèles\Occupation du sol\Produit OS/' \
                      'ESA CCI/ESACCI-LC-L4-LC10-Map-300m-P1Y-2016-v1.0.tif'
path_anopheles = r'H:\Cours\M2\Cours\HGADU03 - Mémoire\Projet Impact PN Anophèles\Anophèles/VectorDB_1898-2016.shp'


def main(path_aoi) -> tuple[Any, Any, Any, Any, Any, Any, str, GeoDataFrame]:
    if path_aoi:
        buff_size = int(get_config_value('buff_size'))
        # Intersect and crop every layers with the area of interest
        gdf_pa_aoi, path_pa = intersect(base=path_pa_africa, overlay=path_aoi)
        gdf_anos_aoi, path_anos = intersect(base=path_anopheles, overlay=path_aoi)
        gdf_urban_aoi, path_urban = intersect(base=path_urbain, overlay=path_aoi)
        path_occsol_aoi = raster_crop(dataset=path_occsol_degrade, shapefile=path_aoi)
        gdf_pa_aoi['buffer'] = gdf_pa_aoi.buffer(buff_size)
        # Intersect vector layers with the data of interest (mosquitoes, etc) to only keep the polygons we can analyze.
        gdf_pa_gabon_anos = isin(base=gdf_pa_aoi, overlay=gdf_anos_aoi)
        return gdf_pa_aoi, path_pa, gdf_anos_aoi, path_anos, gdf_urban_aoi, path_urban, path_occsol_aoi, gdf_pa_gabon_anos
    else:
        pass


gdf_pa_gabon, path_pa, gdf_anos_gabon, path_anos, gdf_urban_gabon, path_urban, path_occsol_gabon, gdf_pa_gabon_anos = main(path_limites_gabon)
# df = get_categories(dataset_path=path_occsol_cropped, band=0, export=True)
gdf, path = get_pas_profiles(geodataframe_aoi=gdf_pa_gabon_anos,
                             aoi=path_pa,
                             occsol=path_occsol_gabon,
                             population=path_urban,
                             export=False)
"""
get_distances(pas=gdf_pa,
              urban_areas=gdf_urbain_gabon,
              path_urban_areas=path_urbain_gabon,
              export=True)
df, sf = read_shapefile_as_dataframe(path_country_boundaries)

In case the following contraption doesn'u work, this allows to get coordinates
for v in sf.__geo_interface__['features']:
    shape = v['geometry']['coordinates']

for x in zip(df.NAME, df.AREA, df.coords):
    if x[0] != '':
        cr = raster_crop(dataset=path_occsol, geodataframe=sf.shp.name)
        get_categories(dataset=cr, shapefile_area=x[1], band=0)
        # plot_shape(geodataframe=sf, dataframe=df, name=x)
    else:
        pass

https://automating-gis-processes.github.io/2017/lessons/L3/nearest-neighbour.html

https://stackoverflow.com/questions/39995839/gis-calculate-distance-between-point-and-polygon-border
load every layers
Illustrer difference Gabon/Afrique (proportion occsol/pays = Surface catégories/surface pays)
Stats pour Afrique, Zone présence Anophèles, Pays (polygonize dominant vectors)
Lister lesx variables calculables: proportion par buffer
Lien proximité/pop/parcs/anophèles

QGIS
Convertir les pixels urbains de l'occsol en polygone
CODE
Convertir ces polygones en mono parties.
Associer puis séparer les villages gros des villages petits.

Dans le premier cas, mesurer dans un premier temps la distance entre le bord de l'aire urbaine et le parc.
Dans le second cas, utiliser le centroïde pour ensuite mesurer la distance avec la bordure du parc.
=> Puis, dans un second temps, mesurer au sein de cellules/patchs la fragmentation des tâches urbaines.
"""
