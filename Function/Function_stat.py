import pandas as pd
from statsmodels.formula.api import ols
from statsmodels.stats.anova import anova_lm
from statsmodels.stats.multicomp import pairwise_tukeyhsd
import scipy.stats as stats
import scikit_posthocs as sp
import numpy as np


def prepare_data(data):
    # Calcul des moyennes pour le haut et le bas du corps
    upper_body_columns = data[['AvBrasD', 'MainD', 'AvBrasG', 'MainG']]
    data["upper_body"] = upper_body_columns.mean(axis=1)
    lower_body_columns = data[['JambeD', 'PiedD', 'JambeG', 'PiedG']]
    data["lower_body"] = lower_body_columns.mean(axis=1)

    # Création des groupes basés uniquement sur le Timing
    conditions = [
        (data['Timing'] == 'Takeoff'),
        (data['Timing'] == '75%'),
        (data['Timing'] == 'Landing')
    ]
    labels = ['Takeoff', '75%', 'Landing']

    data['Timing'] = np.select(conditions, labels, default='Other')

    data_subset = data[data['Timing'] != 'Other']
    return data_subset[['ID', 'upper_body', 'lower_body', 'Timing']]


def perform_anova_and_tukey(data, dependent_var, group_var):
    # Fit the ANOVA model
    model = ols(f'{dependent_var} ~ C({group_var})', data=data).fit()
    anova_results = anova_lm(model, typ=2)
    print(f"ANOVA Results:\n{anova_results}\n")

    # Perform Tukey HSD post-hoc test if ANOVA is significant
    if anova_results.loc['C(Timing)', 'PR(>F)'] < 0.05:
        tukey_results = pairwise_tukeyhsd(endog=data[dependent_var], groups=data[group_var], alpha=0.05)
        print(f"Tukey HSD Results:\n{tukey_results}")
    else:
        print("No significant differences found by ANOVA; no post hoc test performed.")


def perform_kruskal_and_dunn(data, dependent_var, group_var):
    # Group data for Kruskal-Wallis test
    groups = [group[dependent_var].values for name, group in data.groupby(group_var)]
    kruskal_stat, kruskal_p = stats.kruskal(*groups)
    print(f"Kruskal-Wallis Test Results (P-value: {kruskal_p:.4f})")

    index_columns = ['75%', 'Landing', 'Takeoff']
    fake_data = [
        [1, 1, 1],
        [1, 1, 1],
        [1, 1, 1]
    ]
    fake_data_df = pd.DataFrame(fake_data, index=index_columns, columns=index_columns)

    # Perform Dunn's post-hoc test if Kruskal-Wallis test is significant
    if kruskal_p < 0.05:
        posthoc_results = sp.posthoc_dunn(data, val_col=dependent_var, group_col=group_var, p_adjust='bonferroni')
        print("Post-hoc Dunn's Test Results:")
        print(posthoc_results)
        return posthoc_results
    else:
        print("No significant differences found by Kruskal-Wallis; no post hoc test performed.")
        return fake_data_df


def safe_interpolate(x, num_points):
    # Create an array to store interpolated values, initialized with NaN
    interpolated_values = np.full(num_points, np.nan)

    # Check if all elements are finite, ignore NaNs for interpolation
    finite_mask = np.isfinite(x)
    if finite_mask.any():  # Ensure there's at least one finite value to interpolate
        # Interpolate only finite values
        valid_x = x[finite_mask]
        valid_indices = np.linspace(0, 1, len(x))[finite_mask]

        # Perform interpolation over the range with finite values
        interpolated_valid_values = np.interp(np.linspace(0, 1, num_points), valid_indices, valid_x)

        # Round interpolated values to the nearest integer
        rounded_values = np.round(interpolated_valid_values).astype(int)

        # Place rounded interpolated values back in the full array
        interpolated_values = rounded_values

    return interpolated_values