import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from TrampolineAcrobaticVariability.Function.Function_draw import plot_adjusted_fd
from Function.Function_Class_Basics import calculate_scores
from skfda import FDataGrid
from skfda.preprocessing.dim_reduction import FPCA
from skfda.representation.basis import (
    BSplineBasis,
)


# Charger les données à partir du fichier CSV
data_path = '/home/lim/Documents/StageMathieu/DataTrampo/Sarah/my_adjusted_data.csv'
data = pd.read_csv(data_path)
data = data.map(np.degrees)
std_dev_time = data.std(axis=1)

# Tracé de l'écart type en fonction du temps
plt.figure(figsize=(10, 6))
plt.plot(std_dev_time.index, std_dev_time.values)
plt.title('Écart type en fonction du Temps')
plt.xlabel('Temps')
plt.ylabel('Écart type')
plt.grid(True)

# Fréquence d'acquisition
freq_acquisition = 200  # Hz

# Calculer l'intervalle de temps entre les mesures
interval = 1 / freq_acquisition  # secondes

num_points = data.shape[0]
grid_points = np.arange(0, num_points) * interval

# Création de l'objet FDataGrid
fd = FDataGrid(data.values.T, grid_points=[grid_points])
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
# Calculer la moyenne des données fonctionnelles
mean_fd = fd.mean()

multiple = 10

# Calculer les courbes ajustées
adjusted_fd_positive = mean_fd + fpca.components_[0] * multiple
adjusted_fd_negative = mean_fd - fpca.components_[0] * multiple

adjusted_fd_positive_2 = mean_fd + fpca.components_[1] * multiple
adjusted_fd_negative_2 = mean_fd - fpca.components_[1] * multiple

adjusted_fd_positive_3 = mean_fd + fpca.components_[2] * multiple
adjusted_fd_negative_3 = mean_fd - fpca.components_[2] * multiple

adjusted_fd_positive_4 = mean_fd + fpca.components_[3] * multiple
adjusted_fd_negative_4 = mean_fd - fpca.components_[3] * multiple

adjusted_fd_positive_5 = mean_fd + fpca.components_[4] * multiple
adjusted_fd_negative_5 = mean_fd - fpca.components_[4] * multiple

fig, axs = plt.subplots(3, 2, figsize=(10, 12))

# Exemple d'appel de la fonction pour chaque composante principale et subplot
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


scores = calculate_scores(fd, fpca.components_.data_matrix, interval)


print(scores)
# Nombre de colonnes
n_colonnes = scores.shape[1]

# Valeurs en abscisse pour les deux groupes
x_values = np.array([1] * 5 + [0] * 5)

# Création des graphiques
for i in range(n_colonnes):
    plt.figure(figsize=(5, 3))  # Créer une nouvelle figure pour chaque colonne
    plt.scatter(x_values, scores[:, i])  # Tracer les points pour la colonne i
    plt.title(f'FPC {i+1}')  # Titre basé sur le numéro de la colonne
    plt.xlabel('Groupe')  # Axe des abscisses
    plt.ylabel('Valeur')  # Axe des ordonnées
    plt.xticks([0, 1], ['Groupe 0', 'Groupe 1'])  # Définir les étiquettes pour les valeurs en abscisse
    plt.show()  # Afficher le graphique
###########

