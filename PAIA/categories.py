# -*-coding: utf8 -*
"""
PAIA
A tool to process data to learn more about Protected Areas Impact on Malaria Transmission

Copyright (C) <2021>  <Manchon Pierre>

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.


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


path_occsol = r'H:/Cours/M2/Cours/HGADU03 - Mémoire/Projet Impact PN Anophèles/Occupation du sol/Produit OS/' \
              r'ESACCI-LC-L4-LCCS-Map-300m-P1Y-1992_2015-v2.0.7/' \
              r'ESACCI-LC-L4-LCCS-Map-300m-P1Y-1992_2015-v2.0.7_AFRICA.tif'
path_population = r'H:/Cours/M2/Cours/HGADU03 - Mémoire/Projet Impact PN Anophèles/Population/population_dataset/' \
                  r'gab_ppp_2020_UNadj_constrained.tif'
path_country_boundaries = r'H:/Cours/M2/Cours/HGADU03 - Mémoire/Projet Impact PN Anophèles/Administratif/' \
                          r'Limites administratives/african_countries_boundaries.shp'
path_decoupage = r'H:/Cours/M2/Cours/HGADU03 - Mémoire/Projet Impact PN Anophèles/Administratif/decoupe_3857.shp'


# Intersect and crop every layers with the area of interest
gdf_anos_aoi, path_anos_aoi = intersect(base=path_anopheles,
                                        overlay=aoi,
                                        crs=3857,
                                        export=True)

gdf_urban_aoi, path_urban_aoi = intersect(base=path_urbain,
                                          overlay=aoi,
                                          crs=3857,
                                          export=True)

path_occsol_aoi = raster_crop(dataset=path_occsol_degrade, shapefile=aoi)

# Keep all the PAs where there is population
gdf_pa_aoi_anos_pop = is_of_interest(base=gdf_pa_aoi, interest=gdf_urban_aoi)

# Keep all the buffers of the PAs where there is anopheles and population. I process a buffer of 1m so the
# polygons intersects otherwise they would just be next ot each other.
gdf_pa_aoi_anos_pop_buffer_tmp = gdf_pa_aoi.buffer(1)
gdf_pa_buffered_aoi_anos_pop = is_of_interest(base=gdf_pa_aoi, interest=gdf_pa_aoi_anos_pop_buffer_tmp)
"""
from typing import AnyStr
from geopandas import GeoDataFrame
from processing import get_profile
from utils.utils import format_dataset_output
from utils.vector import __read_shapefile_as_geodataframe

# Really not important tho
# Use the qgis project to get the list of files and the list of legend files
# TODO Use a list of files to unpack rather than multiple line vars
# Appears to be impossible due to qgz project file being a binary type file


def app(aoi: AnyStr, export: bool = False) -> GeoDataFrame:
    """
    Docstring

    :param aoi:
    :type aoi:
    :param export:
    :type export:
    :return:
    :rtype:
    """
    path_urbain = r'H:\Cours\M2\Cours\HGADU03 - Mémoire\Projet Impact PN Anophèles\0/pop_polygonized_taille.shp'
    path_occsol_degrade = r'H:\Cours\M2\Cours\HGADU03 - Mémoire\Projet Impact PN Anophèles\Occupation du sol/' \
                          r'Produit OS/ESA CCI/ESACCI-LC-L4-LC10-Map-300m-P1Y-2016-v1.0.tif'
    path_anopheles = r'H:\Cours\M2\Cours\HGADU03 - Mémoire\Projet Impact PN Anophèles\Anophèles/VectorDB_1898-2016.shp'

    # Read file as a geodataframe
    gdf_aoi = __read_shapefile_as_geodataframe(aoi)
    gdf_profiles_aoi, path_profiles_aoi = get_profile(geodataframe_aoi=gdf_aoi,
                                                      aoi=aoi,
                                                      habitat=path_occsol_degrade,
                                                      population=path_urbain,
                                                      anopheles=path_anopheles)

    if export:
        # Retrieves the directory the dataset is in and joins it the output filename
        _, _, output_countries = format_dataset_output(dataset=aoi, name='profiling')
        gdf_profiles_aoi.to_file(output_countries)
        return gdf_profiles_aoi
    else:
        return gdf_profiles_aoi


if __name__ == '__main__':
    path_countries_irish = r'H:\Cours\M2\Cours\HGADU03 - Mémoire\Projet Impact PN Anophèles\Administratif/' \
                           r'Limites administratives/africa_countries_irish.shp'
    path_pas = r'H:/Cours/M2/Cours/HGADU03 - Mémoire/Projet Impact PN Anophèles/Occupation du sol/' \
               r'Aires protegees/WDPA_Africa_anopheles.shp'
    path_pa_buffer_africa = r'H:/Cours/M2/Cours/HGADU03 - Mémoire/Projet Impact PN Anophèles/Occupation du sol/' \
                            r'Aires protegees/WDPA_Mar2021_Public_AFRICA_Land_buffered10km.shp'

    gdf_profiles_PAs = app(aoi=path_countries_irish)
