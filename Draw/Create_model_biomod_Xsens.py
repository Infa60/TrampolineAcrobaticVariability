import biorbd
import numpy as np
import bioviz
import pickle
import matplotlib.pyplot as plt
from TrampolineAcrobaticVariability.Function.Function_build_model import get_all_matrice, convert_to_local_frame
from TrampolineAcrobaticVariability.Function.Function_Class_Basics import parent_list_xsens

chemin_fichier_pkl = "/home/lim/disk/Eye-tracking/Results_831/SaMi/4-/9884f602_0_0-52_451__4-__2__eyetracking_metrics.pkl"

home_path = "/DataTrampo/"
participant_name = "Sarah"
DoF = True

##

if DoF is True:
    modelDof = "FullDof"
else:
    modelDof = ""

chemin_fichier_original = f"{home_path}{participant_name}/{participant_name}ModelTest{modelDof}.s2mMod"
chemin_fichier_modifie = f"{home_path}{participant_name}/New{participant_name}ModelXsens{modelDof}.s2mMod"

with open(chemin_fichier_pkl, "rb") as fichier_pkl:
    # Charger les données à partir du fichier ".pkl"
    eye_tracking_metrics = pickle.load(fichier_pkl)

expertise = eye_tracking_metrics["subject_expertise"]
subject_name = eye_tracking_metrics["subject_name"]

Xsens_global_JCS_positions_full = eye_tracking_metrics["Xsens_global_JCS_positions"]
Xsens_global_JCS_orientations_full = eye_tracking_metrics["Xsens_global_JCS_orientations"]

Xsens_global_JCS_positions_reshape = Xsens_global_JCS_positions_full.reshape(23, 3)

# Selectionner  les articulations inutiles
indices_a_supprimer = [1, 2, 3, 5, 7, 11, 18, 22]

# Calculer les indices à conserver
indices_total = range(Xsens_global_JCS_positions_reshape.shape[0])
indices_a_conserver = [i for i in indices_total if i not in indices_a_supprimer]
Xsens_global_JCS_positions = Xsens_global_JCS_positions_reshape[indices_a_conserver, :]

indices_reels_colonnes_a_supprimer = []
for indice in indices_a_supprimer:
    indices_reels_colonnes_a_supprimer.extend(range(indice * 4, indice * 4 + 4))
mask_colonnes = np.ones(Xsens_global_JCS_orientations_full.shape[1], dtype=bool)
mask_colonnes[indices_reels_colonnes_a_supprimer] = False
Xsens_global_JCS_orientations_modifie = Xsens_global_JCS_orientations_full[:, mask_colonnes]


x = Xsens_global_JCS_positions_reshape[:, 0]
y = Xsens_global_JCS_positions_reshape[:, 1]
z = Xsens_global_JCS_positions_reshape[:, 2]
fig = plt.figure()
ax = fig.add_subplot(111, projection='3d')
ax.scatter(x, y, z)
for i, (px, py, pz) in enumerate(zip(x, y, z)):
    ax.text(px, py, pz, f'{i}', color='blue')
ax.set_xlabel('X Label')
ax.set_ylabel('Y Label')
ax.set_zlabel('Z Label')
plt.show()


nb_mat = Xsens_global_JCS_positions.shape[0]

RotMat_neutre = []

for i_segment in range(nb_mat):
    z_rotation = biorbd.Rotation.fromEulerAngles(np.array([-np.pi / 2]), "z").to_array()

    Quat_normalized_neutre = Xsens_global_JCS_orientations_modifie[0, i_segment * 4 : (i_segment + 1) * 4] / np.linalg.norm(
        Xsens_global_JCS_orientations_modifie[0, i_segment * 4 : (i_segment + 1) * 4]
    )
    Quat_neutre = biorbd.Quaternion(Quat_normalized_neutre[0], Quat_normalized_neutre[1], Quat_normalized_neutre[2], Quat_normalized_neutre[3])
    RotMat_neutre_segment = biorbd.Quaternion.toMatrix(Quat_neutre).to_array()
    RotMat_neutre_segment = z_rotation @ RotMat_neutre_segment
    RotMat_neutre.append(RotMat_neutre_segment)


matrix_in_parent_frame = []
joint_center_in_parent_frame = []
rot_trans_matrix = []

for index, (joint, parent_info) in enumerate(parent_list_xsens.items()):
    if parent_info is not None:  # Vérifie si parent_info n'est pas None
        parent_index, parent_name = parent_info
        P2_in_P1, R2_in_R1 = convert_to_local_frame(Xsens_global_JCS_positions[parent_index], RotMat_neutre[parent_index],
                                                    Xsens_global_JCS_positions[index], RotMat_neutre[index])
        matrix_in_parent_frame.append(R2_in_R1)
        joint_center_in_parent_frame.append(P2_in_P1)
        RT_mat = np.eye(4)
        RT_mat[:3, :3] = R2_in_R1
        RT_mat[:3, 3] = P2_in_P1
        rot_trans_matrix.append(RT_mat)

    else:
        matrix_in_parent_frame.append(RotMat_neutre[index])
        joint_center_in_parent_frame.append(Xsens_global_JCS_positions[index])
        RT_mat = np.eye(4)
        RT_mat[:3, :3] = RotMat_neutre[index]
        RT_mat[:3, 3] = [0.0, 0.0, 0.0]
        rot_trans_matrix.append(RT_mat)


model = biorbd.Model(chemin_fichier_original)
desired_order = [model.markerNames()[i].to_string() for i in range(model.nbMarkers())]

with open(chemin_fichier_original, 'r') as fichier:
    lignes = fichier.readlines()


with open(chemin_fichier_modifie, 'w') as fichier_modifie:
    a = 0
    i = 0
    while i < len(lignes):
        if "RT" in lignes[i]:
            fichier_modifie.write(lignes[i])  # Écrit la ligne RT
            i += 1  # Passe à la ligne suivante
            # Convertir chaque ligne de la matrice NumPy en chaîne avec des tabulations entre les éléments
            for ligne in rot_trans_matrix[a]:
                ligne_formattee = "\t".join(f"{val:.10f}" for val in ligne)
                fichier_modifie.write("\t\t\t" + ligne_formattee + "\n")
            i += 4  # Saute les 4 lignes de l'ancienne matrice
            a += 1
        else:
            fichier_modifie.write(lignes[i])
            i += 1

model = biorbd.Model(chemin_fichier_modifie)
b = bioviz.Viz(loaded_model=model)
b.exec()
