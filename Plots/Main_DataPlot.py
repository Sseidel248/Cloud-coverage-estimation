"""
File name:      Main_DataPlot.py
Author:         Sebastian Seidel
Date:           2024.**.**
"""
import os
import matplotlib.pyplot as plt
import matplotlib.patches as patches

import cartopy.crs as ccrs
import cartopy.feature as cfeature
import numpy as np
import pandas as pd
from matplotlib import pyplot
from matplotlib.axes import Axes
from matplotlib.collections import PathCollection

from Lib import DataAnalysis as da
from pandas import DataFrame
from Lib.IOConsts import *
from matplotlib.colors import LinearSegmentedColormap

MOVE_TO: str = "E:\\TUB_Cloud\\03_Master_Studium\\06_Masterarbeit\\Bilder"


def _set_fonts(scale: float = 1):
    plt.rcParams["font.family"] = "calibri"
    plt.rcParams["font.size"] = 12 * scale
    plt.rcParams["axes.titlesize"] = 12 * scale
    plt.rcParams["axes.labelsize"] = 12 * scale


def _show_and_export(a_plt: pyplot, show: bool, exportname: str):
    if exportname != "":
        _, ext = os.path.split(exportname)
        if ext == ".png":
            a_plt.savefig(os.path.join(f".\\", exportname), dpi=900)
        else:
            a_plt.savefig(os.path.join(f".\\", exportname))
    if show:
        a_plt.show()
    else:
        a_plt.close()


def _add_geographic(ax: Axes):
    ax.add_feature(cfeature.COASTLINE)
    ax.add_feature(cfeature.BORDERS, linestyle=":")
    ax.add_feature(cfeature.OCEAN)
    ax.add_feature(cfeature.LAKES, alpha=0.5)
    ax.add_feature(cfeature.RIVERS)
    gl = ax.gridlines(draw_labels=True, linewidth=1, color="gray", alpha=0.5, linestyle="--")
    gl.top_labels = False
    gl.right_labels = False


def _make_subplot_cloud_coverage(ax: Axes,
                                 data_model: DataFrame,
                                 data_dwd: DataFrame,
                                 colors: LinearSegmentedColormap) -> PathCollection:
    _add_geographic(ax)
    sc = ax.scatter(data_model[COL_LON], data_model[COL_LAT],
                    c=data_model[CLOUD_COVER],
                    vmin=0,
                    vmax=100,
                    cmap=colors,
                    marker="s",
                    alpha=1,
                    transform=ccrs.PlateCarree())
    ax.scatter(data_dwd[COL_LON], data_dwd[COL_LAT],
               color="red",
               s=50,
               marker="x",
               alpha=1,
               transform=ccrs.PlateCarree())
    return sc


def make_hist(df: DataFrame,
              title: str,
              y_label: str,
              x_label: str,
              num_bins: int,
              show: bool = True,
              exportname: str = ""):
    _set_fonts()
    df.hist(bins=num_bins, color="skyblue", edgecolor="black")
    plt.title(title, fontweight="bold")
    plt.ylabel(y_label)
    plt.xlabel(x_label)
    plt.grid(alpha=0.75)
    _show_and_export(plt, show, exportname)


def make_compare_violinplt(col: str,
                           df1: DataFrame,
                           name1: str,
                           df2: DataFrame,
                           name2: str,
                           show: bool = True,
                           exportname: str = ""):
    _set_fonts()
    combined_df = pd.DataFrame({name1: df1[col], name2: df2[col]})
    combined_df.dropna(inplace=True)
    combined_df.sort_values(by=name1, inplace=True)
    combined_df.sort_values(by=name2, inplace=True)
    plt.violinplot(combined_df.values, showmedians=True)
    plt.title(f"Verteilung vom MAE Modelle\n({name1} und {name2}) zu den Wetterstationen")
    plt.ylabel("MAE Bedeckungsgrad [%]")
    plt.xlabel("Modelle")
    plt.xticks(ticks=range(1, len(combined_df.columns) + 1), labels=combined_df.columns)
    plt.grid(alpha=0.75)
    _show_and_export(plt, show, exportname)


def show_metrics(df: DataFrame, model: str, show: bool = True):
    da.calc_abs_error(df, "TCDC", "V_N")
    stations_info = da.get_abs_error_each_station(df)
    me_mae_rmse = da.get_me_mae_rmse(df, "TCDC", "V_N")

    print(f"\n~~~{model}~~~\n")
    print(f"Mittlerer Fehler (ME): {me_mae_rmse[0]:.2f}% Bedeckungsgrad")
    print(f"Mittlere abs. Fehler (MAE): {me_mae_rmse[1]:.2f}% Bedeckungsgrad")
    print(f"Mittlere quad. Fehler (RMSE): {me_mae_rmse[2]:.2f}% Bedeckungsgrad")
    print(f"{len(da.filter_dataframe_by_value(df, COL_ABS_ERROR, 5, False)) / len(df) * 100:.2f}% "
          f"der Daten haben einen Fehler von < 5% Bedeckungsgrad.")
    print(f"{len(da.filter_dataframe_by_value(df, COL_ABS_ERROR, 12.5, False)) / len(df) * 100:.2f}% "
          f"der Daten haben einen Fehler von < 12,5% Bedeckungsgrad.")
    print(f"{len(da.filter_dataframe_by_value(df, COL_ABS_ERROR, 85)) / len(df) * 100:.2f}% "
          f"der Daten haben einen Fehler von > 85% Bedeckungsgrad.")

    make_hist(stations_info[COL_MEAN_ABS_ERROR],
              f"Verteilung des MAE von {model} zu den DWD-Stationen\n(Anzahl DWD-Stationen: {len(stations_info)})",
              f"Anzahl DWD-Stationen",
              f"MAE vom Bedeckungsgrad [%]",
              20,
              show,
              f"Verteilung_MAE_{model}_DWD_Stationen.svg")
    make_hist(df[COL_ABS_ERROR],
              f"Verteilung des absoluten Fehlers von {model} zu den DWD-Stationen\n(Anzahl Daten: {len(df)})",
              f"Anzahl Stationen",
              f"Absoluter Fehler vom Bedeckungsgrad [%]",
              20,
              show,
              f"MAE_{model}_DWD_Stationen.svg")
    # unique_station_heights = pd.DataFrame(df[COL_STATION_HEIGHT].unique(), columns=[COL_STATION_HEIGHT])
    # make_hist(unique_station_heights,
    #           f"Höhenverteilung der DWD-Stationen für\n{model}-Datensatz",
    #           "Anzahl Stationen [-]",
    #           "Stationshöhe [m]",
    #           30,
    #           show,
    #           f"Höhenverteilung_DWD_Stationen_{model}_Datensatz.svg")


def compare_fcst_error(df: DataFrame,
                       model: str,
                       show: bool = True,
                       exportname: str = ""):
    df_0 = df[df["Fcst_Minutes"] == 0].reset_index()
    df_60 = df[df["Fcst_Minutes"] == 60].reset_index()
    df_120 = df[df["Fcst_Minutes"] == 120].reset_index()
    combined_df = pd.DataFrame({"0 min.": df_0["Absolute_Error"],
                                "60 min.": df_60["Absolute_Error"],
                                "120 min.": df_120["Absolute_Error"]})
    combined_df.dropna(inplace=True)
    _set_fonts()
    plt.violinplot(combined_df.values, showmedians=True)
    plt.title(f"Verteilung des MAE nach Prognosezeiten vom {model}", fontweight="bold")
    plt.ylabel("MAE Bedeckungsgrad [%]")
    plt.xlabel("Vorhersagezeit")
    plt.xticks(ticks=range(1, len(combined_df.columns) + 1), labels=combined_df.columns)
    plt.grid(alpha=0.75)

    for i, col in enumerate(combined_df.columns):
        median_val = combined_df[col].median()
        plt.text(i + 1, median_val, f'{median_val:.2f}', color='black', ha='left', va='bottom')
    _show_and_export(plt, show, exportname)


def make_scatterplot_dwd_location(df: DataFrame,
                                  show: bool = True,
                                  exportname: str = ""):
    df_data = df.groupby(COL_STATION_ID).agg({
        COL_LAT: "first",  # Breitengrad der Station
        COL_LON: "first"  # Längengrad der Station
    }).reset_index()

    fig = plt.figure()
    _set_fonts()
    ax = fig.add_subplot(1, 1, 1, projection=ccrs.PlateCarree())
    ax.set_extent([df_data[COL_LON].min() - 1, df_data[COL_LON].max() + 1,
                   df_data[COL_LAT].min() - 1, df_data[COL_LAT].max() + 1],
                  crs=ccrs.PlateCarree())
    # Füge natürliche Erdeigenschaften hinzu
    _add_geographic(ax)
    sc = ax.scatter(df_data[COL_LON], df_data[COL_LAT],
                    s=35,
                    alpha=0.80,
                    edgecolor="black",
                    transform=ccrs.PlateCarree())
    sc.set_label("DWD-Station")
    ax.legend()
    plt.title("Geografische Verteilung der DWD-Stationen zum\nMessen des Bewölkungsgrades", fontweight="bold")
    plt.tight_layout()
    _show_and_export(plt, show, exportname)


def make_scatterplots_cloud_coverage(model_data_icon_d2_area_1: str,
                                     model_data_icon_eu_area_1: str,
                                     dwd_data_area_1: str,
                                     model_data_icon_d2_area_2: str,
                                     model_data_icon_eu_area_2: str,
                                     dwd_data_area_2: str,
                                     show: bool = True,
                                     exportname: str = ""):
    data_icon_d2_area_1 = load(model_data_icon_d2_area_1)
    data_icon_eu_area_1 = load(model_data_icon_eu_area_1)
    dwd_locs_area_1 = load(dwd_data_area_1)

    data_icon_d2_area_2 = load(model_data_icon_d2_area_2)
    data_icon_eu_area_2 = load(model_data_icon_eu_area_2)
    dwd_locs_area_2 = load(dwd_data_area_2)

    _set_fonts(1.7)
    date = data_icon_d2_area_1[COL_DATE].iloc[0]
    colors = ["#4169E1", "#6495ED", "#6495ED", "#87CEFA", "#87CEFA", "#B0E2FF", "#B0E2FF", "#F0F0F0", "#F0F0F0",
              "#D3D3D3", "#D3D3D3", "#A9A9A9", "#A9A9A9", "#808080", "#808080", "#696969"]

    cloud_cmap = LinearSegmentedColormap.from_list("cloud_coverage", colors, N=len(colors))
    fig, axs = plt.subplots(2, 2,
                            figsize=(10, 10),
                            subplot_kw={'projection': ccrs.PlateCarree()},
                            constrained_layout=True)
    axs[0, 0].set_title(MODEL_ICON_D2)
    axs[0, 1].set_title(MODEL_ICON_EU)
    _make_subplot_cloud_coverage(axs[0, 0], data_icon_d2_area_1, dwd_locs_area_1, cloud_cmap)
    _make_subplot_cloud_coverage(axs[1, 0], data_icon_d2_area_2, dwd_locs_area_2, cloud_cmap)
    _make_subplot_cloud_coverage(axs[0, 1], data_icon_eu_area_1, dwd_locs_area_1, cloud_cmap)
    sc = _make_subplot_cloud_coverage(axs[1, 1], data_icon_eu_area_2, dwd_locs_area_2, cloud_cmap)
    # Zugriff auf das zweite Artist-Objekt welches die DWD Markierungen zeichnet
    fig.legend([axs[1, 1].collections[1]], ["DWD-Station"], loc="center", bbox_to_anchor=(0.5, 0.45))
    cbar = fig.colorbar(sc, ax=[axs[0, 1], axs[1, 1]])
    cbar.set_label("Bewölkungsgrad [%]")
    cbar.set_ticks([0, 12.5, 25, 37.5, 50, 62.5, 75, 87.5, 100])
    plt.suptitle(f"Bewölkungsgrade der Modelle\n Datum: {date}", fontweight="bold")
    # Bild als png das svg word langsam macht
    _show_and_export(plt, show, exportname)


def make_germany_dwd_cloud_stations(df_data: DataFrame,
                                    show: bool = True,
                                    exportname: str = ""):
    stations = df_data[[COL_STATION_ID, COL_LON, COL_LAT]].drop_duplicates()
    fig = plt.figure()
    _set_fonts()
    ax = fig.add_subplot(1, 1, 1, projection=ccrs.PlateCarree())
    ax.set_extent([stations[COL_LON].min() - 1, stations[COL_LON].max() + 1,
                   stations[COL_LAT].min() - 1, stations[COL_LAT].max() + 1],
                  crs=ccrs.PlateCarree())
    _add_geographic(ax)
    sc = ax.scatter(stations[COL_LON], stations[COL_LAT],
                    s=35,
                    alpha=0.75,
                    edgecolor="black",
                    transform=ccrs.PlateCarree())
    # 47.5, 49.5, 7.5, 9.5
    area_1_coords = np.array([(7.5, 47.5), (9.5, 47.5), (9.5, 49.5), (7.5, 49.5)])
    area_1 = patches.Polygon(area_1_coords, closed=True, edgecolor='red', fill=False)
    ax.add_patch(area_1)
    # 52.5, 54.5, 12.0, 14.0
    area_2_coords = np.array([(12.0, 52.5), (14.0, 52.5), (14.0, 54.5), (12.0, 54.5)])
    area_2 = patches.Polygon(area_2_coords, closed=True, edgecolor='red', fill=False)
    ax.add_patch(area_2)
    plt.title(f"Betrachtete Bereiche von Deutschland für den \nVergleich {MODEL_ICON_D2} und {MODEL_ICON_EU}",
              fontweight="bold")
    plt.tight_layout()
    sc.set_label("DWD-Station")
    ax.legend()
    _show_and_export(plt, show, exportname)


def load(filename: str) -> DataFrame:
    if not os.path.exists(filename):
        raise FileExistsError
    df = pd.read_csv(filename, sep=";", decimal=",")
    return df


# Initialisation
show_plot = False
override_existing_plot_export = False

# Loading CSV-Files
df_d2 = load(CSV_NAME_ICON_D2)
df_eu = load(CSV_NAME_ICON_EU)

# Show all used DWD-Locations
make_scatterplot_dwd_location(df_d2, show_plot, "Verwendete_DWD-Stationen.svg")
print(f"Anzahl verwendeter DWD-Stationen in ICON-D2: {len(df_d2[COL_STATION_HEIGHT].unique())}")
print(f"Anzahl verwendeter DWD-Stationen in ICON-EU: {len(df_eu[COL_STATION_HEIGHT].unique())}")

# Calculate Errors (RMSE, MAE, ME) and show it as text and as diagramm
show_metrics(df_d2, MODEL_ICON_D2, show_plot)
show_metrics(df_eu, MODEL_ICON_EU, show_plot)

# Show Errors between Forecasts
compare_fcst_error(df_d2, MODEL_ICON_D2, show_plot, "Fehler_zwischen_den_Vorhersagezeitpunkten_vom_ICON_D2.svg")
compare_fcst_error(df_eu, MODEL_ICON_EU, show_plot, "Fehler_zwischen_den_Vorhersagezeitpunkten_vom_ICON_EU.svg")

# # Show Weather example plot
make_scatterplots_cloud_coverage(f".\\Area_I_ICON-D2.csv",
                                 f".\\Area_I_ICON-EU.csv",
                                 f".\\DWD-Stations_in_Area_I_ICON-D2.csv",
                                 f".\\Area_II_ICON-D2.csv",
                                 f".\\Area_II_ICON-EU.csv",
                                 f".\\DWD-Stations_in_Area_II_ICON-D2.csv",
                                 show_plot,
                                 f".\\Cloud_Coverage_Compare_ICON-D2_ICON-EU.png")

make_germany_dwd_cloud_stations(df_d2, show_plot, f".\\DWD_Station_Cloud_Coverage.svg")

#
# make_compare_violinplt(COL_ABS_ERROR, df_d2, "ICON-D2", df_eu, "ICON-EU", show_plot,
#                        f".\\MAE_Vergleich_ViolinPlt_ICON_D2_ICON_EU.svg")
# print(f"Median vom absoluten Fehler zwischen ICON-D2 und DWD-Stationen: {df_d2[COL_ABS_ERROR].median():.2f}%")
# print(f"Median vom absoluten Fehler zwischen ICON-EU und DWD-Stationen: {df_eu[COL_ABS_ERROR].median():.2f}%")
# print(type(da.get_dwd_height_details(df_d2)))
# print(da.get_dwd_height_details(df_eu))

# compare_fcst_error(df_d2, "ICON-D2")
# compare_fcst_error(df_eu, "ICON-EU")

# TODO: Als Funktion auslagern, auch mit Dateiexport
# Erstelle eine Projektion für die Karte
# df = df_d2.groupby("Station_ID").agg({
#     "Lat": "first",  # Breitengrad der Station
#     "Lon": "first",  # Längengrad der Station
#     "Absolute_Error": "mean"  # Mittelwert des absoluten Fehlers
# }).reset_index()

# fig = plt.figure()
# _set_fonts()
# ax = fig.add_subplot(1, 1, 1, projection=ccrs.PlateCarree())
# ax.set_extent([df["Lon"].min() - 1, df["Lon"].max() + 1,
#                df["Lat"].min() - 1, df["Lat"].max() + 1],
#               crs=ccrs.PlateCarree())
#
# # Füge natürliche Erdeigenschaften hinzu
# ax.add_feature(cfeature.COASTLINE)
# ax.add_feature(cfeature.BORDERS, linestyle=":")
# ax.add_feature(cfeature.OCEAN)
# ax.add_feature(cfeature.LAKES, alpha=0.5)
# ax.add_feature(cfeature.RIVERS)
# scatter = ax.scatter(df["Lon"], df["Lat"],
#                      c=df["Absolute_Error"],
#                      cmap="rainbow",
#                      s=35,
#                      alpha=0.80,
#                      edgecolor="black",
#                      transform=ccrs.PlateCarree())
# plt.colorbar(scatter, label="Mittelwert des absoluten Fehlers")
#
#
# gl = ax.gridlines(draw_labels=True, linewidth=1, color="gray", alpha=0.5, linestyle='--')
# gl.top_labels = False
# gl.right_labels = False
# plt.title("Geografische Verteilung des mittleren absoluten Fehlers", fontweight="bold")
# plt.tight_layout()
# plt.show()

# TODO: Überarbeitung der Reihenfolge der Ausgaben!!


# TODO: Scatter Plot für die Verteilung der DWD-Stationen in Deutschland
# TODO: Bedeckungsgrad in einem Gebiet zeigen (ICON-D2 und ICON-EU) plus DWD-Werte der Stationen
#  Die Werte der DWD-Station plus Icon-Modell-Werte ausgeben
# TODO: Ungenauigkeiten der Modelle selbst (0min, 60min, 120min) im Violinplot, Median ausgeben lassen


# TODO: Unterschied in der Genauigkeit DWD-Stationsmessung Person und Instrument, mit Angabe wie viele Datenpunkte
# TODO: Berechnen vom Z-Score -> Nur die Werte oberhalb von 12,5% sind relevant
# TODO: Prüfen, wegen Normalverteilung oder nicht und dann Pearson-Korrelationskoeffizient oder
#  Spearman-Rangkorrelationskoeffizient berechnen um den Einfluss zu messen


# copy all created svg to my target MA-Picture Folder
# if override_existing_plot_export:
#     svgs = get_files(".\\", ".svg")
#     for svg in svgs:
#         target = os.path.join(MOVE_TO, svg)
#         if os.path.exists(target):
#             os.remove(target)
#         shutil.move(svg, MOVE_TO)
