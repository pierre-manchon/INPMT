import os
import pandas as pd
import matplotlib.pyplot as plt
from .utils import __get_cfg_val, format_dataset_output

datasets = __get_cfg_val("datasets_storage_path")
export = os.path.join(datasets, 'result')
result = os.path.join(datasets, "results_urban_profiles_100.xlsx")
_, _, output_path = format_dataset_output(dataset=result, name='corr_plot', ext='.png')
df = pd.read_excel(result)

f = plt.figure(figsize=(19, 15))
plt.matshow(df.corr(), fignum=f.number)
plt.xticks(range(df.select_dtypes(['number']).shape[1]), df.select_dtypes(['number']).columns, fontsize=14, rotation=45)
plt.yticks(range(df.select_dtypes(['number']).shape[1]), df.select_dtypes(['number']).columns, fontsize=14)
cb = plt.colorbar()
cb.ax.tick_params(labelsize=14)
plt.title('Correlation Matrix', fontsize=16)
f.show()
f.savefig(output_path)
