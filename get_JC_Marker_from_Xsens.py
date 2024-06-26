import pickle
import matplotlib.pyplot as plt
import biorbd
import numpy as np
# import bioviz
import os
import scipy

from mpl_toolkits.mplot3d import Axes3D
from matplotlib.animation import FuncAnimation
from TrampolineAcrobaticVariability.Function.Function_build_model import (
    convert_marker_to_local_frame,
    calculer_rotation_et_angle,
)
from TrampolineAcrobaticVariability.Function.Function_Class_Basics import find_index, check_matrix_orthogonality

shoulder_include = False
parent_list_xsens_JC = [
    "Pelvis",  # 0
    "L5",  # delete
    "L3",  # delete
    "T12",  # delete
    "T8",  # delete
    "Neck",  # delete
    "Head",  # 1
    "ShoulderR",  # delete
    "UpperArmR",  # delete
    "LowerArmR",  # 2
    "HandR",  # 3
    "ShoulderL",  # delete
    "UpperArmL",  # delete
    "LowerArmL",  # 4
    "HandL",  # 5
    "UpperLegR",  # 6
    "LowerLegR",  # 7
    "FootR",  # 8
    "ToesR",  # delete
    "UpperLegL",  # 9
    "LowerLegL",  # 10
    "FootL",  # 11
    "ToesL",  # delete
]
home_path = "/home/lim/Documents/StageMathieu/DataTrampo/Xsens_pkl"
participants_name = [dossier for dossier in os.listdir(home_path) if os.path.isdir(os.path.join(home_path, dossier))]

total_length_member = []
for name in participants_name:
    print(f"{name} in process")
    participant_path = f"{home_path}/{name}/"
    acrobatie_type = [dossier for dossier in os.listdir(participant_path) if os.path.isdir(os.path.join(participant_path, dossier))]

    for acrobatie in acrobatie_type:
        acrobatie_path = f"{participant_path}{acrobatie}/"

        fichiers_pkl = []
        for root, dirs, files in os.walk(acrobatie_path):
            for file in files:
                if file.endswith(".pkl"):
                    full_path = os.path.join(root, file)
                    fichiers_pkl.append(full_path)

        for chemin_fichier_pkl in fichiers_pkl:
            folder_path = f"{participant_path}Pos_JC/{acrobatie}/"

            if not os.path.exists(folder_path):
                os.makedirs(folder_path)

            file_name, _ = os.path.splitext(os.path.basename(chemin_fichier_pkl))
            print(f"{file_name} is running")

            with open(chemin_fichier_pkl, "rb") as fichier_pkl:
                # Charger les données à partir du fichier ".pkl"
                eye_tracking_metrics = pickle.load(fichier_pkl)

            subject_expertise = eye_tracking_metrics["subject_expertise"]
            subject_name = eye_tracking_metrics["subject_name"]
            move_orientation = eye_tracking_metrics["move_orientation"]
            Xsens_orientation_per_move = eye_tracking_metrics["Xsens_orientation_per_move"]
            Xsens_position_rotated_per_move = eye_tracking_metrics["Xsens_position_rotated_per_move"]
            laterality = eye_tracking_metrics["laterality"]
            wall_index = eye_tracking_metrics["wall_index"]
            gaze_position_temporal_evolution_projected = eye_tracking_metrics["gaze_position_temporal_evolution_projected"]

            n_frames = Xsens_position_rotated_per_move.shape[0]
            Xsens_position = Xsens_position_rotated_per_move.reshape(n_frames, 23, 3).transpose(2, 1, 0)

            ##
            # fig = plt.figure()
            # ax = fig.add_subplot(111, projection='3d')
            # sc = ax.scatter([], [], [])
            # def init():
            #     sc._offsets3d = ([], [], [])
            #     return sc,
            # def update(frame):
            #     x = Xsens_position[0, :, frame]
            #     y = Xsens_position[1, :, frame]
            #     z = Xsens_position[2, :, frame]
            #     sc._offsets3d = (x, y, z)
            #     return sc,
            # ani = FuncAnimation(fig, update, frames=range(Xsens_position.shape[2]), init_func=init, blit=False)
            # plt.show()
            ##

            indices_a_supprimer = []
            if shoulder_include == True:
                elements_to_remove = ["L5", "L3", "T12", "T8", "Neck", "ShoulderR", "ShoulderL", "ToesR", "ToesL"]

            else:
                elements_to_remove = ["L5", "L3", "T12", "T8", "Neck", "ShoulderR", "UpperArmR",
                                      "ShoulderL", "UpperArmL", "ToesR", "ToesL"]

            for element in elements_to_remove:
                element_index = find_index(element, parent_list_xsens_JC)
                if element_index is not None:
                    indices_a_supprimer.append(element_index)

            indices_total = range(Xsens_position.shape[1])
            indices_a_conserver = [i for i in indices_total if i not in indices_a_supprimer]
            Xsens_positions_complet = Xsens_position[:, indices_a_conserver, :]
            parent_list_xsens_JC_complet = [jc for i, jc in enumerate(parent_list_xsens_JC) if i not in indices_a_supprimer]

            indices_reels_colonnes_a_supprimer = []
            for indice in indices_a_supprimer:
                indices_reels_colonnes_a_supprimer.extend(range(indice * 4, indice * 4 + 4))
            mask_colonnes = np.ones(Xsens_orientation_per_move.shape[1], dtype=bool)
            mask_colonnes[indices_reels_colonnes_a_supprimer] = False

            Xsens_orientation_per_move_complet = Xsens_orientation_per_move[:, mask_colonnes]

            n_markers = len(parent_list_xsens_JC_complet)

            Jc_in_pelvis_frame = np.ndarray((3, n_markers, n_frames))

            length_segment = np.ndarray((n_frames, 8))

            for i in range(n_frames):
                mid_hip_pos = (Xsens_positions_complet[:, find_index("UpperLegR", parent_list_xsens_JC_complet), i] +
                               Xsens_positions_complet[:, find_index("UpperLegL", parent_list_xsens_JC_complet), i]) / 2

                rot_mov_without_zrot = calculer_rotation_et_angle(find_index("Pelvis", parent_list_xsens_JC_complet),
                                                                  Xsens_orientation_per_move_complet[i, :])
                rot_mov = calculer_rotation_et_angle(find_index("Pelvis", parent_list_xsens_JC_complet),
                                                     Xsens_orientation_per_move_complet[i, :], move_orientation)
                check_matrix_orthogonality(rot_mov_without_zrot)
                check_matrix_orthogonality(rot_mov)

                length_segment[i, 0] = np.linalg.norm(
                    Xsens_position[:, find_index("UpperArmR", parent_list_xsens_JC), i] -
                    Xsens_position[:, find_index("LowerArmR", parent_list_xsens_JC), i])
                length_segment[i, 1] = (np.linalg.norm(
                    Xsens_position[:, find_index("LowerArmR", parent_list_xsens_JC), i] -
                    Xsens_position[:, find_index("HandR", parent_list_xsens_JC), i]))
                length_segment[i, 2] = (np.linalg.norm(
                        Xsens_position[:, find_index("UpperArmL", parent_list_xsens_JC), i] -
                        Xsens_position[:, find_index("LowerArmL", parent_list_xsens_JC), i]))
                length_segment[i, 3] = (np.linalg.norm(
                    Xsens_position[:, find_index("LowerArmL", parent_list_xsens_JC), i] -
                    Xsens_position[:, find_index("HandL", parent_list_xsens_JC), i]))
                length_segment[i, 4] = (np.linalg.norm(
                        Xsens_position[:, find_index("UpperLegR", parent_list_xsens_JC), i] -
                        Xsens_position[:, find_index("LowerLegR", parent_list_xsens_JC), i]))
                length_segment[i, 5] = (np.linalg.norm(
                        Xsens_position[:, find_index("LowerLegR", parent_list_xsens_JC), i] -
                        Xsens_position[:, find_index("FootR", parent_list_xsens_JC), i]))
                length_segment[i, 6] = (np.linalg.norm(
                    Xsens_position[:, find_index("UpperLegL", parent_list_xsens_JC), i] -
                    Xsens_position[:, find_index("LowerLegL", parent_list_xsens_JC), i]))
                length_segment[i, 7] = (np.linalg.norm(
                        Xsens_position[:, find_index("LowerLegL", parent_list_xsens_JC), i] -
                        Xsens_position[:, find_index("FootL", parent_list_xsens_JC), i]))

                for idx, jcname in enumerate(parent_list_xsens_JC_complet):

                    if idx == find_index("Pelvis", parent_list_xsens_JC_complet):
                        Rotation_pelvis = biorbd.Rotation(
                            rot_mov[0, 0],
                            rot_mov[0, 1],
                            rot_mov[0, 2],
                            rot_mov[1, 0],
                            rot_mov[1, 1],
                            rot_mov[1, 2],
                            rot_mov[2, 0],
                            rot_mov[2, 1],
                            rot_mov[2, 2],
                        )
                        Jc_in_pelvis_frame[:, idx, i] = biorbd.Rotation.toEulerAngles(
                            Rotation_pelvis, "xyz").to_array()
                        # Jc_in_pelvis_frame[:, idx, i] = mid_hip_pos
                    else:
                        P2_prime = convert_marker_to_local_frame(mid_hip_pos, rot_mov_without_zrot, Xsens_positions_complet[:, idx, i])
                        Jc_in_pelvis_frame[:, idx, i] = P2_prime

            Jc_in_pelvis_frame[:, 0:3, :] = np.unwrap(Jc_in_pelvis_frame[:, 0:3, :], axis=2)

            indices_to_swap = []
            elements_to_find = ["Head", "UpperArmR", "LowerArmR", "HandR", "UpperArmL", "LowerArmL",
                                    "HandL", "LowerLegR", "FootR", "LowerLegL", "FootL"]

            for element in elements_to_find:
                element_index = find_index(element, parent_list_xsens_JC_complet)
                if element_index is not None:
                    indices_to_swap.append(element_index)

            # Boucler sur les indices spécifiés de l'axe 1
            for idx in indices_to_swap:
                temp = np.copy(Jc_in_pelvis_frame[0, idx, :])

                # Échanger les valeurs entre les indices 1 et 2 de l'axe 0
                Jc_in_pelvis_frame[0, idx, :] = Jc_in_pelvis_frame[1, idx, :]
                Jc_in_pelvis_frame[1, idx, :] = temp
                temp_2 = np.copy(Jc_in_pelvis_frame[0, idx, :])
                Jc_in_pelvis_frame[0, idx, :] = -temp_2

            mean_length_segment = np.mean(length_segment, axis=0)

            # Add proximal length member to distal length member to get full length for each member
            indices_impairs = np.arange(1, len(mean_length_segment), 2)
            mean_length_segment[indices_impairs] += mean_length_segment[indices_impairs - 1]

            mat_data = {
                "Jc_in_pelvis_frame": Jc_in_pelvis_frame,
                "JC_order": parent_list_xsens_JC_complet,
                "laterality": laterality,
                "subject_expertise": subject_expertise,
                "length_segment": mean_length_segment,
                "wall_index": wall_index,
                "gaze_position_temporal_evolution_projected": gaze_position_temporal_evolution_projected,
            }
            folder_and_file_name_path = folder_path + f"{file_name}.mat"

            # Enregistrement dans un fichier .mat
            scipy.io.savemat(folder_and_file_name_path, mat_data)


            # colors = ['r', 'g', 'b']
            # n_rows = int(np.ceil(Jc_in_pelvis_frame.shape[1] / 4))
            # plt.figure(figsize=(20, 3 * n_rows))
            #
            # for idx, jcname in enumerate(parent_list_xsens_JC_complet):
            #     ax = plt.subplot(n_rows, 4, idx + 1)
            #     for j in range(Jc_in_pelvis_frame.shape[0]):
            #         ax.plot(Jc_in_pelvis_frame[j, idx, :], color=colors[j], label=f'Composante {["X", "Y", "Z"][j]}')
            #     ax.set_title(f'Graphique {jcname}')
            #     ax.set_xlabel('Frame')
            #     ax.set_ylabel('Valeur')
            #     if idx == 0:
            #         ax.legend()
            # plt.tight_layout()
            # plt.show()
            #
            # indices = [find_index("Pelvis", parent_list_xsens_JC_complet),
            #            find_index("UpperLegR", parent_list_xsens_JC_complet),
            #            find_index("UpperLegL", parent_list_xsens_JC_complet)]
            #
            # fig, axs = plt.subplots(len(indices) + 1, 1, figsize=(14, 12))
            # for j, idx in enumerate(indices):
            #     axs[j].plot(Xsens_positions_complet[0, idx, :], label='X - x')
            #     axs[j].plot(Xsens_positions_complet[1, idx, :], label='X - y')
            #     axs[j].plot(Xsens_positions_complet[2, idx, :], label='X - z')
            #     axs[j].set_title(f'Positions Xsens pour le marqueur {idx}')
            #     axs[j].legend()
            #     axs[j].set_xlabel('Frame')
            #     axs[j].set_ylabel('Position')
            #
            # axs[-1].plot(Jc_in_pelvis_frame[0, 0, :], label='Jc - x', linestyle='--')
            # axs[-1].plot(Jc_in_pelvis_frame[1, 0, :], label='Jc - y', linestyle='--')
            # axs[-1].plot(Jc_in_pelvis_frame[2, 0, :], label='Jc - z', linestyle='--')
            # axs[-1].set_title('Positions Jc_in_pelvis_frame pour le marqueur 0')
            # axs[-1].legend()
            # axs[-1].set_xlabel('Frame')
            # axs[-1].set_ylabel('Position')
            #
            # plt.tight_layout()
            # plt.show()
            #
            #
            # fig = plt.figure()
            # ax = fig.add_subplot(111, projection='3d')
            # sc = ax.scatter([], [], [])
            # def init():
            #     sc._offsets3d = ([], [], [])
            #     return sc,
            # def update(frame):
            #     x = Jc_in_pelvis_frame[0, 1:, frame]
            #     y = Jc_in_pelvis_frame[1, 1:, frame]
            #     z = Jc_in_pelvis_frame[2, 1:, frame]
            #     sc._offsets3d = (x, y, z)
            #     return sc,
            # ani = FuncAnimation(fig, update, frames=range(Xsens_position.shape[2]), init_func=init, blit=False)
            # plt.show()
