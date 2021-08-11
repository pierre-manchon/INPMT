# -*-coding: utf8 -*
import pandas as pd

oney = r'H:/Cours/M2/Cours/HGADU03 - Mémoire/Projet Impact PN Anophèles/datasets/NDVI/NPs/' \
       r'NP_Africa_1y_2016-2017_MOD13A1-006-Statistics.csv'
fivey = r'H:/Cours/M2/Cours/HGADU03 - Mémoire/Projet Impact PN Anophèles/datasets/NDVI/NPs/' \
        r'NP_Africa_5y_2012-2017_MOD13A1-006-Statistics.csv'
teny = r'H:/Cours/M2/Cours/HGADU03 - Mémoire/Projet Impact PN Anophèles/datasets/NDVI/NPs/' \
       r'NP_Africa_10y_2007-2017_MOD13A1-006-Statistics.csv'
NDVI_stats = r'H:/Cours/M2/Cours/HGADU03 - Mémoire/Projet Impact PN Anophèles/datasets/NDVI/NPs/' \
             r'NDVI_NP_statistics.xlsx'

df_oney = pd.read_csv(oney)
df_fivey = pd.read_csv(fivey)
df_teny = pd.read_csv(teny)

mean_df_oney = df_oney.mean()
mean_df_fivey = df_fivey.mean()
mean_df_teny = df_teny.mean()

df_NDVI_stats = pd.DataFrame([mean_df_oney, mean_df_fivey, mean_df_teny])
df_NDVI_stats.to_excel(NDVI_stats)
