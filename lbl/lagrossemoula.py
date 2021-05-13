import geopandas as gpd

v1 = 'v1.shp'
v2 = 'v2.shp'

g1 = gpd.GeoDataFrame.from_file(v1)
g2 = gpd.GeoDataFrame.from_file(v2)
data = []
for index, v1 in g1.iterrows():
    for index2, v2 in g2.iterrows():
       if v1['geometry'].intersects(v2['geometry']):
          data.append({'geometry': v1['geometry'].intersection(v2['geometry']), 'category_area':v1['geometry'].intersection(v2['geometry']).area, 'pop_inter': v1['pop'],
                      'pays_origine': v1['pays'], 'nom_zone_decoupees': v2['nom'], 'ours_zone_origine': v2['ours']})

df = gpd.GeoDataFrame(data,columns=['geometry', 'pop_inter', 'pays_origine','nom_zone_decoupees', 'ours_zone_origine'])
df.to_file('intersection.shp')
