"""
File name:      DataPlot.py
Author:         Sebastian Seidel
Date:           2024.**.**
"""
import os
import matplotlib.pyplot as plt
import pandas as pd
import DataAnalysis as da
from pandas import DataFrame
from Lib.IOConsts import *


def make_hist(df: DataFrame, title: str, y_label: str, x_label: str, num_bins: int):
    # plt.figure()
    df.hist(bins=num_bins, color='skyblue', edgecolor='black')
    plt.title(title)
    plt.ylabel(y_label)
    plt.xlabel(x_label)
    plt.grid(alpha=0.75)
    plt.show()


def make_compare_boxplot(col: str, df1: DataFrame, name1: str, df2: DataFrame, name2: str):
    combined_df = pd.DataFrame({name1: df1[col], name2: df2[col]})
    combined_df.dropna(inplace=True)
    combined_df.sort_values(by=name1, inplace=True)
    combined_df.sort_values(by=name2, inplace=True)
    combined_df.plot(kind="box")
    plt.title(f"Absoluter Fehler der Modelle\n({name1} und {name2}) zu den Wetterstationen")
    plt.ylabel("Fehler im Bedeckungsgrad [%]")
    plt.grid(alpha=0.75)
    plt.show()


def show_metrics(df: DataFrame, model: str):
    station_error = da.get_abs_error_each_station(df)
    me_mae_rmse = da.get_me_mae_rmse(df, "TCDC", "V_N")
    print(f"\n~~~{model}~~~\n")
    print(f"Mittlerer Fehler (ME): {me_mae_rmse[0]:.2f}% Bedeckungsgrad")
    print(f"Mittlere abs. Fehler (MAE): {me_mae_rmse[1]:.2f}% Bedeckungsgrad")
    print(f"Mittlere quad. Fehler (RMSE): {me_mae_rmse[2]:.2f}% Bedeckungsgrad")
    print(f"{len(da.filter_dataframe_by_value(df, COL_ABS_ERROR, 5, False)) / len(df) * 100:.2f}% "
          f"der Daten haben einen Fehler von < 5% Bedeckungsgrad.")
    print(f"{len(da.filter_dataframe_by_value(df, COL_ABS_ERROR, 15, False)) / len(df) * 100:.2f}% "
          f"der Daten haben einen Fehler von < 15% Bedeckungsgrad.")
    print(f"{len(da.filter_dataframe_by_value(df, COL_ABS_ERROR, 85)) / len(df) * 100:.2f}% "
          f"der Daten haben einen Fehler von > 85% Bedeckungsgrad.")
    make_hist(station_error[COL_MEAN_ABS_ERROR],
              f"Verteilung MAE von {model} zu Stationswerte\n(Anzahl Stationen: {len(station_error)})",
              f"Anzahl Stationen",
              f"MAE vom Bedeckungsgrad [%]",
              20)
    make_hist(df[COL_ABS_ERROR],
              f"Verteilung vom absoluten Fehler von {model} zu den Stationen\n(Anzahl Daten: {len(df)})",
              f"Anzahl Stationen",
              f"Absoluter Fehler vom Bedeckungsgrad [%]",
              20)
    unique_station_heights = pd.DataFrame(df[COL_STATION_HEIGHT].unique(), columns=[COL_STATION_HEIGHT])
    make_hist(unique_station_heights,
              f"Höhenverteilung der DWD-Stationen für\n{model}-Datensatz",
              "Anzahl Stationen [-]",
              "Stationshöhe [m]",
              30)


def load(filename: str) -> DataFrame:
    if not os.path.exists(filename):
        raise FileExistsError
    df = pd.read_csv(filename, sep=";", decimal=",")
    return df


# df_metric = da.get_error_metric(df)
df_d2 = load(CSV_NAME_ICON_D2)
da.calc_abs_error(df_d2, "TCDC", "V_N")
show_metrics(df_d2, "ICON-D2")

df_eu = load(CSV_NAME_ICON_EU)
da.calc_abs_error(df_eu, "TCDC", "V_N")
show_metrics(df_eu, "ICON-EU")

make_compare_boxplot(COL_ABS_ERROR, df_d2, "ICON-D2", df_eu, "ICON-EU")
print(f"Median vom absoluten Fehler zwischen ICON-D2 und DWD-Stationen: {df_d2[COL_ABS_ERROR].median():.2f}%")
print(f"Median vom absoluten Fehler zwischen ICON-EU und DWD-Stationen: {df_eu[COL_ABS_ERROR].median():.2f}%")
print(type(da.get_dwd_height_details(df_d2)))
print(da.get_dwd_height_details(df_eu))
