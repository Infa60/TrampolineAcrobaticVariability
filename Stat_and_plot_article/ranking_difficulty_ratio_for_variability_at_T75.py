import pandas as pd
from statsmodels.formula.api import ols
from statsmodels.stats.anova import anova_lm
import matplotlib.pyplot as plt
import seaborn as sns
import os
import numpy as np
from scipy.stats import linregress

home_path = "/home/lim/Documents/StageMathieu/Tab_result3/"


order = ['8-1o', '8-1<', '811<', '41', '41o', '8-3<', '42', '831<', '822', '43']
orderxlabel = ['8-1o', '8-1<', '811<', '41/', '41o', '8-3<', '42/', '831<', '822/', '43/']
orderxlabeltop = ['0.25', '0.5', '0.75', '1', '1.5']

ratio = [5, 5, 10, 10, 10, 15, 20, 20, 20, 30]
x_boxplot_centers = [4.3, 5.7, 8.6, 10, 11.4, 15, 18.6, 20, 21.4, 30]
x_boxplot_top = [5, 10, 15, 20, 30]

name = [
    'GuSe', 'JaSh', 'JeCa', 'AnBe', 'AnSt', 'SaBe', 'JoBu',
    'JaNo', 'SaMi', 'AlLe', 'MaBo', 'SoMe', 'JeCh', 'LiDu',
    'LeJa', 'ArMa', 'AlAd'
]

rotation_files = []

for root, dirs, files in os.walk(home_path):
    for file in files:
        if 'rotation' in file:
            full_path = os.path.join(root, file)
            rotation_files.append(full_path)

complete_data = pd.DataFrame(columns=order, index=name)

for file in rotation_files:
    data = pd.read_csv(file)
    mvt_name = file.split('/')[-1].replace('results_', '').replace('_rotation.csv', '')
    anova_rot_df = data.pivot_table(index=['ID'], columns='Timing', values='Std')
    for gymnast_name in data["ID"].unique():
        complete_data.loc[gymnast_name, mvt_name] = np.degrees(anova_rot_df.loc[gymnast_name, "75%"])

all_x_positions = []
all_values = []

for i, col in enumerate(order):
    all_x_positions.extend([ratio[i]] * complete_data[col].dropna().shape[0])
    all_values.extend(complete_data[col].dropna().values)

slope, intercept, r_value, p_value, std_err = linregress(all_x_positions, all_values)

x_reg_line = np.linspace(min(x_boxplot_centers), max(x_boxplot_centers), 100)
y_reg_line = slope * x_reg_line + intercept
print(f"*** All acrobatics regression equation : {slope} x + {intercept} ***")

fig, ax = plt.subplots(figsize=(10, 6))
sns.boxplot(data=complete_data[order], ax=ax, color="skyblue", positions=x_boxplot_centers)
sns.lineplot(x=x_reg_line, y=y_reg_line, ax=ax, color='gray', label='Regression Line', linewidth=1.5)

p_text = "p < 0.001" if p_value < 0.001 else f"p = {p_value:.3f}"
text_str = f'r = {r_value:.2f}\n{p_text}'
ax.text(0.02, 0.95, text_str, transform=ax.transAxes, fontsize=10, verticalalignment='top', bbox=dict(boxstyle='round', facecolor='white', alpha=0.5))

ax.set_xlabel('Acrobatics', labelpad=15)
ax.set_ylabel('Variability of pelvis rotations at T$_{75}$ (deg)')
ax.set_xticks(x_boxplot_centers)
ax.set_xticklabels(orderxlabel)
ax.set_ylim(0, 58)
ax.legend(loc='lower right')

secax = ax.secondary_xaxis('top')
secax.set_xticks(x_boxplot_top)
secax.set_xticklabels(orderxlabeltop)
secax.set_xlabel('Ratio twists somersaults', labelpad=15)

plt.subplots_adjust(top=0.907, bottom=0.098, left=0.056, right=0.995,)
plt.savefig("/home/lim/Documents/StageMathieu/meeting/linear_reg_all_acrobatics_with_ratio.png", dpi=1000)
plt.show()

