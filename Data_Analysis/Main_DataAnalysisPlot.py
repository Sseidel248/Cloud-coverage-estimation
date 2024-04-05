"""
File name:      Main_DataAnalysisPlot.py
Author:         Sebastian Seidel
Date:           2024.**.**
"""
import os
import pickle
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import cartopy.crs as ccrs
import cartopy.feature as cfeature
import numpy
import numpy as np
import pandas as pd
import statsmodels.api as sm

from matplotlib import pyplot
from matplotlib.axes import Axes
from matplotlib.collections import PathCollection
from Lib import DataAnalysis as da
from pandas import DataFrame
from Lib.IOConsts import *
from matplotlib.colors import LinearSegmentedColormap
from scipy.spatial.distance import cdist
from pathlib import Path


def _set_fonts(scale: float = 1):
    plt.rcParams["font.family"] = "calibri"
    plt.rcParams["font.size"] = 12 * scale
    plt.rcParams["axes.titlesize"] = 12 * scale
    plt.rcParams["axes.labelsize"] = 12 * scale


def _show_and_export(a_plt: pyplot, show: bool, exportname: str):
    if exportname != "":
        _, ext = os.path.split(exportname)
        if ext == ".png":
            a_plt.savefig(exportname, dpi=900)
        else:
            a_plt.savefig(exportname)
    if show:
        a_plt.show()
    else:
        a_plt.close()


def _show_median_on_violin(df: DataFrame,
                           a_plt: pyplot):
    for i, col in enumerate(df.columns):
        median_val = df[col].median()
        a_plt.text(i + 1, median_val, f' {median_val:.2f}', color='black', ha='left', va='bottom')


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


def _show_as_table(title: str,
                   dwd_locs: DataFrame,
                   icon_d2_area: DataFrame,
                   icon_eu_area: DataFrame):
    print(f"\n~~~{title}~~~\n")
    dist_mat_d2 = cdist(dwd_locs[[COL_LAT, COL_LON]], icon_d2_area[[COL_LAT, COL_LON]],
                        metric="euclidean")
    dist_mat_eu = cdist(dwd_locs[[COL_LAT, COL_LON]], icon_eu_area[[COL_LAT, COL_LON]],
                        metric="euclidean")
    closest_idx_d2 = dist_mat_d2.argmin(axis=1)
    closest_idx_eu = dist_mat_eu.argmin(axis=1)
    closest_entries_d2 = (icon_d2_area.iloc[closest_idx_d2]
                          .drop([COL_DATE, COL_LAT, COL_LON, COL_MODEL_FCST_MIN], axis=1)
                          .rename(columns={CLOUD_COVER: f"{CLOUD_COVER} {MODEL_ICON_D2}"}))
    closest_entries_eu = (icon_eu_area.iloc[closest_idx_eu]
                          .drop([COL_DATE, COL_LAT, COL_LON, COL_MODEL_FCST_MIN], axis=1)
                          .rename(columns={CLOUD_COVER: f"{CLOUD_COVER} {MODEL_ICON_EU}"}))
    result_entries = pd.concat([dwd_locs,
                                closest_entries_d2.reset_index(drop=True),
                                closest_entries_eu.reset_index(drop=True)],
                               axis=1)
    print(result_entries)


def _drop_param(df: DataFrame, params: list[str]) -> DataFrame:
    df_clean = df.copy()
    for param in params:
        if param in df.columns:
            # drop hole column
            df_clean.drop(param, axis=1, inplace=True)
    # drop row who includes nan
    df_clean.dropna(inplace=True)
    return df_clean


def _get_param_x_label(param: str) -> str:
    if param == "V_N":
        return "Bewölungsgrad [%]"
    elif param == "F":
        return "Windgeschwindigkeit [m/s]"
    elif param == "RF_TU":
        return "Relative Feuchtigkeit [%]"
    elif param == "TT_TU":
        return "Lufttemperatur [°C]"
    elif param == "P":
        return "Luftdruck auf Meereshöhe NN [hPa]"
    else:
        return "Undefinierter Parameter [-]"


def _print_corr_results(pvalue_n: float, coef_r: float, pvalue_r):
    # Data not normally distributed
    if pvalue_n > 0.05:
        print(f"Person-Korrelationsberechnung: Koeffizient={coef_r}")
        print(f"Person-Korrelationsberechnung: P-Wert={pvalue_r}")
    # Data normally distributed
    else:
        print(f"Spearman-Rangkorrelationsberechnung: Koeffizient={coef_r}")
        print(f"Spearman-Rangkorrelationsberechnung: P-Wert={pvalue_r}")


def make_hist(df: DataFrame,
              title: str,
              y_label: str,
              x_label: str,
              num_bins: int,
              show: bool = True,
              exportname: str = "",
              min_value: float = 0,
              max_y_lim: int = -1,
              color_value_above: float = 0):
    _set_fonts()
    arr = df.hist(bins=num_bins, color="skyblue", edgecolor="black", range=[min_value, df.max()])
    plt.title(title, fontweight="bold")
    plt.ylabel(y_label)
    plt.xlabel(x_label)
    plt.grid(alpha=0.75)
    if color_value_above > 0:
        for patch in arr.patches:
            if patch.xy[0] >= color_value_above:
                patch.set_facecolor("orange")
        custom_patch_1 = plt.Rectangle((0, 0), 1, 1, fc="skyblue", edgecolor="black",
                                       label=f"< {color_value_above} %")
        custom_patch_2 = plt.Rectangle((0, 0), 1, 1, fc="orange", edgecolor="black",
                                       label=f"≥ {color_value_above} %")
        plt.legend(handles=[custom_patch_1, custom_patch_2])
    if max_y_lim > 0:
        plt.ylim(top=max_y_lim)
    _show_and_export(plt, show, exportname)


def make_compare_violinplt(df1: DataFrame,
                           name1: str,
                           df2: DataFrame,
                           name2: str,
                           show: bool = True,
                           exportname: str = ""):
    _set_fonts()
    df1.sort_values(by=COL_STATION_ID, inplace=True)
    df1.reset_index(inplace=True)
    df2.sort_values(by=COL_STATION_ID, inplace=True)
    df2.reset_index(inplace=True)
    combined_df = pd.DataFrame({name1: df1[COL_ABS_ERROR], name2: df2[COL_ABS_ERROR]})
    combined_df.dropna(inplace=True)
    plt.violinplot(combined_df.values, showmedians=True)
    plt.title(f"Verteilung vom MAE Modelle\n({name1} und {name2}) zu den DWD-Stationen", fontweight="bold")
    plt.ylabel("MAE Bedeckungsgrad [%]")
    plt.xlabel("Modelle")
    plt.xticks(ticks=range(1, len(combined_df.columns) + 1), labels=combined_df.columns)
    plt.grid(alpha=0.75)
    _show_median_on_violin(combined_df, plt)
    _show_and_export(plt, show, exportname)


def make_qq_plot(df: DataFrame,
                 title: str,
                 show: bool = True,
                 exportname: str = ""):
    _set_fonts()
    sm.qqplot(df, line='45')
    plt.title(title, fontweight="bold")
    plt.xlabel("Theoretische Quantile der Standardnormalverteilung")
    plt.ylabel("Empirische Quantile der Stichprobe")
    plt.grid(alpha=0.75)
    plt.legend(labels=["Datenpunkt", "Ideallinie"], loc="lower right")
    _show_and_export(plt, show, exportname)


def show_me_mae_rmse(df: DataFrame, col_model: str, col_dwd: str):
    me_mae_rmse = da.get_me_mae_rmse(df, col_model, col_dwd)
    print(f"Mittlerer Fehler (ME): {me_mae_rmse[0]:.2f}% Bedeckungsgrad")
    print(f"Mittlere abs. Fehler (MAE): {me_mae_rmse[1]:.2f}% Bedeckungsgrad")
    print(f"Mittlere quad. Fehler (RMSE): {me_mae_rmse[2]:.2f}% Bedeckungsgrad")


def make_compare_proportion_lineplt(df1: DataFrame,
                                    df2: DataFrame,
                                    show: bool = True,
                                    exportname: str = ""):
    def calc_protortion(df: DataFrame, value: int) -> float:
        return len(da.filter_dataframe_by_value(df, COL_ABS_ERROR, value, False)) / len(df) * 100

    line1 = []
    line2 = []
    x = numpy.arange(0, 101, 12.5)
    for i in x:
        line1.append(calc_protortion(df1, i))
        line2.append(calc_protortion(df2, i))
    _set_fonts()
    plt.plot(x, line1, label="ICON-D2", marker="x")
    plt.plot(x, line2, label="ICON-EU", marker="x")
    plt.legend()
    plt.grid()
    plt.title("Prozentualer Anteil der Daten basierend "
              "\nauf dem absoluten Fehler des Bewölkungsgrads der DWD-Stationen",
              fontweight="bold")
    plt.xlabel("Absoluter Fehler [%]")
    plt.xticks([0, 12.5, 25, 37.5, 50, 62.5, 75, 87.5, 100],
               ["0/8", "1/8", "2/8", "3/8", "4/8", "5/8", "6/8", "7/8", "8/8"])
    plt.ylabel("Differenz zu den Bewölkungsgraden des DWD")
    _show_and_export(plt, show, exportname)


def show_error_metrics(df: DataFrame, model: str, show: bool = True, max_y_lim: int = -1):
    stations_info = da.get_mean_abs_error_each_station(df)
    print(f"\n~~~{model}~~~\n")
    show_me_mae_rmse(df, "TCDC", "V_N")
    print(f"{len(da.filter_dataframe_by_value(df, COL_ABS_ERROR, 5, False)) / len(df) * 100:.2f}% "
          f"der Daten haben einen absoluten Fehler von < 5% Bedeckungsgrad.")
    print(f"{len(da.filter_dataframe_by_value(df, COL_ABS_ERROR, 12.5, False)) / len(df) * 100:.2f}% "
          f"der Daten haben einen absoluten Fehler von < 12,5% Bedeckungsgrad (1/8).")
    print(f"{len(da.filter_dataframe_by_value(df, COL_ABS_ERROR, 25, False)) / len(df) * 100:.2f}% "
          f"der Daten haben einen absoluten Fehler von < 25% Bedeckungsgrad (2/8).")
    print(f"{len(da.filter_dataframe_by_value(df, COL_ABS_ERROR, 50, False)) / len(df) * 100:.2f}% "
          f"der Daten haben einen absoluten Fehler von < 50% Bedeckungsgrad (4/8).")
    print(f"{len(da.filter_dataframe_by_value(df, COL_ABS_ERROR, 75)) / len(df) * 100:.2f}% "
          f"der Daten haben einen absoluten Fehler von > 75% Bedeckungsgrad (6/8).")

    make_hist(stations_info[COL_MEAN_ABS_ERROR],
              f"Verteilung des MAE von {model} zu den DWD-Stationen\n(Anzahl DWD-Stationen: {len(stations_info)})",
              f"Anzahl DWD-Stationen",
              f"MAE vom Bedeckungsgrad [%]",
              30,
              show,
              f".\\plots\\HistPlt_Verteilung_MAE_{model}_DWD_Stationen.svg",
              color_value_above=12.5)
    make_hist(df[COL_ABS_ERROR],
              f"Verteilung des absoluten Fehlers von {model} zu den DWD-Stationen\n(Anzahl Daten: {len(df)})",
              f"Anzahl berechnete Modelldaten",
              f"Absoluter Fehler vom Bedeckungsgrad [%]",
              40,
              show,
              f".\\plots\\HistPlt_MAE_{model}_DWD_Stationen.svg",
              max_y_lim=max_y_lim)


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
    plt.xlabel("Prognose")
    plt.xticks(ticks=range(1, len(combined_df.columns) + 1), labels=combined_df.columns)
    plt.grid(alpha=0.75)
    _show_median_on_violin(combined_df, plt)
    _show_and_export(plt, show, exportname)


def make_scatterplot_dwd_locations(df: DataFrame,
                                   show: bool = True,
                                   exportname: str = "",
                                   model: str = "",
                                   show_mean_abs_error: bool = False,
                                   custom_col_bar_label: str = "",
                                   custom_title: str = ""):
    # calculation of MAE
    if show_mean_abs_error:
        df_data = df.groupby(COL_STATION_ID).agg({
            COL_LAT: "first",
            COL_LON: "first",
            COL_ABS_ERROR: "mean"
        }).reset_index()
    else:
        df_data = df.groupby(COL_STATION_ID).agg({
            COL_LAT: "first",
            COL_LON: "first"
        }).reset_index()

    fig = plt.figure()
    _set_fonts()
    ax = fig.add_subplot(1, 1, 1, projection=ccrs.PlateCarree())
    ax.set_extent([df_data[COL_LON].min() - 1, df_data[COL_LON].max() + 1,
                   df_data[COL_LAT].min() - 1, df_data[COL_LAT].max() + 1],
                  crs=ccrs.PlateCarree())
    _add_geographic(ax)
    if show_mean_abs_error:
        sc = ax.scatter(df_data[COL_LON], df_data[COL_LAT],
                        c=df_data[COL_ABS_ERROR],
                        cmap="rainbow",
                        s=35,
                        alpha=0.80,
                        edgecolor="black",
                        transform=ccrs.PlateCarree())
        if custom_col_bar_label == "":
            plt.colorbar(sc, ax=ax, label="Absoluter Fehler [%]")
        else:
            plt.colorbar(sc, ax=ax, label=custom_col_bar_label)
        plt.title(f"Geografische Verteilung des absoluten Fehler zwischen {model}\nund den DWD-Stationen",
                  fontweight="bold")
    else:
        sc = ax.scatter(df_data[COL_LON], df_data[COL_LAT],
                        s=35,
                        alpha=0.80,
                        edgecolor="black",
                        transform=ccrs.PlateCarree())
        plt.title("Geografische Verteilung der DWD-Stationen zum\nMessen des Bedeckungsgrades", fontweight="bold")
    if custom_title != "":
        plt.title(custom_title, fontweight="bold")
    sc.set_label("DWD-Station")
    ax.legend()
    plt.tight_layout()
    _show_and_export(plt, show, exportname)


def make_scatterplot_dwd_locs_compare(df1: DataFrame,
                                      df2: DataFrame,
                                      show: bool = True,
                                      exportname: str = "",
                                      legend_df1: str = "",
                                      legend_df2: str = "",
                                      custom_title: str = ""):
    # Grouped data
    df_data1 = df1.groupby(COL_STATION_ID).agg({
        COL_LAT: "first",
        COL_LON: "first"
    }).reset_index()
    df_data2 = df2.groupby(COL_STATION_ID).agg({
        COL_LAT: "first",
        COL_LON: "first"
    }).reset_index()

    fig = plt.figure()
    _set_fonts()
    ax = fig.add_subplot(1, 1, 1, projection=ccrs.PlateCarree())
    ax.set_extent([df_data1[COL_LON].min() - 1, df_data1[COL_LON].max() + 1,
                   df_data1[COL_LAT].min() - 1, df_data1[COL_LAT].max() + 1],
                  crs=ccrs.PlateCarree())
    _add_geographic(ax)
    sc1 = ax.scatter(df_data1[COL_LON], df_data1[COL_LAT],
                     s=35,
                     alpha=0.8,
                     edgecolor="black",
                     transform=ccrs.PlateCarree())
    sc2 = ax.scatter(df_data2[COL_LON], df_data2[COL_LAT],
                     s=30,
                     alpha=0.80,
                     color="red",
                     marker="x",
                     transform=ccrs.PlateCarree())
    plt.title("Geografische Verteilung der DWD-Stationen",
              fontweight="bold")
    if custom_title != "":
        plt.title(custom_title, fontweight="bold")
    sc1.set_label(legend_df1)
    sc2.set_label(legend_df2)
    ax.legend()
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
    dwd_locs_area_1 = load(dwd_data_area_1).dropna().reset_index()

    data_icon_d2_area_2 = load(model_data_icon_d2_area_2)
    data_icon_eu_area_2 = load(model_data_icon_eu_area_2)
    dwd_locs_area_2 = load(dwd_data_area_2).dropna().reset_index()

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
    # Access to the second Artist object which draws the DWD markings
    fig.legend([axs[1, 1].collections[1]], ["DWD-Station"], loc="center", bbox_to_anchor=(0.5, 0.45))
    cbar = fig.colorbar(sc, ax=[axs[0, 1], axs[1, 1]])
    cbar.set_label("Bedeckungsgrad [%]")
    cbar.set_ticks([0, 12.5, 25, 37.5, 50, 62.5, 75, 87.5, 100])
    plt.suptitle(f"Bedeckungsgrad der Modelle\n Datum: {date}", fontweight="bold")
    # Picture export as png because svg slow down word
    _show_and_export(plt, show, exportname)
    _show_as_table("Area 1", dwd_locs_area_1, data_icon_d2_area_1, data_icon_eu_area_1)
    _show_as_table("Area 2", dwd_locs_area_2, data_icon_d2_area_2, data_icon_eu_area_2)


def show_used_areas_dwd_stations(df_data: DataFrame,
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


def show_num_of_station(df: DataFrame, drop_cols: list[str], param_descr: str):
    tmp = df.drop(drop_cols, axis=1).copy()
    tmp.dropna(inplace=True)
    print(f"Anzahl Stationen die nur {param_descr} messen können: {len(tmp[COL_STATION_ID].unique())}")


def calc_dwd_outliers(df: DataFrame) -> DataFrame:
    abs_error = da.get_mean_abs_error_each_station(df)
    dwd_station_outliers = da.calc_custom_z_score(abs_error, COL_MEAN_ABS_ERROR, 12.5)
    return dwd_station_outliers.loc[dwd_station_outliers[COL_MEAN_ABS_ERROR] >= 12.5]


def load(filename: str) -> DataFrame:
    if not os.path.exists(filename):
        raise FileExistsError
    filepath = Path(filename)
    if filepath.suffix == ".csv":
        return pd.read_csv(filename, sep=";", decimal=",")
    elif filepath.suffix == ".pkl":
        with open(filename, 'rb') as file:
            return pickle.load(file)
    else:
        raise ValueError("Unsupported file extension. Only *.cvs and *.pkl are supported.")


# Initialisation
show_plot = False
dwd_params = ["V_N", "V_N_I", "D", "F", "RF_TU", "TT_TU", "P", "P0"]

# Loading CSV-Files
# df_d2_cloud_only = load(CSV_NAME_ICON_D2)
# df_eu_cloud_only = load(CSV_NAME_ICON_EU)
df_d2_full = load(f".\\datas\\all_param_data_ICON_D2.csv")
df_d2_cloud_only = _drop_param(df_d2_full, ["D", "F", "RF_TU", "TT_TU", "P", "P0"])
df_eu_full = load(f".\\datas\\all_param_data_ICON_EU.csv")
df_eu_cloud_only = _drop_param(df_eu_full, ["D", "F", "RF_TU", "TT_TU", "P", "P0"])
df_dwd_solar = load(f".\\datas\\solar_DWD_Stationlocations.csv")

# Show all used DWD-Locations
make_scatterplot_dwd_locations(df_d2_cloud_only, show_plot, f".\\plots\\ScatPlt_Verwendete_DWD-Stationen.svg")
make_scatterplot_dwd_locs_compare(df_d2_cloud_only, df_dwd_solar, show_plot,
                                  f".\\plots\\ScatPlt_Bedeckungsgrad_Sonnenscheindauer.svg",
                                  "DWD Bedeckungsgrad",
                                  "DWD Sonnenscheindauer",
                                  "Geografische Verteilung der DWD-Stationen zum"
                                  "\nMessen des Bedeckungsgrades und der Sonnenscheindauer")

# Calculate Errors (RMSE, MAE, ME) and show it as text and as diagramm
da.calc_abs_error(df_d2_cloud_only, "TCDC", "V_N")
da.calc_abs_error(df_eu_cloud_only, "TCDC", "V_N")
show_error_metrics(df_d2_cloud_only, MODEL_ICON_D2, show_plot, 30000)
show_error_metrics(df_eu_cloud_only, MODEL_ICON_EU, show_plot, 30000)
make_compare_proportion_lineplt(df_d2_cloud_only,
                                df_eu_cloud_only,
                                show_plot,
                                f".\\plots\\LinPlt_Differenz_Modell_DWD.svg")

# Show Errors between Forecasts
compare_fcst_error(df_d2_cloud_only, MODEL_ICON_D2, show_plot,
                   f".\\plots\\VioPlt_Fehler_zwischen_den_Prognosezeitpunkten_vom_ICON_D2.svg")
compare_fcst_error(df_eu_cloud_only, MODEL_ICON_EU, show_plot,
                   f".\\plots\\VioPlt_Fehler_zwischen_den_Prognosezeitpunkten_vom_ICON_EU.svg")

# Show used areas in germany for the example plot
show_used_areas_dwd_stations(df_d2_cloud_only, show_plot, f".\\plots\\ScatPlt_DWD_Station_Cloud_Coverage.svg")

# Show Weather example plot
make_scatterplots_cloud_coverage(f".\\datas\\Area_I_ICON-D2.csv",
                                 f".\\datas\\Area_I_ICON-EU.csv",
                                 f".\\datas\\DWD-Stations_in_Area_I_ICON-D2.csv",
                                 f".\\datas\\Area_II_ICON-D2.csv",
                                 f".\\datas\\Area_II_ICON-EU.csv",
                                 f".\\datas\\DWD-Stations_in_Area_II_ICON-D2.csv",
                                 show_plot,
                                 f".\\plots\\ScatPlt_Cloud_Coverage_Compare_ICON-D2_ICON-EU.png")

# Show compare of MAE from ICON-D2 and ICON-EU
make_compare_violinplt(df_d2_cloud_only, MODEL_ICON_D2, df_eu_cloud_only, MODEL_ICON_EU, show_plot,
                       f".\\plots\\VioPlt_MAE_Vergleich_ICON_D2_ICON_EU.svg")

# Show difference between MAE for each DWD-Station of ICON-D2 and ICON-EU
df_diff = df_d2_cloud_only[[COL_STATION_ID, COL_LAT, COL_LON]].copy()
df_diff[COL_ABS_ERROR] = abs(df_d2_cloud_only[COL_ABS_ERROR] - df_eu_cloud_only[COL_ABS_ERROR])
make_scatterplot_dwd_locations(df_diff, show_plot, f".\\plots\\ScatPlt_Diff_MAE_vergleich_ICON-D2_EU.svg",
                               MODEL_ICON_D2, True,
                               "Differenz Fehlerbewölkungsgrad [%]",
                               "Verteilung der Fehlerdifferenzen von ICON-D2 und ICON-EU\n"
                               "bezogen auf die DWD-Stationen")

# only D2 #
# D2 - Calculate outliers in the data
dwd_outlier_d2 = calc_dwd_outliers(df_d2_cloud_only)

# remove unused DWD-Param
# remove pressure at Station_height
dwd_params.remove("P0")
# remove wind direction
dwd_params.remove("D")
# remove cloud coverage dwd Station
dwd_params.remove("V_N")
dwd_params.remove("V_N_I")
# add Station-Height
dwd_params.append(COL_STATION_HEIGHT)

# collect all DWD-Stations who can measure all params
print(f"\n~~~DWD-Stationsinformationen~~~\n")
print(f"Anzahl aller Stationen (beinhaltet auch Stationshöhe): {len(df_d2_full[COL_STATION_ID].unique())}")

dwd_station_all_param = df_d2_full.dropna().copy()
print(f"Anzahl der DWD-Stationen die alle Parameter messen: {len(dwd_station_all_param[COL_STATION_ID].unique())}")
da.calc_abs_error(dwd_station_all_param, "TCDC", "V_N")

show_num_of_station(df_d2_full, ["V_N_I", "D", "F", "RF_TU", "TT_TU", "P", "P0"], "Bewölkungsgrad (V_N)")
v_n_i_df = df_d2_cloud_only.dropna()
measurment_counts = v_n_i_df['V_N_I'].value_counts()
print(f"    Davon wurden {measurment_counts['I'] / len(v_n_i_df) * 100:.2f} % durch ein Instrument aufgenommen.")
print(f"    Davon wurden {measurment_counts['P'] / len(v_n_i_df) * 100:.2f} % durch eine Person aufgenommen.")
print(f"    Für {measurment_counts['-999'] / len(v_n_i_df) * 100:.2f} % gab es keine Angaben.")

show_num_of_station(df_d2_full, ["V_N_I", "V_N", "D", "F", "RF_TU", "P", "P0"], "Lufttemperatur (TT_TU)")
show_num_of_station(df_d2_full, ["V_N_I", "V_N", "D", "F", "TT_TU", "P", "P0"], "relative Feuchte (RF_TU)")
show_num_of_station(df_d2_full, ["V_N_I", "D", "F", "TT_TU", "RF_TU", "P0"], "Luftdruck auf Meereshöhe NN (P)")
show_num_of_station(df_d2_full, ["V_N_I", "D", "TT_TU", "RF_TU", "P0"], "Windgeschwindigkeit (F)")

# explorative dataanalysis for each dwd param
for dwd_param in dwd_params:
    print(f"\n~~~{dwd_param}~~~\n")
    print(da.get_dwd_col_details(dwd_station_all_param, dwd_param))
    param_details = dwd_station_all_param[dwd_param].dropna()
    make_hist(param_details,
              f"Verteilung vom Parameter: {dwd_param}",
              "Anzahl Datenpunkte",
              _get_param_x_label(dwd_param),
              30,
              show_plot,
              f".\\plots\\HistPlt_Verteilung_DWD_Param_{dwd_param}.svg",
              min_value=param_details.min())
    make_qq_plot(param_details,
                 f"QQ-Plot vom Parameter: {dwd_param}",
                 show_plot,
                 f".\\plots\\QQPlot_DWD_Param_{dwd_param}.png")
    _, pvalue = da.normaltest(param_details)
    print(f"Normaltest von {dwd_param}: p-Value = {pvalue:.4f}")
    coef, pvaluer = da.calc_corr_coef(pvalue, dwd_station_all_param, COL_ABS_ERROR, dwd_param)
    _print_corr_results(pvalue, coef, pvaluer)

print(f"\n~~~Vergleich Instrumentmessung und Personenmessung - Bewölkungsgrad~~~\n")
print(
    f"Hier werden nur RMSE, MAE und ME betrachtet, da ein Zusammenhang zwischen TCDC und V_N definitiv bestehen würde,"
    f" denn Beide beinhalten den Bewölkungsgrad.")
print(f"\nFehler: Instrumentmessung")
show_me_mae_rmse(v_n_i_df[v_n_i_df["V_N_I"] == "I"], "TCDC", "V_N")
print(f"\nFehler: Personenmessung")
show_me_mae_rmse(v_n_i_df[v_n_i_df["V_N_I"] == "P"], "TCDC", "V_N")

# calculate DWD-Station locations with idw radius von 0.04°
df_d2_idw_cloud_only = load(f".\\datas\\idw_data_ICON_D2.csv")
da.calc_abs_error(df_d2_idw_cloud_only, "TCDC", "V_N")
make_compare_violinplt(df_d2_cloud_only, "ICON-D2", df_d2_idw_cloud_only, "ICON-D2 mit IDW", show_plot,
                       f".\\plots\\VioPlt_MAE_Vergleich_ICON_D2_mit_ohne_IDW.svg")
