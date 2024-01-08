"""
File name:      DataPlot.py
Author:         Sebastian Seidel
Date:           2024.**.**
"""
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import DataConsts as dc
import DataAnalysis as da
from typing import List
from numpy.typing import NDArray


def calc_accuracy(data_ref, data_value) -> NDArray:
    data_ref_np = np.array(data_ref)
    data_sim_np = np.array(data_value)
    # calculate accuracy [%]
    delta = abs(data_sim_np - data_ref_np)
    return 100 - (delta / data_ref_np) * 100  # [%]


def make_boxplot(data: NDArray, title: str, y_label: str, value_name: str):
    plt.figure()
    plt.boxplot(data, patch_artist=True, labels=[value_name])
    plt.title(title)
    plt.ylabel(y_label)
    plt.grid()
    plt.show()


def make_2boxplots(data1: NDArray, data2: NDArray, title: str, y_label: str, value_names: List[str]):
    plt.figure()
    plt.boxplot([data1, data2], patch_artist=True, labels=value_names)
    plt.title(title)
    plt.ylabel(y_label)
    plt.grid()
    plt.show()


def make_hist(data: NDArray, title: str, y_label: str, x_label: str, num_bins: int):
    plt.figure()
    plt.hist(data, bins=num_bins)
    plt.title(title)
    plt.ylabel(y_label)
    plt.xlabel(x_label)
    plt.grid()
    plt.show()


def _get_data_smaller_as(data: NDArray, thershold) -> NDArray:
    bool_mask = da.get_index_filter_by_accuracy_thershold(data[:, 3], data[:, 4], thershold)
    return data[bool_mask]


def _get_data_bigger_as(data: NDArray, thershold) -> NDArray:
    bool_mask = np.invert(da.get_index_filter_by_accuracy_thershold(data[:, 3], data[:, 4], thershold))
    return data[bool_mask]


def show_details(filename: str, title: str) -> NDArray:
    print(f"\n--- {title} --- \n")
    df = pd.read_csv(filename, sep=";", decimal=",")
    np_data = df.to_numpy()

    print(f"Mittlere quad. Fehler (RMSE): {da.mean_sqrt_error(np_data[:, 3], np_data[:, 4]):.2f}% Bedeckungsgrad")
    print(f"Mittlerer Fehler (MAE): {da.mean_error(np_data[:, 3], np_data[:, 4]):.2f}% Bedeckungsgrad")
    print(f"Mittlere abs. Fehler (ME): {da.mean_absolute_error(np_data[:, 3], np_data[:, 4]):.2f}% Bedeckungsgrad")

    data_accuracy_under_15: NDArray = _get_data_smaller_as(np_data, 15)
    print(f"{len(data_accuracy_under_15) / len(np_data) * 100:.2f}% der Daten haben eine Genauigkeit von < 15%.")

    data_accuracy_over_85: NDArray = _get_data_bigger_as(np_data, 85)
    print(f"{len(data_accuracy_over_85) / len(np_data) * 100:.2f}% der Daten haben eine Genauigkeit von > 85%.")

    data_accuracy_over_95: NDArray = _get_data_bigger_as(np_data, 95)
    print(f"{len(data_accuracy_over_95) / len(np_data) * 100:.2f}% der Daten haben eine Genauigkeit von > 95%.")

    data_accuracy: NDArray = 100 - np.abs(np_data[:, 3] - np_data[:, 4])
    make_hist(data_accuracy, f"Genauigkeit (Anzahl Daten: {len(np_data)})", "Anzahl der Daten",
              "Genauigkeit [%]", 8)
    return data_accuracy


accuracy_d2 = show_details(dc.IMPORT_NAME_D2, "ICON-D2")
accuracy_eu = show_details(dc.IMPORT_NAME_EU, "ICON-EU")

make_2boxplots(accuracy_d2, accuracy_eu, "Vergleich Genauigkeit ICON-D2 und ICON-EU",
               "Genauigkeit [%]", ["ICON-D2", "ICON_EU"])
