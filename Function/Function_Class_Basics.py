import scipy.io
import pandas as pd
import numpy as np
import biorbd
from .Function_draw import column_names
from scipy.integrate import simpson
from scipy.interpolate import interp1d


class OrderMatData:
    def __init__(self, dataframe):
        self.dataframe = dataframe
        # Mapping des indices aux suffixes attendus
        self.index_suffix_map = {0: "X", 1: "Y", 2: "Z"}

    def __getitem__(self, key):
        if isinstance(key, list):
            # Initialiser une liste pour stocker tous les noms de colonnes correspondants
            matching_columns = []
            for prefix in key:
                matching_columns += [
                    col for col in self.dataframe.columns if col.startswith(prefix)
                ]
            if not matching_columns:
                raise KeyError(f"Variables {key} not found.")
        else:
            # Traiter key comme une chaîne de caractères unique
            matching_columns = [
                col for col in self.dataframe.columns if col.startswith(key)
            ]
            if not matching_columns:
                raise KeyError(f"Variable {key} not found.")

        return self.dataframe[matching_columns]

    def get_column_names(self):
        return self.dataframe.columns.tolist()

    def get_column_by_index(self, key, index):
        # Vérifie si l'index est valide
        if index not in self.index_suffix_map:
            raise KeyError(f"Invalid index {index}.")

        # Nettoie la clé en supprimant les espaces de début et de fin, et les espaces multiples
        cleaned_key = " ".join(key.strip().split())

        expected_suffix = self.index_suffix_map[index]
        column_name = f"{cleaned_key}_{expected_suffix}"

        if column_name not in self.dataframe.columns:
            # Essayez de gérer les espaces supplémentaires dans les noms de colonnes du DataFrame
            matching_columns = [col for col in self.dataframe.columns if
                                col.replace(" ", "").startswith(cleaned_key.replace(" ", "")) and col.endswith(
                                    expected_suffix)]
            if matching_columns:
                # Si des colonnes correspondantes sont trouvées, utilisez la première correspondance
                return self.dataframe[matching_columns[0]]
            else:
                raise KeyError(f"Column {column_name} does not exist.")

        return self.dataframe[column_name]

    def to_numpy_array(self):
        return self.dataframe.to_numpy()


def load_and_interpolate(file, interval, num_points=100):
    """
    Load and interpol the data from a MATLAB file(.mat).

    Args:
        file (str): Path to the .mat file to load.
        interval (tuple): A tuple of two elements specifying the interval of data to extract.
        num_points (int): Number of points for interpolation of data.

    Returns:
        OrderMatData: An instance of the OrderMatData class containing interpolate data.
    """
    # Load data with the DoF
    data = scipy.io.loadmat(file)
    if "Q2" in data:
        df = pd.DataFrame(data["Q2"]).T
    else:
        df = pd.DataFrame(data["Q_ready_to_use"]).T

    # df.columns = column_names
    Euler_Sequence = data["Euler_Sequence"]

    column_names = []
    for segment, sequence in Euler_Sequence:
        segment = segment.strip()
        for axis in sequence.strip():
            column_names.append(f"{segment}_{axis.upper()}")

    # Select data in specify interval
    df_selected = df.iloc[interval[0] : interval[1]]

    # Interpolate each column to have a uniform number of points
    df_interpolated = df_selected.apply(
        lambda x: np.interp(np.linspace(0, 1, num_points), np.linspace(0, 1, len(x)), x)
    )

    df_interpolated.columns = column_names
    my_data = OrderMatData(df_interpolated)
    return my_data


def load_and_interpolate_for_point(file_path, num_points=100, include_expertise_laterality_length=False):
    data_loaded = scipy.io.loadmat(file_path)
    JC = data_loaded["Jc_in_pelvis_frame"]
    Order_JC = data_loaded["JC_order"]

    Xsens_position = pd.DataFrame((JC.transpose(1, 0, 2).reshape(-1, JC.shape[2])).T)
    duration = len(Xsens_position)/60

    Xsens_position = Xsens_position.apply(
        lambda x: np.interp(np.linspace(0, 1, num_points), np.linspace(0, 1, len(x)), x)
    )

    complete_order = []
    for joint_center in Order_JC:
        complete_order.append(f"{joint_center.strip()}_X")
        complete_order.append(f"{joint_center.strip()}_Y")
        complete_order.append(f"{joint_center.strip()}_Z")

    DataFrame_with_colname = pd.DataFrame(Xsens_position)
    DataFrame_with_colname.columns = complete_order

    if include_expertise_laterality_length:
        subject_expertise = data_loaded["subject_expertise"]
        laterality = data_loaded["laterality"]
        length_segment = data_loaded["length_segment"]
        wall_index = data_loaded["wall_index"]
        gaze_position_temporal_evolution_projected = data_loaded["gaze_position_temporal_evolution_projected"]
        return DataFrame_with_colname, subject_expertise, laterality, length_segment, wall_index, gaze_position_temporal_evolution_projected, duration
    else:
        return DataFrame_with_colname


def calculate_mean_std(data_instances, member, axis):
    """
    Calculates the mean and std for a given member and an axes on all data instances
    """
    data_arrays = [
        instance.get_column_by_index(member, axis) for instance in data_instances
    ]
    Mean_Data = np.mean(data_arrays, axis=0)
    Std_Dev_Data = np.std(data_arrays, axis=0)
    return Mean_Data, Std_Dev_Data


def calcul_stats(data):
    # Convertir en array 3D pour faciliter les calculs (participants, essais, temps)
    data_array = np.array(data)
    # Moyenne et écart-type sur les essais pour chaque participant et degré de liberté
    moyenne = np.mean(data_array, axis=0)  # Moyenne sur les participants et les essais
    ecart_type = np.std(data_array, axis=0)  # Écart-type sur les participants et les essais
    return moyenne, ecart_type


def get_q(Xsens_orientation_per_move):
    """
    This function returns de generalized coordinates in the sequence XYZ (biorbd) from the quaternion of the orientation
    of the Xsens segments.
    The translation is left empty as it has to be computed otherwise.
    I am not sure if I would use this for kinematics analysis, but for visualisation it is not that bad.
    """

    parent_idx_list = {
        "Pelvis": None,  # 0
        "L5": [0, "Pelvis"],  # 1
        "L3": [1, "L5"],  # 2
        "T12": [2, "L3"],  # 3
        "T8": [3, "T12"],  # 4
        "Neck": [4, "T8"],  # 5
        "Head": [5, "Neck"],  # 6
        "ShoulderR": [4, "T8"],  # 7
        "UpperArmR": [7, "ShoulderR"],  # 8
        "LowerArmR": [8, "UpperArmR"],  # 9
        "HandR": [9, "LowerArmR"],  # 10
        "ShoulderL": [4, "T8"],  # 11
        "UpperArmL": [11, "ShoulderR"],  # 12
        "LowerArmL": [12, "UpperArmR"],  # 13
        "HandL": [13, "LowerArmR"],  # 14
        "UpperLegR": [0, "Pelvis"],  # 15
        "LowerLegR": [15, "UpperLegR"],  # 16
        "FootR": [16, "LowerLegR"],  # 17
        "ToesR": [17, "FootR"],  # 18
        "UpperLegL": [0, "Pelvis"],  # 19
        "LowerLegL": [19, "UpperLegL"],  # 20
        "FootL": [20, "LowerLegL"],  # 21
        "ToesL": [21, "FootL"],  # 22
    }

    nb_frames = Xsens_orientation_per_move.shape[0]
    Q = np.zeros((23 * 3, nb_frames))
    rotation_matrices = np.zeros((23, nb_frames, 3, 3))
    for i_segment, key in enumerate(parent_idx_list):
        for i_frame in range(nb_frames):
            Quat_normalized = Xsens_orientation_per_move[
                i_frame, i_segment * 4 : (i_segment + 1) * 4
            ] / np.linalg.norm(
                Xsens_orientation_per_move[i_frame, i_segment * 4 : (i_segment + 1) * 4]
            )
            Quat = biorbd.Quaternion(
                Quat_normalized[0],
                Quat_normalized[1],
                Quat_normalized[2],
                Quat_normalized[3],
            )

            RotMat_current = biorbd.Quaternion.toMatrix(Quat).to_array()
            z_rotation = biorbd.Rotation.fromEulerAngles(
                np.array([-np.pi / 2]), "z"
            ).to_array()
            RotMat_current = z_rotation @ RotMat_current

            if parent_idx_list[key] is None:
                RotMat = np.eye(3)
            else:
                RotMat = rotation_matrices[parent_idx_list[key][0], i_frame, :, :]

            RotMat_between = np.linalg.inv(RotMat) @ RotMat_current
            RotMat_between = biorbd.Rotation(
                RotMat_between[0, 0],
                RotMat_between[0, 1],
                RotMat_between[0, 2],
                RotMat_between[1, 0],
                RotMat_between[1, 1],
                RotMat_between[1, 2],
                RotMat_between[2, 0],
                RotMat_between[2, 1],
                RotMat_between[2, 2],
            )
            Q[
                i_segment * 3 : (i_segment + 1) * 3, i_frame
            ] = biorbd.Rotation.toEulerAngles(RotMat_between, "xyz").to_array()

            rotation_matrices[i_segment, i_frame, :, :] = RotMat_current
    return Q


def recons_kalman(n_frames, num_markers, markers_xsens, model, initial_guess):
    markersOverFrames = []
    for i in range(n_frames):
        node_segment = []
        for j in range(num_markers):
            node_segment.append(biorbd.NodeSegment(markers_xsens[:, j, i].T))
        markersOverFrames.append(node_segment)

    freq = 200
    params = biorbd.KalmanParam(freq)
    kalman = biorbd.KalmanReconsMarkers(model, params)
    kalman.setInitState(initial_guess[0], initial_guess[1], initial_guess[2])

    Q = biorbd.GeneralizedCoordinates(model)
    Qdot = biorbd.GeneralizedVelocity(model)
    Qddot = biorbd.GeneralizedAcceleration(model)
    q_recons = np.ndarray((model.nbQ(), len(markersOverFrames)))
    qdot_recons = np.ndarray((model.nbQ(), len(markersOverFrames)))
    for i, targetMarkers in enumerate(markersOverFrames):
        kalman.reconstructFrame(model, targetMarkers, Q, Qdot, Qddot)
        q_recons[:, i] = Q.to_array()
        qdot_recons[:, i] = Qdot.to_array()
    return q_recons, qdot_recons


def find_index(column_name, column_list):
    if column_name in column_list:
        return column_list.index(column_name)
    else:
        return None


def calculate_rmsd(markers, pos_recons):
    # Vérifier que les formes des tableaux sont identiques
    assert (
        markers.shape == pos_recons.shape
    ), "Les tableaux doivent avoir la même forme."

    n_frames = markers.shape[2]
    rmsd_per_frame = np.zeros(n_frames)

    for i in range(n_frames):
        # Calculer la différence entre les ensembles de marqueurs pour le cadre i
        diff = markers[:, :, i] - pos_recons[:, :, i]
        # Calculer la norme au carré de la différence pour chaque marqueur
        squared_diff = np.nansum(diff**2, axis=0)
        # Calculer la moyenne des différences au carré
        mean_squared_diff = np.mean(squared_diff)
        # Calculer la racine carrée de la moyenne des différences au carré pour obtenir la RMSD
        rmsd_per_frame[i] = np.sqrt(mean_squared_diff)

    return rmsd_per_frame


def normalise_vecteurs(vecteurs):
    normes = np.linalg.norm(vecteurs, axis=1)[:, np.newaxis]
    vecteurs_normalises = vecteurs / normes
    return vecteurs_normalises


parent_list_marker = {
    "Pelvis": None,  # 0
    "Thorax": [0, "Pelvis"],  # 1
    "Tete": [1, "Thorax"],  # 2
    "BrasD": [1, "Thorax"],  # 3
    "ABrasD": [3, "BrasD"],  # 4
    "MainD": [4, "ABrasD"],  # 5
    "BrasG": [1, "Thorax"],  # 6
    "ABrasG": [6, "BrasG"],  # 7
    "MainG": [7, "ABrasG"],  # 8
    "CuisseD": [0, "Pelvis"],  # 9
    "JambeD": [9, "CuisseD"],  # 10
    "PiedD": [10, "JambeD"],  # 11
    "CuisseG": [0, "Pelvis"],  # 12
    "JambeG": [12, "CuisseG"],  # 13
    "PiedG": [13, "JambeG"],  # 14
}


parent_list_xsens = {
    "Pelvis": None,  # 0
    # "L5": [0, "Pelvis"],  # delete
    # "L3": [1, "L5"],  # delete
    # "T12": [2, "L3"],  # delete
    "T8": [0, "Pelvis"],  # 1
    # "Neck": [4, "T8"],  # delete
    "Head": [1, "T8"],  # 2
    # "ShoulderR": [4, "T8"],  # delete
    "UpperArmR": [1, "T8"],  # 3
    "LowerArmR": [3, "UpperArmR"],  # 4
    "HandR": [4, "LowerArmR"],  # 5
    # "ShoulderL": [4, "T8"],  # delete
    "UpperArmL": [1, "T8"],  # 6
    "LowerArmL": [6, "UpperArmR"],  # 7
    "HandL": [7, "LowerArmR"],  # 8
    "UpperLegR": [0, "Pelvis"],  # 9
    "LowerLegR": [9, "UpperLegR"],  # 10
    "FootR": [10, "LowerLegR"],  # 11
    # "ToesR": [17, "FootR"],  # delete
    "UpperLegL": [0, "Pelvis"],  # 12
    "LowerLegL": [12, "UpperLegL"],  # 13
    "FootL": [13, "LowerLegL"],  # 14
    # "ToesL": [21, "FootL"],  # delete
}


def trouver_index_parent(nom_parent):
    # Créer une liste des clés de parent_list pour obtenir les index
    keys_list = list(parent_list.keys())
    # Trouver l'index du nom du parent dans cette liste
    index_parent = keys_list.index(nom_parent) if nom_parent in keys_list else None
    return index_parent


def calculate_scores(fd, fpca_components, dx):
    # Nombre d'essais, nombre de points par essai, nombre de FPC
    n_essais, n_points, _ = fd.data_matrix.shape
    n_fpc = fpca_components.shape[0]

    # Initialiser un tableau pour stocker les scores
    scores = np.zeros((n_essais, n_fpc))

    # Itérer sur chaque essai
    for i in range(n_essais):
        essai_values = fd.data_matrix[i, :, 0]  # Extraire les valeurs pour l'essai courant

        # Itérer sur chaque FPC
        for j in range(n_fpc):
            fpc_values = fpca_components[j, :, 0]  # Extraire les valeurs pour la FPC courante

            # Calculer le produit et intégrer pour obtenir le score
            produit = essai_values * fpc_values
            score = simpson(produit, dx=dx)

            scores[i, j] = score  # Stocker le score calculé

    return scores


def normaliser_essai(essai, nombre_points=100):
    # Créer un vecteur linéaire de points basé sur la longueur originale de l'essai
    x_original = np.linspace(0, 1, num=len(essai))
    # Créer un vecteur linéaire de points pour la longueur cible
    x_nouveau = np.linspace(0, 1, num=nombre_points)

    # Interpolation linéaire
    fonction_interpolation = interp1d(x_original, essai, kind='linear')
    essai_normalise = fonction_interpolation(x_nouveau)

    return essai_normalise


def check_matrix_orthogonality(matrix, i_segment="segment", matrix_name="Matrix"):
    if matrix.ndim == 3:  # Si ensemble de matrices
        for i in range(matrix.shape[2]):
            single_matrix = matrix[:, :, i]
            is_transpose_inverse = np.allclose(single_matrix.T, np.linalg.inv(single_matrix))
            is_determinant_one = np.isclose(np.linalg.det(single_matrix), 1)
            if not (is_transpose_inverse and is_determinant_one):
                print(
                    f"Erreur : {matrix_name} {i} pour le segment {i_segment} n'est pas orthogonale ou son déterminant n'est pas 1.")
                return False
    else:  # Si une seule matrice
        is_transpose_inverse = np.allclose(matrix.T, np.linalg.inv(matrix))
        is_determinant_one = np.isclose(np.linalg.det(matrix), 1)
        if not (is_transpose_inverse and is_determinant_one):
            print(
                f"Erreur : {matrix_name} pour le segment {i_segment} n'est pas orthogonale ou son déterminant n'est pas 1.")
            return False

    return True


def extract_identifier(filename):
    import re
    match = re.search(r'results_(\d+[^_]*)(?=_rotation)', filename)
    return match.group(1) if match else ''