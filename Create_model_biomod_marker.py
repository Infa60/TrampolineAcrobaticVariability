import biorbd
import numpy as np
import bioviz
import pandas as pd
import matplotlib.pyplot as plt
from TrampolineAcrobaticVariability.Function.Function_build_model import get_all_matrice, convert_to_local_frame, average_rotation_matrix
from TrampolineAcrobaticVariability.Function.Function_Class_Basics import parent_list_marker

home_path = "/home/lim/Documents/StageMathieu/DataTrampo/"
csv_path = f"{home_path}Labelling_trampo.csv"
DoF = False
is_y_up = False


##
interval_name_tab = pd.read_csv(csv_path, sep=';', usecols=['Participant', 'Analyse', 'Essai', 'Debut', 'Fin', 'Durée'])
interval_name_tab = interval_name_tab[interval_name_tab["Analyse"] == 'O']
participant_names = interval_name_tab['Participant'].unique()

if DoF is True:
    modelDof = "FullDof"
else:
    modelDof = ""

for participant_name in participant_names:

    model_kalman = f"{home_path}{participant_name}/{participant_name}.s2mMod"

    model = biorbd.Model(model_kalman)
    # Chemin du dossier contenant les fichiers .c3d
    file_path_relax = f"{home_path}{participant_name}/Score/"

    chemin_fichier_original = f"{home_path}{participant_name}/{participant_name}ModelTest{modelDof}.s2mMod"
    chemin_fichier_modifie = f"{home_path}{participant_name}/New{participant_name}Model{modelDof}.s2mMod"

    relax_intervals = [
        (file_path_relax + "Relax.c3d", (0, 50)),
    ]

    joint_center_mov = []
    rotate_matrice_mov = []

    joint_center_relax = []
    rotate_matrice_relax = []

    pos_marker_relax = []

    file_path_relax, interval_relax = relax_intervals[0]
    rot_mat, articular_joint_center, pos_marker_relax = get_all_matrice(file_path_relax, interval_relax, model, is_y_up)

    nb_mat = rot_mat.shape[0]
    relax_matrix = np.zeros((nb_mat, 3, 3))
    for i in range(nb_mat):
        matrices = rot_mat[i]
        relax_matrix[i] = average_rotation_matrix(matrices)

    relax_joint_center = np.mean(articular_joint_center, axis=1)

    matrix_in_parent_frame = []
    joint_center_in_parent_frame = []
    rot_trans_matrix = []

    for index, (joint, parent_info) in enumerate(parent_list_marker.items()):
        if parent_info is not None:  # Vérifie si parent_info n'est pas None
            parent_index, parent_name = parent_info
            P2_in_P1, R2_in_R1 = convert_to_local_frame(relax_joint_center[parent_index], relax_matrix[parent_index],
                                                        relax_joint_center[index], relax_matrix[index])
            matrix_in_parent_frame.append(R2_in_R1)
            joint_center_in_parent_frame.append(P2_in_P1)
            RT_mat = np.eye(4)
            RT_mat[:3, :3] = R2_in_R1
            RT_mat[:3, 3] = P2_in_P1
            rot_trans_matrix.append(RT_mat)

        else:
            matrix_in_parent_frame.append(relax_matrix[index])
            joint_center_in_parent_frame.append(relax_joint_center[index])
            RT_mat = np.eye(4)
            RT_mat[:3, :3] = relax_matrix[index]
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

    #
    # informations_marqueurs = []
    # nouvelles_lignes = []  # Liste pour stocker les nouvelles lignes avec les positions mises à jour
    # # Parcourir les lignes du fichier pour extraire les informations
    # i = 0  # Index pour parcourir les lignes
    # while i < len(lignes):
    #     if lignes[i].strip().startswith("marker"):  # Vérifie si la ligne commence par "marker"
    #         nouvelles_lignes.append(lignes[i])
    #         nouvelles_lignes.append(lignes[i+1])
    #         nom_marqueur = lignes[i].split()[1]  # Extrait le nom du marqueur
    #         nom_parent = lignes[i+1].split()[1]  # Extrait le nom du parent à la ligne suivante
    #         id_parent = trouver_index_parent(nom_parent)
    #         mat_parent_marker = relax_matrix[id_parent]
    #         pos_parent_marker = relax_joint_center[id_parent]
    #         index_marker = find_index(nom_marqueur, desired_order)
    #         marker_global_pos = pos_marker_relax[0][:, index_marker, :]
    #         mean_marker_global_pos = np.mean(marker_global_pos, axis=1)
    #
    #         marker_local_pos = convert_marker_to_local_frame(pos_parent_marker, mat_parent_marker, mean_marker_global_pos)
    #
    #         pos_str = "\t\t" + "position" + "\t\t" + "\t".join(f"{coord:.6f}" for coord in marker_local_pos) + "\n"
    #         print(pos_str)
    #
    #         # Ajoute la nouvelle position à la liste des nouvelles lignes
    #         nouvelles_lignes.append(pos_str)
    #
    #         # Incrémente i pour passer les lignes déjà traitées, en supposant que 'position' est la ligne i+2
    #         i += 3
    #     else:
    #         # Ajoute les lignes non relatives aux markers directement à nouvelles_lignes
    #         nouvelles_lignes.append(lignes[i])
    #         i += 1
    #
    #
    # with open(chemin_fichier_modifie, 'w') as fichier_modifie:
    #     fichier_modifie.writelines(nouvelles_lignes)

    model = biorbd.Model(chemin_fichier_modifie)
    b = bioviz.Viz(loaded_model=model)
    b.exec()

    # model = biorbd.Model(model_kalman)
    # b = bioviz.Viz(loaded_model=model)
    # b.exec()
