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
"""
import math
import numpy as np
import pandas as pd
import libpysal as lps
from alive_progress import alive_bar
from pandas import DataFrame
from geopandas import GeoDataFrame
from typing import AnyStr, SupportsInt

try:
    from utils.vector import merge_touching, to_wkt, iter_poly, intersect
    from utils.raster import raster_crop, get_pixel_count, polygonize
    from utils.utils import format_dataset_output, getConfigValue, read_qml
except ImportError:
    from .utils.vector import merge_touching, to_wkt, iter_poly, intersect
    from .utils.raster import raster_crop, get_pixel_count, polygonize
    from .utils.utils import format_dataset_output, getConfigValue, read_qml


def set_urban_profile(
        urban_areas: GeoDataFrame,
        path_urban_areas: AnyStr,
        urban_treshold: SupportsInt,
        export: bool = False
) -> GeoDataFrame:
    """
    # TODO
    """
    merging_result = merge_touching(geodataframe=urban_areas)

    result = []
    for poly in merging_result.geometry:
        if poly.area <= urban_treshold:
            result.append("small")
        else:
            result.append("large")
    del poly

    merging_result["Size"] = result
    del result

    if export:
        _, _, output_path = format_dataset_output(dataset=path_urban_areas, name='urban_extent')
        merging_result.to_file(output_path)
        return merging_result
    else:
        return merging_result


def get_distances(pas: GeoDataFrame,
                  urban_areas: GeoDataFrame,
                  path_urban_areas: AnyStr,
                  export: bool = False
                  ) -> DataFrame:
    """
    # TODO
    """
    urban_treshold = getConfigValue('urban_area_treshold')
    ug = set_urban_profile(urban_areas=urban_areas,
                           path_urban_areas=path_urban_areas,
                           urban_treshold=urban_treshold)

    centros = []
    for r in zip(ug.fid, ug.DN, ug.Size, ug.geometry):
        if r[2] == 'small':
            centros.append([r[0], str(r[3].centroid)])
        else:
            centros.append([r[0]])
            pass
    del r
    df = pd.DataFrame(centros, columns=['fid', 'centro'])
    del centros
    df = to_wkt(df=df, column='centro')
    ug = ug.merge(df, on='fid')
    del df

    result = []
    weighted_dist = None
    for u in ug.values:
        min_dist = getConfigValue('min_dist')
        name = None
        for p in pas.values:
            dist = p[3].distance(u[3])
            if dist < min_dist:
                min_dist = dist
                try:
                    weighted_dist = u[1]/(min_dist*math.sqrt(p[3].area))
                except ZeroDivisionError:
                    weighted_dist = u[1]
                name = p[1]
        result.append([u[0], u[1], u[2], u[3], name, min_dist, weighted_dist])
    del dist, min_dist, name, p, u

    cols = ug.keys().values.tolist()
    cols.append('distance')
    df = pd.DataFrame(result, columns=cols)
    del result

    if export:
        _, _, output_path = format_dataset_output(dataset=path_urban_areas, name='distances', ext='.xlsx')
        df.to_excel(output_path, index=False)
        return df
    else:
        return df


def get_profile(
        geodataframe_aoi: GeoDataFrame,
        aoi: AnyStr,
        habitat: AnyStr,
        method: AnyStr,
        population: AnyStr,
        anopheles: AnyStr,
        distances: bool = True,
        export: bool = False
) -> tuple[GeoDataFrame, AnyStr]:
    """
        Takes a Geodataframe as an input and iterate over every of its polygons, each as a new GeoDataFrame.

    For every of those polygons, this function does two types of things:
        - Crop/Intersect the data
        - Process the data

    There is four kind of data to be processed:
        - Land use
            - Read and count pixel values to see the diversity of these values
            - Read and associate the labels with the pixel values to get the land use categories and the proportionality
        - Population
            - Read every vectorized pixel and sums their value to get the total population.
            - Does the same thing but divide by the area to get the density.
        - Distances
            - Calculate the mean distance for every polygons of urban settlement to get the fragmentation index
        - Anopheles species (mosquitoes)
            - Count every point in the polygon to get the number of sites where anopheles (mosquitoes) where captured
            - Count the number of species found for each captur sites (sums the number of 'Y' in every rows)

    :param geodataframe_aoi: GeoDatFrame of the Areas of Interest to process.
    :type geodataframe_aoi: GeoDataFrame
    :param aoi: Path to the vector file of the Areas of Interest to process.
    :type aoi: AnyStr
    :param habitat: Raster file path for the land cover of Africa (ESA, 2016), degraded to 300m).
    :type habitat: AnyStr
    :param population: Vector file path for the population of Africa (WorldPop, 2020), Unconstrained, UN adjusted, 100m
    :type population: AnyStr
    :param anopheles: Vector file path of the Anopheles species present in countries in sub-Saharan Africa (Kyalo, 2019)
    :type anopheles: AnyStr
    :param distances: Boolean parameter to know wether or not the distances must be processed.
    :type distances: bool
    :param export: Same file as input but with additional columns corresponding to the results of the calculations
    :type export: bool
    :return: Same file as input but with additional columns corresponding to the results of the calculations
    :rtype: tuple[GeoDataFrame, AnyStr]
    """
    _, _, path_poly1 = format_dataset_output(dataset=aoi, name='tmp')
    _, _, path_poly2 = format_dataset_output(dataset=habitat, name='tmp')

    dist_treshold = getConfigValue('dist_treshold')
    gdf_result = GeoDataFrame()
    df_extract = GeoDataFrame()
    geodataframe_aoi.index.name = 'id'
    geodataframe_aoi.insert(geodataframe_aoi.shape[1] - 1, 'SUM_POP', 0)
    geodataframe_aoi.insert(geodataframe_aoi.shape[1] - 1, 'DENS_POP', 0)
    geodataframe_aoi.insert(geodataframe_aoi.shape[1] - 1, 'MEAN_DIST', 0)
    geodataframe_aoi.insert(geodataframe_aoi.shape[1] - 1, 'CATCH_SITE', 0)
    geodataframe_aoi.insert(geodataframe_aoi.shape[1] - 1, 'SPECIE_DIV', 0)
    geodataframe_aoi.insert(geodataframe_aoi.shape[1] - 1, 'HAB_DIV', 0)
    # At the end but before the geometry column because the types of habitats come after it.
    for i, p in iter_poly(shapefile=geodataframe_aoi):
        p.to_file(filename=path_poly1)
        path_occsol_cropped = raster_crop(dataset=habitat, shapefile=path_poly1)
        gdf_os_pol = polygonize(dataset=path_occsol_cropped)
        with alive_bar(total=(len(gdf_os_pol)*5)) as bar_process:
            for o, q in iter_poly(shapefile=gdf_os_pol):
                q.to_file(filename=path_poly2)
                path_occsol_cropped_hab = raster_crop(dataset=habitat, shapefile=path_poly2)
                df_extract = df_extract.append(geodataframe_aoi.loc[[i]], ignore_index=True)
                if habitat:  # Habitat diversity
                    bar_process.text('Habitats')  # Progress bar
                    dataset, ctr = get_pixel_count(dataset_path=path_occsol_cropped_hab, band=0)
                    df_extract.loc[o, 'HAB_DIV'] = len(ctr)
                    bar_process()  # Progress bar

                    bar_process.text('Land use')
                    data = []
                    for c in ctr:
                        category_area = round(ctr[c] * (dataset.res[0] * dataset.res[1]), 3)
                        raster_area = sum(ctr.values())
                        percentage = ((ctr[c] * 100) / raster_area)
                        data.append([c, ctr[c], category_area, percentage])

                    df_hab_div = pd.DataFrame(data, columns=['Category', 'Nbr of pixels', 'Surface (m2)', 'Proportion (%)'])

                    # TODO export style files from cropped raster so it can be read flawlessly here. Right now i have to
                    #  load it into qgis export it into a qml file by hand.
                    __dataset_name, _, __qml_path = format_dataset_output(dataset=path_occsol_cropped, ext='.qml')
                    __style = read_qml(__qml_path)
                    __val = None
                    for m, r in df_hab_div.iterrows():
                        for n in __style:
                            if r['Category'] == n[0]:
                                __val = n[1]
                        df_hab_div.loc[m, 'Label'] = __val
                    if method == 'append:':
                        df_hab_div = df_hab_div.pivot_table(columns='Label',
                                                            values='Proportion (%)',
                                                            aggfunc='sum')
                        df_hab_div.rename(index={'Proportion (%)': int(o)}, inplace=True)
                        df_extract.loc[o, df_hab_div.columns] = df_hab_div.loc[o, :].values
                    elif method == 'duplicate':
                        try:
                            df_extract.insert(df_extract.shape[1] - 1, 'HAB', 0)
                            df_extract.insert(df_extract.shape[1] - 1, 'HAB_PROP', 0)
                        except ValueError:
                            pass
                        df_extract.loc[o, 'HAB'] = df_hab_div.loc[0, 'Label']
                        df_extract.loc[o, 'HAB_PROP'] = round(df_hab_div.loc[0, 'Proportion (%)'], 3)
                    else:
                        pass
                    bar_process()  # Progress bar
                """    
                if population:  # Population and urban patches
                    bar_process.text('Population')  # Progress bar
                    gdf_pop_cropped = intersect(base=population, overlay=path_poly2, crs=3857)
                    print(int(gdf_pop_cropped['DN'].sum()), int(gdf_pop_cropped['DN'].sum()/p.area[0]))
                    df_extract.loc[o, 'SUM_POP'] = int(gdf_pop_cropped['DN'].sum())
                    df_extract.loc[o, 'DENS_POP'] = int(gdf_pop_cropped['DN'].sum() / p.area[0])
                    bar_process()  # Progress bar

                if distances:  # Distances and urban fragmentation
                    # No need to intersect it again
                    bar_process.text('Distances')  # Progress bar
                    # https://splot.readthedocs.io/en/stable/users/tutorials/weights.html#weights-from-other-python-objects
                    dbc = lps.weights.DistanceBand.from_dataframe(gdf_pop_cropped,
                                                                  threshold=dist_treshold,
                                                                  p=2,
                                                                  binary=False,
                                                                  build_sp=True,
                                                                  silent=True)
                    print(round(dbc.mean_neighbors, 4))
                    df_extract.loc[o, 'MEAN_DIST'] = round(dbc.mean_neighbors, 4)
                    bar_process()  # Progress bar

                if anopheles:  # Anopheles diversity and catching sites
                    bar_process.text('Anopheles')  # Progress bar
                    gdf_anopheles_cropped = intersect(base=anopheles, overlay=path_poly2, crs=3857)
                    gdf_anopheles_cropped['spnb'] = 0
                    gdf_anopheles_cropped['PA_dist'] = 0
                    gdf_anopheles_cropped['PA_buffer_dist'] = 0
                    for x in range(0, len(gdf_anopheles_cropped)):
                        gdf_anopheles_cropped.loc[x, 'spnb'] = gdf_anopheles_cropped.iloc[x].str.count('Y').sum()
                        gdf_anopheles_cropped.loc[x, 'PA_dist'] = 'PA_dist'
                        gdf_anopheles_cropped.loc[x, 'PA_buffer_dist'] = 'PA_buffer_dist'

                    print(int(len(gdf_anopheles_cropped)), gdf_anopheles_cropped['spnb'].max())
                    df_extract.loc[o, 'CATCH_SITE'] = int(len(gdf_anopheles_cropped))
                    df_extract.loc[o, 'SPECIE_DIV'] = gdf_anopheles_cropped['spnb'].max()
                    bar_process()  # Progress bar
                """

        gdf_result = gdf_result.append(df_extract, ignore_index=True)
        # TODO NBR colonne habitats != Colonnes habitats: deux derières colonnes pas insérées ?
        # TODO val 200 inconnue mais présente de manièrre normale = la légende ne la répertorie pas ?
        # Snow ice et Nodata ne sont pas insérés: merged avec d'autres colonnes ?

        print('[{}/{}]'.format(i+1, len(geodataframe_aoi)))

        # End

    if export:
        _, _, path_poly1 = format_dataset_output(dataset=aoi, name='profiles', ext='.xlsx')
        gdf_result.to_excel(path_poly1, index=False)
        return gdf_result, aoi
    else:
        return gdf_result, aoi
