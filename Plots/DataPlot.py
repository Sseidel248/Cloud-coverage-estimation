"""
File name:      DataPlot.py
Author:         Sebastian Seidel
Date:           2024.**.**
"""
import os
import matplotlib.pyplot as plt
import pandas as pd
from Lib.Consts import DataExportConsts as dc
import DataAnalysis as da
from pandas import DataFrame


def make_hist(df: DataFrame, title: str, y_label: str, x_label: str, num_bins: int):
    plt.figure()
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
    me_mae_rmse = da.get_me_mae_rmse(df)
    print(f"\n~~~{model}~~~\n")
    print(f"Mittlere abs. Fehler (ME): {me_mae_rmse[0]:.2f}% Bedeckungsgrad")
    print(f"Mittlerer Fehler (MAE): {me_mae_rmse[1]:.2f}% Bedeckungsgrad")
    print(f"Mittlere quad. Fehler (RMSE): {me_mae_rmse[2]:.2f}% Bedeckungsgrad")
    print(f"{len(da.filter_dataframe_by_value(df, dc.ABS_ERROR, 5, False)) / len(df) * 100:.2f}% "
          f"der Daten haben einen Fehler von < 5% Bedeckungsgrad.")
    print(f"{len(da.filter_dataframe_by_value(df, dc.ABS_ERROR, 15, False)) / len(df) * 100:.2f}% "
          f"der Daten haben einen Fehler von < 15% Bedeckungsgrad.")
    print(f"{len(da.filter_dataframe_by_value(df, dc.ABS_ERROR, 85)) / len(df) * 100:.2f}% "
          f"der Daten haben einen Fehler von > 85% Bedeckungsgrad.")
    make_hist(station_error[dc.MEAN_ABS_ERROR],
              f"Verteilung MAE von {model} zu Stationswerte\n(Anzahl Stationen: {len(station_error)})",
              f"Anzahl Stationen",
              f"MAE vom Bedeckungsgrad [%]",
              20)
    make_hist(df[dc.ABS_ERROR],
              f"Verteilung vom absoluten Fehler von {model} zu den Stationen\n(Anzahl Daten: {len(df)})",
              f"Anzahl Stationen",
              f"Absoluter Fehler vom Bedeckungsgrad [%]",
              20)
    make_hist(df[dc.STATION_HEIGHT],
              f"Höhenverteilung der DWD-Stationen für\n{model}-Datensatz",
              "Stationshöhe [m]",
              "Prozentuale Verteilung [%]",
              30)


def load(filename: str) -> DataFrame:
    if not os.path.exists(filename):
        raise FileExistsError
    return pd.read_csv(filename, sep=";", decimal=",")


# df_metric = da.get_error_metric(df)
df_d2 = load(dc.CSV_NAME_ICON_D2)
da.calc_abs_error(df_d2)
show_metrics(df_d2, "ICON-D2")

df_eu = load(dc.CSV_NAME_ICON_EU)
da.calc_abs_error(df_eu)
show_metrics(df_eu, "ICON-EU")


make_compare_boxplot(dc.ABS_ERROR, df_d2, "ICON-D2", df_eu, "ICON-EU")
print(f"Median vom absoluten Fehler zwischen ICON-D2 und DWD-Stationen: {df_d2[dc.ABS_ERROR].median():.2f}%")
print(f"Median vom absoluten Fehler zwischen ICON-EU und DWD-Stationen: {df_eu[dc.ABS_ERROR].median():.2f}%")
print(type(da.get_dwd_height_details(df_d2)))
print(da.get_dwd_height_details(df_eu))







