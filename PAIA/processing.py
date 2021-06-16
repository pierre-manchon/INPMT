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
from PAIA.utils.vector import merge_touching, to_wkt, iter_poly, intersect
from PAIA.utils.raster import raster_crop, get_pixel_count
from PAIA.utils.utils import format_dataset_output, getConfigValue, read_qml


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
    _, _, output_path = format_dataset_output(dataset=aoi, name='tmp')

    dist_treshold = getConfigValue('dist_treshold')

    geodataframe_aoi.index.name = 'id'
    geodataframe_aoi.insert(geodataframe_aoi.shape[1] - 1, 'SUM_POP', int)
    geodataframe_aoi.insert(geodataframe_aoi.shape[1] - 1, 'DENS_POP', int)
    geodataframe_aoi.insert(geodataframe_aoi.shape[1] - 1, 'MEAN_DIST', int)
    geodataframe_aoi.insert(geodataframe_aoi.shape[1] - 1, 'CATCH_SITE', int)
    geodataframe_aoi.insert(geodataframe_aoi.shape[1] - 1, 'SPECIE_DIV', int)
    geodataframe_aoi.insert(geodataframe_aoi.shape[1] - 1, 'HAB_DIV', int)
    # At the end but before the geometry column because the types of habitats come after it.

    with alive_bar(total=len(geodataframe_aoi)*3) as bar_process:
        # len(geodataframe_aoi*5 = Number of countries times the number of operations i need to do per countries
        for i, p in iter_poly(shapefile=geodataframe_aoi):
            p.to_file(filename=output_path)  # Retrieve the temporary file of the polygons.

            if habitat:  # Habitat diversity
                bar_process.text('Habitats')  # Progress bar
                path_occsol_cropped = raster_crop(dataset=habitat, shapefile=output_path)
                dataset, ctr = get_pixel_count(dataset_path=path_occsol_cropped, band=0)
                geodataframe_aoi.loc[i, 'HAB_DIV'] = len(ctr)
                bar_process()  # Progress bar

                bar_process.text('Land use')
                data = []
                for c in ctr:
                    category_area = round(ctr[c] * (dataset.res[0] * dataset.res[1]), 3)
                    raster_area = sum(ctr.values())
                    percentage = ((ctr[c] * 100) / raster_area)
                    data.append([c, ctr[c], category_area, percentage])

                df_habitat_diversity = pd.DataFrame(data,
                                                    columns=['Category', 'Nbr of pixels', 'Surface (m2)', 'Proportion (%)'])

                # TODO export style files from cropped raster so it can be read flawlessly here. Right now i have to
                #  load it into qgis export it into a qml file by hand.
                __dataset_name, _, __qml_path = format_dataset_output(dataset=path_occsol_cropped, ext='.qml')
                __style = read_qml(__qml_path)
                __val = None
                for m, r in df_habitat_diversity.iterrows():
                    for n in __style:
                        if r['Category'] == n[0]:
                            __val = n[1]
                    df_habitat_diversity.loc[m, 'Label'] = __val
                df_habitat_diversity = df_habitat_diversity.pivot_table(columns='Label',
                                                                        values='Proportion (%)',
                                                                        aggfunc='sum')
                df_habitat_diversity.rename(index={'Proportion (%)': int(i)}, inplace=True)
                geodataframe_aoi.loc[i, df_habitat_diversity.columns] = df_habitat_diversity.loc[i, :].values
                bar_process()  # Progress bar

            elif population:  # Population and urban patches
                bar_process.text('Population')  # Progress bar
                gdf_pop_cropped = intersect(base=population, overlay=output_path, crs=3857)
                geodataframe_aoi.loc[i, 'SUM_POP'] = int(gdf_pop_cropped['DN'].sum())
                geodataframe_aoi.loc[i, 'DENS_POP'] = int(gdf_pop_cropped['DN'].sum() / p.area[0])
                bar_process()  # Progress bar

            elif distances:  # Distances and urban fragmentation
                # No need to intersect it again
                bar_process.text('Distances')  # Progress bar
                # https://splot.readthedocs.io/en/stable/users/tutorials/weights.html#weights-from-other-python-objects
                dbc = lps.weights.DistanceBand.from_dataframe(gdf_pop_cropped,
                                                              threshold=dist_treshold,
                                                              p=2,
                                                              binary=False,
                                                              build_sp=True,
                                                              silent=True)

                geodataframe_aoi.loc[i, 'MEAN_DIST'] = round(dbc.mean_neighbors, 4)
                bar_process()  # Progress bar

            elif anopheles:  # Anopheles diversity and catching sites
                bar_process.text('Anopheles')  # Progress bar
                gdf_anopheles_cropped = intersect(base=anopheles, overlay=output_path, crs=3857)
                gdf_anopheles_cropped['spnb'] = np.nan
                gdf_anopheles_cropped['PA_dist'] = np.nan
                gdf_anopheles_cropped['PA_buffer_dist'] = np.nan
                for x in range(0, len(gdf_anopheles_cropped)):
                    gdf_anopheles_cropped.loc[x, 'spnb'] = gdf_anopheles_cropped.iloc[x].str.count('Y').sum()
                    gdf_anopheles_cropped.loc[x, 'PA_dist'] = 'PA_dist'
                    gdf_anopheles_cropped.loc[x, 'PA_buffer_dist'] = 'PA_buffer_dist'

                geodataframe_aoi.loc[i, 'CATCH_SITE'] = int(len(gdf_anopheles_cropped))
                geodataframe_aoi.loc[i, 'SPECIE_DIV'] = gdf_anopheles_cropped['spnb'].max()

            # TODO NBR colonne habitats != Colonnes habitats: deux derières colonnes pas insérées ?
            # Snow ice et Nodata ne sont pas insérés: merged avec d'autres colonnes ?

            print(' [{}/{}]'.format(i, len(geodataframe_aoi)))
            bar_process()  # Progress bar

            # End

    if export:
        _, _, output_path = format_dataset_output(dataset=aoi, name='profiles', ext='.xlsx')
        geodataframe_aoi.to_excel(output_path, index=False)
        return geodataframe_aoi, aoi
    else:
        return geodataframe_aoi, aoi
