import numpy as np
import matplotlib.pyplot as plt
from TrampolineAcrobaticVariability.Function.Function_draw import plot_adjusted_fd
import os
import scipy
import pickle
from TrampolineAcrobaticVariability.Function.Function_Class_Basics import (get_q,
                                                                           normaliser_essai,
                                                                           calcul_stats,
                                                                           calculate_scores)
from skfda import FDataGrid
from skfda.preprocessing.dim_reduction import FPCA
from skfda.representation.basis import (BSplineBasis)
import matplotlib.patches as mpatches
angular_data_elite = []
angular_data_subelite = []

home = "/home/lim/Documents/XsensResults/"

names = os.listdir(home)
for name in enumerate(names):

    file_path = f"/home/lim/Documents/XsensResults/{name[1]}/43/"

    data_elite = []
    data_subelite = []
    elements = os.listdir(file_path)
    filtered_elements = [file for file in elements if file.endswith('eyetracking_metrics.pkl')]
    for files in enumerate(filtered_elements):
        file_path_complete = f"{file_path}{files[1]}"

        with open(file_path_complete, "rb") as fichier_pkl:
            eye_tracking_metrics = pickle.load(fichier_pkl)

        Xsens_orientation_per_move = eye_tracking_metrics["Xsens_orientation_per_move"]
        expertise = eye_tracking_metrics["subject_expertise"]
        q = get_q(Xsens_orientation_per_move)
        df = np.degrees(q[37])

        if expertise == "Elite":
            data_elite.append(df)
        else:
            data_subelite.append(df)

    if data_elite:
        angular_data_elite.append(data_elite)

    if data_subelite:
        angular_data_subelite.append(data_subelite)

nombre_points = 100
freq_acquisition = 200
interval = 1 / freq_acquisition

plt.figure(figsize=(10, 6))

# Tracer les données Elite après normalisation
for participant in angular_data_elite:
    for essai in participant:
        essai_normalise = normaliser_essai(essai, nombre_points)
        plt.plot(essai_normalise, color='blue', alpha=0.5)

# Tracer les données Sub-Elite après normalisation
for participant in angular_data_subelite:
    for essai in participant:
        essai_normalise = normaliser_essai(essai, nombre_points)
        plt.plot(essai_normalise, color='red', alpha=0.5)

plt.title('Comparaison des performances Elite vs Sub-Elite (Normalisées)')
plt.xlabel('Point interpolé')
plt.ylabel('Angles (°)')
elite_handle = mpatches.Patch(color='blue', label='Elite')
sub_elite_handle = mpatches.Patch(color='red', label='Sub-Elite')
plt.legend(handles=[elite_handle, sub_elite_handle], loc='best')


grid_points = np.arange(0, nombre_points) * interval

data_elite_normalisees = [normaliser_essai(essai, nombre_points) for participant in angular_data_elite for essai in participant]
data_subelite_normalisees = [normaliser_essai(essai, nombre_points) for participant in angular_data_subelite for essai in participant]

###
moyenne_elite, ecart_type_elite = calcul_stats(data_elite_normalisees)
moyenne_subelite, ecart_type_subelite = calcul_stats(data_subelite_normalisees)
temps = np.linspace(0, 1, nombre_points)  # Remplacez par vos vrais points temporels si nécessaire

plt.figure(figsize=(10, 6))

# Elite
plt.plot(temps, moyenne_elite, 'b-', label='Moyenne Elite')
plt.fill_between(temps, moyenne_elite-ecart_type_elite, moyenne_elite+ecart_type_elite, color='blue', alpha=0.2)

# Sub-Elite
plt.plot(temps, moyenne_subelite, 'r-', label='Moyenne Sub-Elite')
plt.fill_between(temps, moyenne_subelite-ecart_type_subelite, moyenne_subelite+ecart_type_subelite, color='red', alpha=0.2)

plt.title('Comparaison des performances Elite vs Sub-Elite (Normalisées)')
plt.xlabel('Point interpolé')
plt.ylabel('Angles (°)')
plt.legend(loc='best')

##


ids_elite = ['Elite' for _ in range(len(data_elite_normalisees))]
ids_subelite = ['Sub-Elite' for _ in range(len(data_subelite_normalisees))]

data_totale = np.vstack([data_elite_normalisees, data_subelite_normalisees])
ids_totales = np.array(ids_elite + ids_subelite)

# Créer l'objet FDataGrid
fd = FDataGrid(data_matrix=data_totale, grid_points=grid_points)

fd.plot()
plt.title('Données Originales')

# FPCA discretisée
fpca_discretized = FPCA(n_components=5)
fpca_discretized.fit(fd)
fpca_discretized.components_.plot()
plt.title('Composantes Principales - Données Discretisées')

# Conversion en base de B-Splines et tracé
basis_fd = fd.to_basis(BSplineBasis(n_basis=7))
basis_fd.plot()
plt.title('Données en Base de B-Splines')

# FPCA sur données en B-Splines
fpca = FPCA(n_components=5)
fpca.fit(basis_fd)
fpca.components_.plot()
plt.title('Composantes Principales - Base de B-Splines')


###
# Effectuer la FPCA sur vos données fd
fpca = FPCA(n_components=5)
fpca.fit(fd)
fd_transformed = fpca.transform(fd)
explained_variance_ratio = fpca.explained_variance_ratio_

mean_fd = fd.mean()

scores = calculate_scores(fd, fpca.components_.data_matrix, interval)
n_fpc = scores.shape[1]

std_scorefpc = []
for fpc in range(n_fpc):
    std_scorefpc.append(np.std(scores[fpc]))

adjusted_fd_positive = mean_fd + fpca.components_[0] * 2 * std_scorefpc[0]
adjusted_fd_negative = mean_fd - fpca.components_[0] * 2 * std_scorefpc[0]

adjusted_fd_positive_2 = mean_fd + fpca.components_[1] * 2 * std_scorefpc[1]
adjusted_fd_negative_2 = mean_fd - fpca.components_[1] * 2 * std_scorefpc[1]

adjusted_fd_positive_3 = mean_fd + fpca.components_[2] * 2 * std_scorefpc[2]
adjusted_fd_negative_3 = mean_fd - fpca.components_[2] * 2 * std_scorefpc[2]

adjusted_fd_positive_4 = mean_fd + fpca.components_[3] * 2 * std_scorefpc[3]
adjusted_fd_negative_4 = mean_fd - fpca.components_[3] * 2 * std_scorefpc[3]

adjusted_fd_positive_5 = mean_fd + fpca.components_[4] * 2 * std_scorefpc[4]
adjusted_fd_negative_5 = mean_fd - fpca.components_[4] * 2 * std_scorefpc[4]

fig, axs = plt.subplots(3, 2, figsize=(10, 12))

plot_adjusted_fd(axs[0, 0], mean_fd, adjusted_fd_positive, adjusted_fd_negative,
                 'FPC1', fd.grid_points[0], round(explained_variance_ratio[0], 2))
plot_adjusted_fd(axs[1, 0], mean_fd, adjusted_fd_positive_2, adjusted_fd_negative_2,
                 'FPC2', fd.grid_points[0],  round(explained_variance_ratio[1], 2))
plot_adjusted_fd(axs[2, 0], mean_fd, adjusted_fd_positive_3, adjusted_fd_negative_3,
                 'FPC3', fd.grid_points[0],  round(explained_variance_ratio[2], 2))
plot_adjusted_fd(axs[0, 1], mean_fd, adjusted_fd_positive_4, adjusted_fd_negative_4,
                 'FPC4', fd.grid_points[0],  round(explained_variance_ratio[3], 2))
plot_adjusted_fd(axs[1, 1], mean_fd, adjusted_fd_positive_5, adjusted_fd_negative_5,
                 'FPC5', fd.grid_points[0],  round(explained_variance_ratio[4], 2))

plt.tight_layout()


# Graph with dot
x_values = np.array([1 if id == 'Elite' else 0 for id in ids_totales])

plt.figure(figsize=(15, 6))
for i in range(n_fpc):
    # Ajout d'un subplot pour chaque FPC
    ax = plt.subplot(1, n_fpc, i + 1)
    scatter = ax.scatter(x_values, scores[:, i], c=x_values, cmap='viridis')
    ax.set_title(f'FPC {i + 1}')
    ax.set_xlabel('Groupe')
    ax.set_ylabel('Valeur')
    ax.set_xticks([0, 1])
    ax.set_xticklabels(['Sub-Elite', 'Elite'])
plt.tight_layout()

# Create BOXPLOT
scores_elite = []
scores_subelite = []
for i, score in enumerate(scores):
    if ids_totales[i] == 'Elite':
        scores_elite.append(score)
    else:
        scores_subelite.append(score)

scores_elite = np.array(scores_elite)
scores_subelite = np.array(scores_subelite)

plt.figure(figsize=(15, 6))
for i in range(n_fpc):
    # Ajout d'un subplot pour chaque FPC
    ax = plt.subplot(1, n_fpc, i + 1)
    data = [scores_subelite[:, i], scores_elite[:, i]]
    bplot = ax.boxplot(data, patch_artist=True, labels=['Sub-Elite', 'Elite'])
    colors = ['#FF9999', '#66B3FF']
    for patch, color in zip(bplot['boxes'], colors):
        patch.set_facecolor(color)
    for median in bplot['medians']:
        median.set_color('black')
    ax.set_title(f'FPC {i + 1}')
    ax.set_ylabel('Scores')
    ax.set_xticklabels(['Sub-Elite', 'Elite'])

plt.tight_layout()
plt.show()