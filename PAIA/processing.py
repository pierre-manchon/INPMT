# -*-coding: utf8 -*
import numpy as np
import pandas as pd
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
    for u in ug.values:
        min_dist = getConfigValue('min_dist')
        name = None
        for p in pas.values:
            dist = p[3].distance(u[3])
            if dist < min_dist:
                min_dist = dist
                name = p[1]
        result.append([u[0], u[1], u[2], u[3], name, min_dist])
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


def get_anopheles_data(geodataframe_aoi: GeoDataFrame, i: SupportsInt, anopheles: AnyStr, overlay: AnyStr):
    gdf_anopheles_cropped = intersect(base=anopheles, overlay=overlay, crs=3857)
    gdf_anopheles_cropped['spnb'] = np.nan
    gdf_anopheles_cropped['PA_dist'] = np.nan
    gdf_anopheles_cropped['PA_buffer_dist'] = np.nan
    for x in range(0, len(gdf_anopheles_cropped)):
        gdf_anopheles_cropped.loc[x, 'spnb'] = gdf_anopheles_cropped.iloc[x].str.count('Y').sum()
        gdf_anopheles_cropped.loc[x, 'PA_dist'] = 'PA_dist'
        gdf_anopheles_cropped.loc[x, 'PA_buffer_dist'] = 'PA_buffer_dist'

    geodataframe_aoi.loc[i, 'CATCHING_SITES_NUMBER'] = int(len(gdf_anopheles_cropped))
    geodataframe_aoi.loc[i, 'SPECIES_NUMBER'] = gdf_anopheles_cropped['spnb'].max()
    return geodataframe_aoi


def get_pas_profiles(
        geodataframe_aoi: GeoDataFrame,
        aoi: AnyStr,
        occsol: AnyStr,
        population: AnyStr,
        anopheles: AnyStr,
        export: bool = False
) -> tuple[GeoDataFrame, AnyStr]:
    """
    Crop the raster and the vector for every polygon of the pas layer
    Might want use a mask otherwise
    Then process and associate result to each polygon

    :param geodataframe_aoi: GeoDatFrame of the Areas of Interest to process.
    :type geodataframe_aoi: GeoDataFrame
    :param aoi: Path to the vector file of the Areas of Interest to process.
    :type aoi: AnyStr
    :param occsol: Raster file path for the land cover of Africa (ESA, 2016), degraded to 300m).
    :type occsol: AnyStr
    :param population: Vector file path for the population of Africa (WorldPop, 2020), Unconstrained, UN adjusted, 100m
    :type population: AnyStr
    :param anopheles: Vector file path of the Anopheles species present in countries in sub-Saharan Africa (Kyalo, 2019)
    :type anopheles: AnyStr
    :param export: Same file as input but with additional columns corresponding to the results of the calculations
    :type export: bool
    :return: Same file as input but with additional columns corresponding to the results of the calculations
    :rtype: tuple[GeoDataFrame, AnyStr]
    """
    _, _, output_path = format_dataset_output(dataset=aoi, name='tmp')

    geodataframe_aoi.insert(geodataframe_aoi.shape[1] - 1, 'SUM_POP', np.nan)
    geodataframe_aoi.insert(geodataframe_aoi.shape[1] - 1, 'DENS_POP', np.nan)
    geodataframe_aoi.insert(geodataframe_aoi.shape[1] - 1, 'MEAN_DIST', np.nan)
    geodataframe_aoi.insert(geodataframe_aoi.shape[1] - 1, 'CATCHING_SITES_NUMBER', np.nan)
    geodataframe_aoi.insert(geodataframe_aoi.shape[1] - 1, 'SPECIES_NUMBER', np.nan)
    geodataframe_aoi.insert(geodataframe_aoi.shape[1] - 1, 'HABITAT_DIVERSITY', np.nan)
    # At the end but before the geometry column because the types of habitats come after it.

    with alive_bar(total=len(geodataframe_aoi)*3) as bar_process:
        # len(geodataframe_aoi*5 = Number of countries times the number of operations i need to do per countries
        for i, p in iter_poly(shapefile=geodataframe_aoi):
            # Retrieve the temporary file of the polygons.
            p.to_file(filename=output_path)

            # Habitat diversity
            bar_process.text('Habitats')  # Progress bar
            path_occsol_cropped = raster_crop(dataset=occsol, shapefile=output_path)
            dataset, ctr = get_pixel_count(dataset_path=path_occsol_cropped, band=0)
            geodataframe_aoi.loc[i, 'HABITAT_DIVERSITY'] = len(ctr)
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

            # TODO export style files from cropped raster so it can be read flawlessly here. Right now i have to load
            #  it into qgis export it into a qml file by hand.
            __dataset_name, _, __qml_path = format_dataset_output(dataset=path_occsol_cropped, ext='.qml')
            __style = read_qml(__qml_path)
            __val = None
            for i, row in df_habitat_diversity.iterrows():
                for j in __style:
                    if row['Category'] == j[0]:
                        __val = j[1]
                df_habitat_diversity.loc[i, 'Label'] = __val
            df_habitat_diversity = df_habitat_diversity.pivot_table(columns='Label',
                                                                    values='Proportion (%)',
                                                                    aggfunc='sum').reset_index(drop=True)
            df_habitat_diversity.reindex([i])
            print(df_habitat_diversity.head())
            geodataframe_aoi = geodataframe_aoi.append(df_habitat_diversity)
            bar_process()  # Progress bar
            """
            # Population and urban patches
            bar_process.text('Population')  # Progress bar
            gdf_pop_cropped = intersect(base=population, overlay=output_path, crs=3857)
            geodataframe_aoi.loc[i, 'SUM_POP'] = int(gdf_pop_cropped['DN'].sum())
            geodataframe_aoi.loc[i, 'DENS_POP'] = int(gdf_pop_cropped['DN'].sum() / p.area[0])
            bar_process()  # Progress bar
            # Distances and urban fragmentation
            # No need to intersect it again
            bar.text('Distances')  # Progress bar
            df_dist_global = []
            for o, q in iter_poly(shapefile=gdf_pop_cropped):
                df_dist = []
                for l, s in iter_poly(shapefile=gdf_pop_cropped):
                    df_dist.append(q.distance(s)[0])
                df_dist_global.append(mean(df_dist_global))
            # geodataframe_aoi.loc[i, 'MEAN_DIST'] = round(df_dist_global['dist'].mean(), 4)
            # geodataframe_aoi.loc[i, 'MEAN_DIST'] = round(gdf_pop_cropped['dist'].mean(), 4)
            bar()  # Progress bar
                        """
            # Anopheles diversity and catching sites
            bar_process.text('Anopheles')  # Progress bar
            geodataframe_aoi = get_anopheles_data(geodataframe_aoi, i, anopheles, output_path)
            bar_process()  # Progress bar

            # End

    if export:
        _, _, output_path = format_dataset_output(dataset=aoi, name='profiles', ext='.xlsx')
        geodataframe_aoi.to_excel(output_path, index=False)
        return geodataframe_aoi, aoi
    else:
        return geodataframe_aoi, aoi
