import matplotlib.pyplot as plt
import numpy as np
from typing import List
from numpy.typing import NDArray


def calc_accuracy(data_ref, data_value) -> NDArray:
    data_ref_np = np.array(data_ref)
    data_sim_np = np.array(data_value)
    # calculate accuracy [%]
    delta = abs(data_sim_np-data_ref_np)
    return 100 - (delta/data_ref_np) * 100  # [%]


def make_boxplot(data, title: str, y_label: str, value_name: str):
    plt.figure(1)
    plt.boxplot(data, patch_artist=True, labels=[value_name])
    plt.title(title)
    plt.ylabel(y_label)
    plt.grid()
    plt.show()


def make_2boxplots(data1, data2, title: str, y_label: str, value_names: List[str]):
    plt.figure(1)
    plt.boxplot([data1, data2], patch_artist=True, labels=value_names)
    plt.title(title)
    plt.ylabel(y_label)
    plt.grid()
    plt.show()
