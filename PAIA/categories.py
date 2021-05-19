# -*-coding: utf8 -*
"""
PAIA tests

Tox: tests CI
Jenkins: Open source automation server
Devpi: PyPI server and packaging/testing/release tool
"""
from .plotting import plot_shape
from .processing import get_categories
from .raster import raster_crop
from .vector import read_shapefile_as_dataframe

# Really not important tho
# Use the qgis project to get the list of files and the list of legend files
# TODO Use a list of files to unpack rather than multiple line vars
# Appears to be impossible due to qgz project file being a binary type file

path_occsol = r'H:\Cours\M2\Cours\HGADU03 - Mémoire\Projet Impact PN Anophèles\Occupation du sol\Produit OS/' \
              r'ESACCI-LC-L4-LCCS-Map-300m-P1Y-1992_2015-v2.0.7/' \
              r'ESACCI-LC-L4-LCCS-Map-300m-P1Y-1992_2015-v2.0.7_AFRICA.tif'
path_urbain = r'H:\Cours\M2\Cours\HGADU03 - Mémoire\Projet Impact PN Anophèles\Population\population_dataset/' \
              r'gab_ppp_2020_UNadj_constrained.tif'
path_pa = r'H:/Cours/M2/Cours/HGADU03 - Mémoire/Projet Impact PN Anophèles/Occupation du sol/Aires protegees/' \
          r'WDPA_Mar2021_Public_AFRICA_Land.shp'
path_boundaries = r'H:/Cours/M2/Cours/HGADU03 - Mémoire/Projet Impact PN Anophèles/Administratif/' \
                  r'Limites administratives/africa_boundary.shp'
path_country_boundaries = r'H:\Cours\M2\Cours\HGADU03 - Mémoire\Projet Impact PN Anophèles\Administratif/' \
                          r'Limites administratives/african_countries_boundaries.shp'
path_decoupage = r'H:/Cours/M2/Cours/HGADU03 - Mémoire/Projet Impact PN Anophèles/Administratif/decoupe_3857.shp'
path_occsol_decoupe = r'H:/Cours/M2/Cours/HGADU03 - Mémoire/Projet Impact PN Anophèles/Occupation du sol/Produit OS/' \
                      r'ESACCI-LC-L4-LCCS-Map-300m-P1Y-1992_2015-v2.0.7/mask.tif'

df, sf = read_shapefile_as_dataframe(path_country_boundaries)
"""
In case the following contraption doesn't work, this allows to get coordinates
for v in sf.__geo_interface__['features']:
    shape = v['geometry']['coordinates']
"""
for x in zip(df.NAME, df.AREA, df.coords):
    if x[0] != '':
        cr = raster_crop(dataset=path_occsol, shapefile=sf.shp.name)
        get_categories(dataset=cr, shapefile_area=x[1], band=0)
        # plot_shape(shapefile=sf, dataframe=df, name=x)
    else:
        pass

# get_categories(dataset=path_occsol_decoupe, band=0)
# raster_crop(dataset=path_occsol, shapefile=path_decoupage)

# https://stackoverflow.com/questions/39995839/gis-calculate-distance-between-point-and-polygon-border
# load every layers
# Illustrer difference Gabon/Afrique (proportion occsol/pays = Surface catégories/surface pays)
# Stats pour Afrique, Zone présence Anophèles, Pays (polygonize dominant vectors)
# Lister lesx variables calculables: proportion par buffer
# Lien proximité/pop/parcs/anophèles

"""
QGIS
Convertir les pixels urbains de l'occsol en polygone mono parties.
CODE
Associer puis séparer les villages gros des villages petits.
Dans le premier cas, mesurer dans un premier temps la distance entre le bord de l'aire urbaine et le parc. Puis, dans
un second temps, mesurer au sein de cellules/patchs la fragmentation des tâches urbaines.
Dans le second cas, utiliser le centroïde pour ensuite mesurer la distance avec la bordure du parc. 
"""
