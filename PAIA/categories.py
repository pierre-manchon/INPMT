# -*-coding: utf8 -*
"""
PAIA tests

Tox: tests CI
Jenkins: Open source automation server
Devpi: PyPI server and packaging/testing/release tool

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
        get_pixel_diversity(dataset=cr, shapefile_area=x[1], band=0)
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


path_occsol = r'H:\Cours\M2\Cours\HGADU03 - Mémoire\Projet Impact PN Anophèles\Occupation du sol\Produit OS/' \
              r'ESACCI-LC-L4-LCCS-Map-300m-P1Y-1992_2015-v2.0.7/' \
              r'ESACCI-LC-L4-LCCS-Map-300m-P1Y-1992_2015-v2.0.7_AFRICA.tif'
path_population = r'H:\Cours\M2\Cours\HGADU03 - Mémoire\Projet Impact PN Anophèles\Population\population_dataset/' \
                  r'gab_ppp_2020_UNadj_constrained.tif'
path_country_boundaries = r'H:\Cours\M2\Cours\HGADU03 - Mémoire\Projet Impact PN Anophèles\Administratif/' \
                          r'Limites administratives/african_countries_boundaries.shp'
path_decoupage = r'H:/Cours/M2/Cours/HGADU03 - Mémoire/Projet Impact PN Anophèles/Administratif/decoupe_3857.shp'
"""
from pandas import DataFrame
from geopandas import GeoDataFrame
from typing import Any, AnyStr, Union
from alive_progress import alive_bar
from PAIA.processing import get_pas_profiles, get_pixel_diversity
from PAIA.utils.utils import format_dataset_output
from PAIA.utils.vector import intersect, is_of_interest
from PAIA.utils.raster import raster_crop

# Really not important tho
# Use the qgis project to get the list of files and the list of legend files
# TODO Use a list of files to unpack rather than multiple line vars
# Appears to be impossible due to qgz project file being a binary type file


def app(aoi: AnyStr, export: bool = False) -> tuple[
    DataFrame, GeoDataFrame, Union[Union[str, bytes], Any], GeoDataFrame, Union[Union[str, bytes], Any]]:
    path_pa_africa = r'H:/Cours/M2/Cours/HGADU03 - Mémoire/Projet Impact PN Anophèles/Occupation du sol/' \
                     r'Aires protegees/WDPA_Mar2021_Public_AFRICA_Land.shp'
    path_pa_buffer_africa = r'H:/Cours/M2/Cours/HGADU03 - Mémoire/Projet Impact PN Anophèles/Occupation du sol/' \
                            r'Aires protegees/WDPA_Mar2021_Public_AFRICA_Land_buffered10km.shp'
    path_urbain = r'H:\Cours\M2\Cours\HGADU03 - Mémoire\Projet Impact PN Anophèles\0/pop_polygonized_taille.shp'
    path_occsol_degrade = r'H:\Cours\M2\Cours\HGADU03 - Mémoire\Projet Impact PN Anophèles\Occupation du sol/' \
                          r'Produit OS/ESA CCI/ESACCI-LC-L4-LC10-Map-300m-P1Y-2016-v1.0.tif'
    path_anopheles = r'H:\Cours\M2\Cours\HGADU03 - Mémoire\Projet Impact PN Anophèles\Anophèles/VectorDB_1898-2016.shp'

    with alive_bar(total=11) as bar:
        bar.text('AOI:Intersection')  # Progress bar
        # Intersect and crop every layers with the area of interest
        gdf_pa_aoi, path_pa_aoi = intersect(base=path_pa_africa, overlay=aoi, crs=3857, export=True)
        bar()  # Progress bar
        gdf_pa_buffered_aoi, path_pa_buffered_aoi = intersect(base=path_pa_buffer_africa, overlay=aoi, crs=3857, export=True)
        bar()  # Progress bar
        gdf_anos_aoi, path_anos_aoi = intersect(base=path_anopheles, overlay=aoi, crs=3857, export=True)
        bar()  # Progress bar
        gdf_urban_aoi, path_urban_aoi = intersect(base=path_urbain, overlay=aoi, crs=3857, export=True)
        bar()  # Progress bar
        path_occsol_aoi = raster_crop(dataset=path_occsol_degrade, shapefile=aoi)
        bar()  # Progress bar

        # Intersect vector layers with the data of interest (mosquitoes, etc) to only keep the polygons we can analyze.
        #  keep all the PAs where we find anopheles
        bar.text('PAs:Anopheles')  # Progress bar
        gdf_pa_aoi_anos = is_of_interest(base=gdf_pa_aoi, interest=gdf_anos_aoi)
        bar()  # Progress bar
        """
        #  keep all the PAs where there is population
        bar.text('PAs:Population')  # Progress bar
        gdf_pa_aoi_anos_pop = is_of_interest(base=gdf_pa_aoi_anos, interest=gdf_urban_aoi)
        bar()  # Progress bar

        #  keep all the buffers of the PAs where there is anopheles and population. I process a buffer of 1m so the
        # polygons intersects otherwise they would just be next ot each other.
        bar.text('Buffers:PAs')  # Progress bar
        gdf_pa_aoi_anos_pop_buffer_tmp = gdf_pa_aoi_anos.buffer(1)
        gdf_pa_buffered_aoi_anos_pop = is_of_interest(base=gdf_pa_buffered_aoi, interest=gdf_pa_aoi_anos_pop_buffer_tmp)
        """
        bar()  # Progress bar
        bar.text('AOI:Pixel diversity')  # Progress bar
        df = get_pixel_diversity(dataset_path=path_occsol_aoi, band=0, export=True)
        bar()  # Progress bar

        bar.text('PAs:Profiling')  # Progress bar
        gdf_profiles_pas, path_profiles_pas = get_pas_profiles(geodataframe_aoi=gdf_pa_aoi_anos,
                                                               aoi=path_pa_aoi,
                                                               occsol=path_occsol_aoi,
                                                               population=path_urban_aoi,
                                                               anopheles=path_anos_aoi)
        bar()  # Progress bar
        bar.text('Buffers:Profiling')  # Progress bar
        gdf_profiles_buffer, path_profiles_buffer = get_pas_profiles(geodataframe_aoi=gdf_pa_buffered_aoi,
                                                                     aoi=path_pa_buffered_aoi,
                                                                     occsol=path_occsol_aoi,
                                                                     population=path_urban_aoi,
                                                                     anopheles=path_anos_aoi)
        bar()  # Progress bar

    if export:
        _, _, output_pas_profile = format_dataset_output(dataset=path_pa_aoi, name='profiling')
        _, _, output_pas_buffer_profile = format_dataset_output(dataset=path_pa_buffered_aoi, name='profiling')
        gdf_profiles_pas.to_file(output_pas_profile)
        gdf_profiles_buffer.to_file(output_pas_buffer_profile)
        return df, gdf_profiles_pas, path_profiles_pas, gdf_profiles_buffer, path_profiles_buffer
    else:
        return df, gdf_profiles_pas, path_profiles_pas, gdf_profiles_buffer, path_profiles_buffer


if __name__ == '__main__':
    path_aoi_gabon = r'H:\Cours\M2\Cours\HGADU03 - Mémoire\Projet Impact PN Anophèles/Administratif/' \
                     r'Limites administratives/gabon.shp'

    df, gdf_pas, _, gdf_buffers, _ = app(aoi=path_aoi_gabon,
                                         export=True)
