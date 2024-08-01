"""
General Information:
______
- File name:      Main_Data_Evaluation.py
- Author:         Sebastian Seidel
- Date:           2024.04.10

Description:
______
The generated export files ('.csv' or '.pkl') from Main_Data_Processing.py are loaded and analyzed
here. After the evaluation and analysis, graphics are saved in addition to textual results.
"""
import os
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import cartopy.crs as ccrs
import cartopy.feature as cfeature
from mpl_toolkits.basemap import Basemap
import numpy
import numpy as np
import pandas as pd
import statsmodels.api as sm
from matplotlib.legend import Legend
from matplotlib.transforms import Bbox
import Lib.DataAnalysis as da
from matplotlib import pyplot
from matplotlib.axes import Axes
from matplotlib.collections import PathCollection
from pandas import DataFrame
from Lib.IOConsts import *
from matplotlib.colors import LinearSegmentedColormap
from scipy.spatial.distance import cdist
from pathlib import Path


def _set_fonts(scale: float = 1):
    """
    Sets the font family and sizes for matplotlib plots to Calibri, adjusting the size based on a scaling factor.

    This function directly modifies the matplotlib runtime configuration (rcParams) to set the global font family to
    Calibri and adjusts the font size for different elements of the plots (general font size, axes titles, and axes
    labels) according to the provided scale factor. The default font size is multiplied by the scale to allow for
    customization of the plot's appearance.

    :param scale: (float, optional): A scaling factor for the font sizes. The default value is 1, which keeps the font
                  sizes at their base values (12 for general text, axes titles, and labels). A value greater than 1
                  increases the font sizes proportionally, while a value less than 1 decreases them.

    :return: None
    """
    plt.rcParams["font.family"] = "calibri"
    plt.rcParams["font.size"] = 12 * scale
    plt.rcParams["axes.titlesize"] = 12 * scale
    plt.rcParams["axes.labelsize"] = 12 * scale


def _show_and_export(a_plt: pyplot, show: bool, exportname: str):
    """
    Displays or exports a Matplotlib plot based on the given parameters. The plot can be exported to a file
    with the specified name. If exporting, the function checks the file extension to decide on the DPI setting;
    .png files are saved with a high DPI for better resolution.

    :param a_plt: The Matplotlib pyplot object to be shown or exported.
    :param show: A boolean flag that determines whether the plot should be displayed. If False, the plot is not shown.
    :param exportname: The filename for exporting the plot. If this is an empty string, no file is exported.
                       Supports high-resolution export for .png files specifically.

    Note: If 'exportname' is provided and does not end with '.png', the plot is saved with default DPI settings.
          The function closes the plot window if 'show' is False, to prevent it from using system resources.
    """
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
    """
    Annotates the median values on each violin plot in a Matplotlib figure. This function iterates through
    the columns of the provided DataFrame, calculates the median for each column, and then uses the pyplot
    text method to display these median values at the appropriate position on each violin plot.

    :param df: The pandas DataFrame containing the data for which violin plots have been created. Assumes that each
               column in the DataFrame corresponds to a separate violin plot on the current pyplot figure.
    :param a_plt: The Matplotlib pyplot object on which the violin plots are drawn and where the median annotations
                  will be added.

    Note: The function calculates the median value for each column in the DataFrame and displays it on the
          corresponding violin plot. The median is formatted to two decimal places. The annotations are positioned
          just above the median value within each plot, aligned to the left of the centerline of the violin plot.
    """
    for i, col in enumerate(df.columns):
        median_val = df[col].median()
        a_plt.text(i + 1, median_val, f" {median_val:.2f}", color="black", ha="left", va="bottom")


def _add_geographic(ax: Axes):
    """
    Enhances the provided Matplotlib Axes object by adding geographic features such as coastlines, borders,
    oceans, lakes, and rivers. It also adds gridlines to the plot for better readability and geographic
    orientation. The function is designed to work with cartopy, a library for geographic data visualization.

    :param ax: The Matplotlib Axes object to which the geographic features will be added. This object must be
               compatible with cartopy, as the features are added using cartopy's feature interface.

    Note: Borders are added with a dotted line style, lakes are semi-transparent, and rivers are added with
          default styling. Gridlines are added with labels on the left and bottom edges only, with a light gray,
          semi-transparent, dashed line style. Top and right labels for gridlines are disabled to maintain a
          clean appearance.
    """
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
    """
    Adds cloud coverage data to a subplot represented by the given Axes object. This function uses two sets of
    data: model data for cloud coverage and DWD station data, and plots them with distinct markers and colors.
    Geographic features such as coastlines, borders, and bodies of water are added for context. Model data points
    are displayed as squares colored based on cloud cover percentage, while DWD station data points are marked
    with red 'x' symbols.

    :param ax: The Matplotlib Axes object on which the data will be plotted. Should be set up with a geographic
               projection compatible with cartopy.
    :param data_model: A pandas DataFrame containing model data with longitude (COL_LON), latitude (COL_LAT),
                       and cloud coverage (CLOUD_COVER) columns.
    :param data_dwd: A pandas DataFrame containing DWD station data, expected to have longitude (COL_LON) and
                     latitude (COL_LAT) columns.
    :param colors: A Matplotlib LinearSegmentedColormap used to color the model data points based on their cloud
                   coverage values.

    :return: A PathCollection object representing the model data points plotted on the map.

    Note: This function is designed to visually distinguish between model data and DWD station data on the plot,
          with specific attention to representing cloud coverage data effectively. It also decorates the plot
          with helpful geographic context by calling an internal function to add features like coastlines and
          borders.
    """
    _add_geographic(ax)
    sc = ax.scatter(data_model[COL_LON], data_model[COL_LAT],
                    c=data_model[CLOUD_COVER],
                    vmin=0,
                    vmax=100,
                    cmap=colors,
                    marker="s",
                    alpha=1,
                    transform=ccrs.PlateCarree())
    # ax.scatter(data_dwd[COL_LON], data_dwd[COL_LAT],
    # color="red",
    # s=50,
    # marker="x",
    # alpha=1,
    # transform=ccrs.PlateCarree())

    # numbering the dots
    for i, (lon, lat) in enumerate(zip(data_dwd[COL_LON], data_dwd[COL_LAT])):
        # 'ha' and 'va' mean the position von 'marker'="x"
        ax.annotate(f" {i}", (lon, lat), color="red", fontsize=20, ha="center", va="center",
                    transform=ccrs.PlateCarree())

    return sc


def _drop_param(df: DataFrame, params: list[str]) -> DataFrame:
    """
    Removes specified columns from the DataFrame and then drops any rows that contain NaN values. This function
    creates a copy of the input DataFrame, removes the columns listed in 'params' if they exist, and subsequently
    removes any rows that have missing values in any of the remaining columns.

    :param df: The pandas DataFrame from which columns and rows with NaN values will be removed.
    :param params: A list of strings representing the names of the columns to be removed from the DataFrame.

    :return: A pandas DataFrame that has been cleaned by removing specified columns and any rows with NaN values
             across the remaining columns.

    Note: This function is particularly useful for cleaning data by removing unnecessary columns and ensuring
          that the dataset does not contain any incomplete records. The operation is performed on a copy of
          the input DataFrame to avoid modifying the original data.
    """
    df_clean = df.copy()
    for param in params:
        if param in df.columns:
            # drop hole column
            df_clean.drop(param, axis=1, inplace=True)
    # drop row who includes nan
    df_clean.dropna(inplace=True)
    return df_clean


def _get_param_x_label(param: str) -> str:
    """
    Returns a descriptive x-axis label for a given weather parameter. The function maps common weather parameter
    abbreviations to their full descriptions and units, facilitating more informative plot labels.

    :param param: A string representing the abbreviation of the weather parameter. Recognized parameters include
                  'V_N' for cloud cover, 'F' for wind speed, 'RF_TU' for relative humidity, 'TT_TU' for air temperature,
                  and 'P' for sea-level air pressure.

    :return: A string containing the full description and units of the parameter, suitable for use as an x-axis
             label in plots. If the parameter is not recognized, it returns a generic label indicating an undefined
             parameter.

    Note: This function is designed to enhance the readability and interpretability of plots by providing detailed
          axis labels for various weather-related data points.
    """
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
    elif param == COL_STATION_HEIGHT:
        return "Stationshöhe bezogen auf NN [m]"
    else:
        return "Undefinierter Parameter [-]"


def show_as_table(title: str,
                  dwd_locs: DataFrame,
                  icon_d2_area: DataFrame,
                  icon_eu_area: DataFrame):
    """
    Displays a consolidated table in the console, summarizing the DWD location data along with the closest
    matching entries from ICON-D2 and ICON-EU model data based on geographic proximity. The function calculates
    the Euclidean distance between each DWD location and all ICON model data points, identifies the closest
    model data points for both ICON-D2 and ICON-EU, and prints a table that includes the DWD data and the
    cloud coverage values from the closest points in both models.

    Parameters:
    :param title: A string to be displayed as the title of the table.
    :param dwd_locs: A pandas DataFrame containing DWD station locations, expected to include columns for
                     latitude (COL_LAT) and longitude (COL_LON).
    :param icon_d2_area: A pandas DataFrame containing ICON-D2 model data, including latitude (COL_LAT),
                         longitude (COL_LON), and cloud coverage (CLOUD_COVER) among others.
    :param icon_eu_area: A pandas DataFrame containing ICON-EU model data in the same format as icon_d2_area.

    Note: The function removes specific columns from the ICON model data (like forecast date and minimum forecast)
          before displaying the table. It renames the cloud coverage columns to distinguish between the two models.
          The resulting table is printed to the console, providing an easy-to-read comparison of DWD locations
          and their corresponding cloud coverage values from the nearest ICON-D2 and ICON-EU model data points.
    """
    print(f"\n~~~ {title} ~~~\n")
    dist_mat_d2 = cdist(dwd_locs[[COL_LAT, COL_LON]], icon_d2_area[[COL_LAT, COL_LON]],
                        metric="euclidean")
    dist_mat_eu = cdist(dwd_locs[[COL_LAT, COL_LON]], icon_eu_area[[COL_LAT, COL_LON]],
                        metric="euclidean")
    closest_idx_d2 = dist_mat_d2.argmin(axis=1)
    closest_idx_eu = dist_mat_eu.argmin(axis=1)
    # Get the model values with the index array and adjust the DataFrame
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
    print(result_entries.to_string())


def print_corr_results(pvalue_n: float, coef_c: float, pvalue_c):
    """
    Prints the results of a correlation analysis, choosing between Pearson and Spearman correlation based on
    a preliminary test for normal distribution. If the data are not normally distributed (p-value > 0.05),
    Pearson correlation results are printed. Otherwise, Spearman rank correlation results are shown.

    :param pvalue_n: The p-value from a test of normality. A p-value greater than 0.05 indicates that the data
                     are not normally distributed.
    :param coef_c: The correlation coefficient. This could be Pearson's r or Spearman's rho, depending on the
                   distribution of the data.
    :param pvalue_c: The p-value associated with the correlation coefficient, indicating the significance of the
                     correlation.

    Note: This function is designed to provide a flexible reporting of correlation results, automatically selecting
          the appropriate type of correlation analysis based on the distribution characteristics of the data.
    """
    # Data not normally distributed
    if pvalue_n > 0.05:
        print(f"Person-Korrelationsberechnung: Koeffizient={coef_c}")
        print(f"Person-Korrelationsberechnung: P-Wert={pvalue_c}")
    # Data normally distributed
    else:
        print(f"Spearman-Rangkorrelationsberechnung: Koeffizient={coef_c}")
        print(f"Spearman-Rangkorrelationsberechnung: P-Wert={pvalue_c}")


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
    """
    Creates and optionally displays or exports a histogram for the specified DataFrame. The histogram's appearance
    is customizable with parameters for the title, axis labels, and color. Values above a certain threshold can be
    highlighted in a different color.

    :param df: The pandas DataFrame containing the data to plot.
    :param title: The title of the histogram.
    :param y_label: The label for the y-axis.
    :param x_label: The label for the x-axis.
    :param num_bins: The number of bins for the histogram.
    :param show: A boolean indicating whether to display the histogram. Defaults to True.
    :param exportname: The filename for exporting the histogram. If empty, the histogram is not exported.
    :param min_value: The minimum value to include in the histogram. Defaults to 0.
    :param max_y_lim: The maximum limit for the y-axis. If less than or equal to 0, it is ignored.
    :param color_value_above: A threshold value above which the histogram bars will be colored differently to
                              highlight. If 0 or less, all bars are the same color.

    Note: This function also sets custom fonts for the plot and uses a default skyblue color for histogram bars,
          with an option to highlight bars representing values above a specified threshold in orange. Legends
          and custom maximum y-axis limits can be added as per the parameters.
    """
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
    """
    Generates a violin plot comparing the distributions of absolute errors between two models across DWD stations.
    The function preprocesses the input DataFrames to ensure they are sorted and indexed by station ID before
    combining them for comparison. The plot displays medians and highlights the median values on each violin.

    :param df1: The pandas DataFrame containing the first dataset for comparison, expected to include a column
                for absolute error (COL_ABS_ERROR) and station IDs (COL_STATION_ID).
    :param name1: A descriptive name for the first dataset to be used in the plot legend and axis labeling.
    :param df2: The pandas DataFrame containing the second dataset for comparison, similar to df1.
    :param name2: A descriptive name for the second dataset to be used in the plot legend and axis labeling.
    :param show: A boolean indicating whether to display the plot. Defaults to True.
    :param exportname: The filename for exporting the plot. If empty, the plot is not exported.

    Note: The plot is titled with a comparison of mean absolute errors (MAE) for cloud cover predictions by
          the two models against DWD stations. It is equipped with a grid for better readability, and custom
          fonts are set for aesthetic purposes. If 'show' is False or 'exportname' is provided, the plot is
          either not displayed or exported to a file, respectively.
    """
    _set_fonts()
    df1.sort_values(by=COL_STATION_ID, inplace=True)
    df1.reset_index(inplace=True)
    df2.sort_values(by=COL_STATION_ID, inplace=True)
    df2.reset_index(inplace=True)
    combined_df = pd.DataFrame({name1: df1[COL_ABS_ERROR], name2: df2[COL_ABS_ERROR]})
    combined_df.dropna(inplace=True)
    plt.violinplot(combined_df.values, showmedians=True)
    plt.title(f"Vergleich vom MAE der Modelle\n({name1} und {name2}) zu den DWD-Stationen", fontweight="bold")
    plt.ylabel("MAE Bedeckungsgrad [%]")
    plt.xlabel("Modelle")
    plt.xticks(ticks=range(1, len(combined_df.columns) + 1), labels=combined_df.columns)
    plt.grid(alpha=0.75)
    _show_median_on_violin(combined_df, plt)
    _show_and_export(plt, show, exportname)


def make_hist_qq_plot_compare(df: DataFrame,
                              title_hist: str,
                              title_qq: str,
                              x_label_hist: str,
                              y_label_hist: str,
                              show: bool = True,
                              exportname: str = ""):
    """
    Creates a quantile-quantile (Q-Q) plot to compare the empirical quantiles of the sample data in the DataFrame
    against the theoretical quantiles of a standard normal distribution. This plot helps in visually assessing
    if the data follow a normal distribution. The function sets custom fonts for the plot and adds a legend to
    distinguish between the data points and the reference line.

    :param df: The pandas DataFrame containing the sample data for which the Q-Q plot will be generated.
               Assumes that the DataFrame has a single column or that the first column will be used for the plot.
    :param title_hist: The title of the histogram plot.
    :param title_qq: The title of the qq-plot
    :param x_label_hist: The label for the x-axis
    :param y_label_hist: The label for the y-axis
    :param show: A boolean indicating whether to display the plot. Defaults to True.
    :param exportname: The filename for exporting the plot. If empty, the plot is not exported.

    Note: The plot is annotated with a title, labels for the x and y axes describing the theoretical and empirical
          quantiles, respectively, and includes a grid for better readability. The function leverages statsmodels'
          qqplot function for plot generation, drawing a 45-degree line that represents where the data would lie
          if they perfectly followed a standard normal distribution. If 'show' is False or 'exportname' is
          provided, the plot is either not displayed or exported to a file, respectively.
    """
    _set_fonts(1.4)
    fig, axs = plt.subplots(1, 2, figsize=(10, 6))

    # Histogramm
    axs[0].hist(df, bins=30, edgecolor="black")
    axs[0].set_title(title_hist, fontweight="bold")
    axs[0].set_xlabel(x_label_hist)
    axs[0].set_ylabel(y_label_hist)
    axs[0].grid(alpha=0.75)

    # Q-Q-Plot
    sm.qqplot(df, line="45", ax=axs[1])
    axs[1].set_title(title_qq, fontweight="bold")
    axs[1].set_xlabel("Theoretische Quantile der Standard-\nnormalverteilung")
    axs[1].set_ylabel("Empirische Quantile der Stichprobe")
    axs[1].grid(alpha=0.75)
    axs[1].legend(labels=["Datenpunkt", "Ideallinie"], loc="lower right")

    plt.tight_layout()
    _show_and_export(plt, show, exportname)


def show_me_mae_rmse(df: DataFrame, col_model: str, col_dwd: str):
    """
    Calculates and displays the Mean Error (ME), Mean Absolute Error (MAE), and Root Mean Squared Error (RMSE)
    for cloud coverage predictions compared to actual observations. This function assumes that the predictions
    and observations are expressed as percentages of cloud coverage.

    :param df: The pandas DataFrame containing the model predictions and actual DWD observations.
    :param col_model: The name of the column in the DataFrame that contains the model's cloud coverage predictions.
    :param col_dwd: The name of the column in the DataFrame that contains the actual DWD cloud coverage observations.

    Note: The errors are calculated based on the differences between the model's predictions and the actual DWD
          observations. This function prints the ME, MAE, and RMSE, providing a simple evaluation of the model's
          prediction accuracy in terms of cloud coverage.
    """
    me_mae_rmse = da.get_me_mae_rmse(df, col_model, col_dwd)
    print(f"Mittlerer Fehler (ME): {me_mae_rmse[0]:.2f}% Bedeckungsgrad")
    print(f"Mittlere abs. Fehler (MAE): {me_mae_rmse[1]:.2f}% Bedeckungsgrad")
    print(f"Mittlere quad. Fehler (RMSE): {me_mae_rmse[2]:.2f}% Bedeckungsgrad")


def make_compare_proportion_lineplt(df1: DataFrame,
                                    df2: DataFrame,
                                    show: bool = True,
                                    exportname: str = ""):
    """
    Generates a line plot comparing the proportion of data points within specified absolute error ranges
    between two datasets. This function calculates the proportion of data points that fall within each range
    of absolute error regarding cloud coverage compared to DWD stations and plots these proportions across
    the error ranges for both datasets.

    :param df1: The pandas DataFrame for the first dataset, which should include a column for absolute error
                in cloud coverage.
    :param df2: The pandas DataFrame for the second dataset, structured similarly to df1.
    :param show: A boolean indicating whether to display the plot immediately. Defaults to True.
    :param exportname: The filename for exporting the plot to an image file. If left as an empty string, the plot
                       will not be exported.

    Note: This visualization aids in comparing the accuracy and reliability of two cloud coverage prediction
          models against actual observations from DWD stations. It provides insights into which model tends to
          have smaller deviations across different thresholds of absolute error. The x-axis represents error
          thresholds, while the y-axis represents the percentage of data points below each threshold.
    """

    def calc_protortion(df: DataFrame, value: int) -> float:
        """Calculates the percentage of data that is below a certain value."""
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
              "\nauf dem absoluten Fehler des Bedeckungsgrads der DWD-Stationen",
              fontweight="bold")
    plt.xlabel("Differenz zu den Bedeckungsgraden des DWD")
    plt.xticks([0, 12.5, 25, 37.5, 50, 62.5, 75, 87.5, 100],
               ["0/8", "1/8", "2/8", "3/8", "4/8", "5/8", "6/8", "7/8", "8/8"])
    plt.ylabel("Prozentualer Anteil [%]")
    _show_and_export(plt, show, exportname)


def make_compare_hist_plt(df1: DataFrame,
                          df2: DataFrame,
                          title: str,
                          x_label: str,
                          y_label: str,
                          legend: list[str],
                          show: bool = True,
                          exportname: str = ""):
    """
    Generates a histogram comparing the distribution of two datasets. This function plots two histograms
    in one figure, allowing for an easy comparison of the frequency distributions of the datasets.

    :param df1: The pandas DataFrame for the first dataset.
    :param df2: The pandas DataFrame for the second dataset.
    :param title: The title of the plot.
    :param x_label: The label for the x-axis.
    :param y_label: The label for the y-axis.
    :param legend: A list of legend labels corresponding to the datasets.
    :param show: A boolean indicating whether to display the plot immediately. Defaults to True.
    :param exportname: The filename for exporting the plot to an image file. If left as an empty string, the plot
                       will not be exported.

    Note: This visualization aids in comparing the distributions of two datasets by overlaying their histograms.
          It provides insights into how the data points are spread across different values for each dataset.
          The x-axis represents the data values, while the y-axis represents the frequency of data points.
    """

    _set_fonts()
    plt.hist(df1, bins=40, color="skyblue", alpha=0.75, edgecolor="black")
    plt.hist(df2, bins=40, color="orange", alpha=0.5, edgecolor="black")
    plt.title(title, fontweight="bold")
    plt.ylabel(y_label)
    plt.xlabel(x_label)

    plt.grid(alpha=0.75)

    plt.legend(legend)
    _show_and_export(plt, show, exportname)


def show_error_metrics(df: DataFrame, model: str, show: bool = True, max_y_lim: int = -1):
    """
    Displays various error metrics for a given prediction model against actual observations and generates histograms
    to visualize the distribution of these errors. The function prints the mean error (ME), mean absolute error (MAE),
    and root mean squared error (RMSE), along with the proportion of data within specific absolute error thresholds.
    It then creates histograms for the distribution of the mean absolute error across all stations and the overall
    distribution of absolute errors.

    :param df: The pandas DataFrame containing the error data for model predictions. It must include columns for
               absolute error (COL_ABS_ERROR) and the specific comparison columns (e.g., predicted vs. actual cloud
               cover).
    :param model: A string representing the name of the prediction model. This is used for titling plots and print
    statements.
    :param show: A boolean indicating whether to display the generated plots. Defaults to True.
    :param max_y_lim: The maximum y-axis limit for the histogram of absolute errors. If less than or equal to 0,
                      the limit is automatically determined by Matplotlib.

    Note: This function is designed to provide a comprehensive overview of the model's prediction accuracy by
          calculating and displaying key error metrics and visualizing the error distribution. This can aid in
          identifying the model's performance characteristics and areas for improvement.
    """
    stations_info = da.get_mean_abs_error_each_station(df)
    print(f"\n~~~ {model} ~~~\n")
    show_me_mae_rmse(df, "TCDC", "V_N")
    print(f"Anzahl Modelldaten für den Bedeckungsgrad: {len(df)}")
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
              40,
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
    """
    Creates a violin plot comparing the distribution of the Mean Absolute Error (MAE) for different forecast
    periods within the specified model's predictions. This visualization helps to understand how the forecast
    accuracy changes with the length of the forecast period.

    :param df: The pandas DataFrame containing the forecast error data, including columns for forecast period
               ("Fcst_Minutes") and absolute error ("Absolute_Error").
    :param model: A string representing the name of the prediction model. This is used for titling the plot.
    :param show: A boolean indicating whether to display the plot immediately. Defaults to True.
    :param exportname: The filename for exporting the plot to an image file. If left as an empty string, the plot
                       will not be exported.

    Note: The function filters the input DataFrame to create subsets for 0, 60, and 120-minute forecast periods,
          then combines these subsets into a new DataFrame for plotting. The violin plot includes medians and
          provides an option to highlight median values. The plot is titled with the model name and labeled to
          reflect the forecast periods being compared. Custom fonts are set, and if specified, the plot can be
          displayed or exported.
    """
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
                                   custom_title: str = "",
                                   with_topographie: bool = False):
    """
    Generates a scatter plot to visualize the geographic distribution of DWD stations, with an option to
    color-code the stations based on the Mean Absolute Error (MAE) of a specified model's predictions. This
    function can be used to assess the geographic distribution of error in model predictions.

    :param df: The pandas DataFrame containing the station locations and, optionally, error metrics.
    :param show: A boolean indicating whether to display the plot. Defaults to True.
    :param exportname: The filename for exporting the plot. If empty, the plot is not exported.
    :param model: The name of the model being evaluated. Used in the plot title when displaying MAE.
    :param show_mean_abs_error: If True, the MAE is visualized on the plot; otherwise, only station locations are shown.
    :param custom_col_bar_label: Custom label for the color bar. If empty and showing MAE, defaults to "Absoluter Fehler
           [%]".
    :param custom_title: Custom title for the plot. Overrides the default title if provided.

    Note: The plot is created with a geographical map background to provide context for the station locations.
          Stations can be color-coded based on MAE to visualize the distribution of prediction accuracy across
          geographic locations. The function supports customization of plot aesthetics, including the title
          and color bar labeling, to accommodate different analysis focuses.
    """
    # calculation of MAE
    if show_mean_abs_error:
        df_data = df.groupby(COL_STATION_ID).agg({
            COL_LAT: "first",
            COL_LON: "first",
            COL_ABS_ERROR: "mean"
        }).reset_index()
        df_data.dropna(inplace=True)
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
    if with_topographie:
        m = Basemap(projection="cyl",
                    llcrnrlat=df_data[COL_LAT].min() - 1,
                    urcrnrlat=df_data[COL_LAT].max() + 1,
                    llcrnrlon=df_data[COL_LON].min() - 1,
                    urcrnrlon=df_data[COL_LON].max() + 1,
                    ax=ax)
        m.etopo()
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
    """
    Generates a scatter plot to compare the geographic distribution of DWD stations as represented in two
    different DataFrames. This visualization highlights the overlap and differences in station locations
    between the two datasets by plotting them with distinct markers and colors.

    :param df1: The pandas DataFrame containing the first set of station locations, including columns for
                latitude (COL_LAT) and longitude (COL_LON).
    :param df2: The pandas DataFrame containing the second set of station locations, structured similarly to df1.
    :param show: A boolean indicating whether to display the plot. Defaults to True.
    :param exportname: The filename for exporting the plot. If left as an empty string, the plot is not exported.
    :param legend_df1: The legend label for the first DataFrame's stations.
    :param legend_df2: The legend label for the second DataFrame's stations.
    :param custom_title: A custom title for the plot. If left as an empty string, a default title is used.

    Note: This function is useful for visually assessing the coverage and distribution of meteorological
          stations within and across datasets. Stations from df1 are plotted with default settings, while
          stations from df2 are highlighted in red with an 'x' marker for easy differentiation. The plot
          includes geographic context such as coastlines and borders for better location understanding.
    """
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
    """
    Generates scatter plots for cloud coverage comparison across two different areas between ICON-D2 and ICON-EU
    models and corresponding DWD station observations. The function loads and processes model and DWD data,
    creating four scatter plots in a 2x2 grid: each row represents a different area, and each column represents
    a different model.

    :param model_data_icon_d2_area_1: Path to the ICON-D2 model data for the first area.
    :param model_data_icon_eu_area_1: Path to the ICON-EU model data for the first area.
    :param dwd_data_area_1: Path to the DWD station observations for the first area.
    :param model_data_icon_d2_area_2: Path to the ICON-D2 model data for the second area.
    :param model_data_icon_eu_area_2: Path to the ICON-EU model data for the second area.
    :param dwd_data_area_2: Path to the DWD station observations for the second area.
    :param show: A boolean indicating whether to display the plots. Defaults to True.
    :param exportname: The filename for exporting the plots. If empty, the plots are not exported.

    Note: This function facilitates a visual comparison of model predictions against actual observations for
          cloud coverage, highlighting differences in prediction accuracy between models and across geographic
          areas. The plots are color-coded to represent varying degrees of cloud coverage, providing a clear visual
          representation of both model performance and observational data. Additional summary statistics are printed
          for each area to further assist in the comparison.
    """
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

    # draw areas and DWD-Stations
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

    # draw a custom legend  to represent the DWD-Stations
    legend = Legend(fig, [], [], loc="center", frameon=True,
                    bbox_to_anchor=Bbox.from_bounds(0.42, 0.4, 0.1, 0.1),
                    title="0 bis n  -  DWD-Station", labelspacing=0, borderpad=0.2)
    legend.get_title().set_color("red")
    fig.legends.append(legend)

    # Draw Plot
    cbar = fig.colorbar(sc, ax=[axs[0, 1], axs[1, 1]])
    cbar.set_label("Bedeckungsgrad [%]")
    cbar.set_ticks([0, 12.5, 25, 37.5, 50, 62.5, 75, 87.5, 100])
    plt.suptitle(f"Bedeckungsgrad der Modelle\n Datum: {date}", fontweight="bold")

    # Picture export as png because svg slow down word
    _show_and_export(plt, show, exportname)
    show_as_table("Area 1", dwd_locs_area_1, data_icon_d2_area_1, data_icon_eu_area_1)
    show_as_table("Area 2", dwd_locs_area_2, data_icon_d2_area_2, data_icon_eu_area_2)


def show_used_areas_dwd_stations(df_data: DataFrame,
                                 show: bool = True,
                                 exportname: str = ""):
    """
    Displays a map highlighting the geographic distribution of DWD stations and delineates specific areas of
    interest for comparison between ICON-D2 and ICON-EU model predictions. This visualization aids in understanding
    the spatial coverage of the analysis and locates the DWD stations within the defined areas.

    :param df_data: The pandas DataFrame containing the DWD station data, including longitude (COL_LON) and latitude
                    (COL_LAT) columns, and station IDs (COL_STATION_ID).
    :param show: A boolean indicating whether to display the plot. Defaults to True.
    :param exportname: The filename for exporting the plot. If left as an empty string, the plot is not exported.

    Note: Two areas of interest are specifically marked with red edges on the map to visualize the regions under
          study. This function provides a clear visual reference for the geographic scope of the model comparison
          analysis. The map includes geographical features such as coastlines, borders, and bodies of water for
          context, enhancing the interpretability of the station locations and study areas.
    """
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


def show_num_of_station_for_param(df: DataFrame,
                                  count_col: str,
                                  param_descr: str):
    """
    Calculates and prints the number of unique stations capable of measuring specific parameters, as described
    by `param_descr`. This is determined by dropping specified columns from the DataFrame and counting the unique
    station IDs that remain after removing rows with missing data.

    :param df: The pandas DataFrame containing station data, including a column for station IDs (COL_STATION_ID)
               and measurements for various parameters.
    :param count_col: ADefines the column from whose entries the stations are to be counted.
    :param param_descr: A descriptive string representing the parameters of interest for which the stations are
                        being counted. This description is used in the output message.

    Note: This function is useful for understanding the coverage of specific measurements across the network of
          stations. By dropping irrelevant columns and rows with missing data, it provides a count of stations
          that have non-missing data for the remaining measurements.
    """
    # create a filterlist
    drop_list = [col for col in df.columns if col not in [COL_DATE, COL_LAT, COL_LON, COL_STATION_ID, count_col]]
    tmp = df.drop(drop_list, axis=1).copy()
    tmp.dropna(inplace=True)
    print(f"Anzahl Stationen die nur {param_descr} messen können: {len(tmp[COL_STATION_ID].unique())}")


def calc_dwd_outliers(df: DataFrame) -> DataFrame:
    """
    Identifies DWD stations as outliers if their mean absolute error (MAE) is above a certain threshold.
    The function calculates the MAE value for each station to identify outliers with an MAE greater than 12.5%.

    :param df: The Pandas DataFrame with station data and absolute error measurements.

    :return: A Pandas DataFrame containing only the stations identified as outliers based on their MAE.

    Note: This function relies on a predefined threshold (12.5%) to identify outliers. Stations with an MAE
          above this threshold are considered outliers and are returned in the resulting DataFrame.
    """
    abs_error = da.get_mean_abs_error_each_station(df)
    return da.filter_dataframe_by_value(abs_error, COL_MEAN_ABS_ERROR, 12.5, True)


def load(filename: str) -> DataFrame:
    """
    Loads data from a specified file into a pandas DataFrame. The function supports loading from CSV and pickle
    ('.pkl') files. It automatically detects the file extension and applies the appropriate loading method.

    :param filename: The path to the file to be loaded.

    :return: A pandas DataFrame containing the loaded data.

    :raises FileExistsError: If the specified file does not exist.
    :raises ValueError: If the file extension is not supported (i.e., not `.csv` or `.pkl`).

    Note: For CSV files, a semicolon (`;`) is assumed as the separator, and a comma (`,`) as the decimal point.
          This function provides a unified interface for loading data, simplifying the process of working with
          different file formats.
    """
    if not os.path.exists(filename):
        raise FileExistsError
    filepath = Path(filename)
    if filepath.suffix == ".csv":
        return pd.read_csv(filename, sep=";", decimal=",", low_memory=False)
    else:
        raise ValueError("Unsupported file extension. Only *.csv are supported.")


# Initialisation
show_plot = False
dwd_params = ["V_N", "V_N_I", "D", "F", "RF_TU", "TT_TU", "P", "P0"]
if not os.path.exists(f"plots"):
    os.mkdir(f"plots")

# Loading CSV-Files
# df_d2_cloud_only = load(CSV_NAME_ICON_D2)
# df_eu_cloud_only = load(CSV_NAME_ICON_EU)
print("load CSV Files, please wait...\n")
df_d2_full = load(f"datas/all_param_data_ICON-D2.csv")
df_d2_cloud_only = _drop_param(df_d2_full, ["D", "F", "RF_TU", "TT_TU", "P", "P0"])
df_eu_full = load(f"datas/all_param_data_ICON-EU.csv")
df_eu_cloud_only = _drop_param(df_eu_full, ["D", "F", "RF_TU", "TT_TU", "P", "P0"])
df_dwd_solar = load(f"datas/solar_DWD_Stationlocations.csv")
print("loading done.\n")

# *** Data validation ***

# Show all used DWD-Locations
make_scatterplot_dwd_locations(df_d2_cloud_only, show_plot, f".\\plots\\ScatPlt_Verwendete_DWD-Stationen.svg")
print("start calculation and create graphics...\n")
make_scatterplot_dwd_locs_compare(df_d2_cloud_only, df_dwd_solar, show_plot,
                                  f".\\plots\\ScatPlt_Bedeckungsgrad_Strahlungsintensität.svg",
                                  "DWD Bedeckungsgrad",
                                  "DWD Strahlungsintensität",
                                  "Geografische Verteilung der DWD-Stationen zum"
                                  "\nMessen des Bedeckungsgrades und der Strahlungsintensität")

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

# Calculate Errors (RMSE, MAE, ME) and show it as text and as diagramm
da.calc_abs_error(df_d2_cloud_only, "TCDC", "V_N")
da.calc_abs_error(df_eu_cloud_only, "TCDC", "V_N")
show_error_metrics(df_d2_cloud_only, MODEL_ICON_D2, show_plot, 350000)
show_error_metrics(df_eu_cloud_only, MODEL_ICON_EU, show_plot, 350000)

# Show Errors between Forecasts
compare_fcst_error(df_d2_cloud_only, MODEL_ICON_D2, show_plot,
                   f".\\plots\\VioPlt_Fehler_zwischen_den_Prognosezeitpunkten_vom_ICON-D2.svg")
compare_fcst_error(df_eu_cloud_only, MODEL_ICON_EU, show_plot,
                   f".\\plots\\VioPlt_Fehler_zwischen_den_Prognosezeitpunkten_vom_ICON-EU.svg")

make_compare_hist_plt(df_d2_cloud_only[COL_ABS_ERROR], df_eu_cloud_only[COL_ABS_ERROR],
                      f"Verteilung des absoluten Fehlers von ICON-D2 und ICON-EU zu den DWD-Stationen",
                      f"Absoluter Fehler vom Bedeckungsgrad [%]",
                      f"Anzahl berechnete Modelldaten",
                      ["ICON_D2", "ICON-EU"],
                      show_plot,
                      f".\\plots\\HistPlt_Vergleich_MAE_Modelle_und_Stationen.svg")

# Show difference between MAE for each DWD-Station of ICON-D2 and ICON-EU
df_merged = pd.merge(
    df_d2_cloud_only,
    df_eu_cloud_only,
    on=[COL_STATION_ID, COL_LAT, COL_LON, COL_DATE],
    suffixes=('_d2', '_eu')
)
df_merged[COL_ABS_ERROR] = abs(df_merged[f'{COL_ABS_ERROR}_d2'] - df_merged[f'{COL_ABS_ERROR}_eu'])
result_columns = [COL_STATION_ID, COL_LAT, COL_LON, COL_DATE, COL_ABS_ERROR]
df_diff = df_merged[result_columns]
make_scatterplot_dwd_locations(df_diff, show_plot,
                               f".\\plots\\ScatPlt_Diff_MAE_vergleich_ICON-D2_EU.svg",
                               MODEL_ICON_D2, True,
                               "Differenz abs. Fehler vom Bedeckungsgrad [%]",
                               "Verteilung der Fehlerdifferenzen von ICON-D2 und ICON-EU\n"
                               "bezogen auf die DWD-Stationen",
                               True)

make_compare_proportion_lineplt(df_d2_cloud_only,
                                df_eu_cloud_only,
                                show_plot,
                                f".\\plots\\LinPlt_Differenz_Modell_DWD.svg")

# Show compare of MAE from ICON-D2 and ICON-EU
make_compare_violinplt(df_d2_cloud_only, MODEL_ICON_D2, df_eu_cloud_only, MODEL_ICON_EU, show_plot,
                       f".\\plots\\VioPlt_MAE_Vergleich_ICON-D2_ICON-EU.svg")


# *** Data evaluation ***
# only D2 #
# D2 - Calculate outliers in the data
dwd_outlier_d2 = calc_dwd_outliers(df_d2_cloud_only)
filtered_df = df_d2_full[df_d2_full[COL_STATION_ID].isin(dwd_outlier_d2[COL_STATION_ID])]

# collect all DWD-Stations who can measure all params
print(f"\n~~~ DWD-Stationsinformationen ~~~\n")
print(f"Anzahl aller Stationen (beinhaltet auch Stationshöhe): {len(df_d2_full[COL_STATION_ID].unique())}")
print(f"Anzahl Stationen die als Ausreißer gelten: {len(dwd_outlier_d2)}")

da.calc_abs_error(df_d2_full, "TCDC", "V_N")
show_num_of_station_for_param(df_d2_full, "V_N", "Bedeckungsgrad (V_N)")
v_n_i_df = df_d2_cloud_only.dropna()
measurment_counts = v_n_i_df['V_N_I'].value_counts()
print(f"    Anzahl Datenpunkte für V_N: {len(v_n_i_df)}")
print(f"    Davon wurden {measurment_counts['I'] / len(v_n_i_df) * 100:.2f} % durch ein Instrument aufgenommen.")
print(f"    Davon wurden {measurment_counts['P'] / len(v_n_i_df) * 100:.2f} % durch eine Person aufgenommen.")
print(f"    Für {measurment_counts['-999'] / len(v_n_i_df) * 100:.2f} % gab es keine Angaben.")

show_num_of_station_for_param(df_d2_full, "TT_TU", "Lufttemperatur (TT_TU)")
# tmp_df = df_d2_full[df_d2_full[COL_STATION_ID].isin(dwd_outlier_d2[COL_STATION_ID])]
# print(f"    Davon Ausreißer TT_TU: {len(tmp_df[COL_STATION_ID].unique())}")

show_num_of_station_for_param(df_d2_full, "RF_TU", "relative Feuchte (RF_TU)")
# tmp_df = df_d2_full[df_d2_full[COL_STATION_ID].isin(dwd_outlier_d2[COL_STATION_ID])]
# print(f"    Davon Ausreißer RF_TU: {len(tmp_df[COL_STATION_ID].unique())}")

show_num_of_station_for_param(df_d2_full, "P", "Luftdruck auf Meereshöhe NN (P)")
# tmp_df = df_d2_full[df_d2_full[COL_STATION_ID].isin(dwd_outlier_d2[COL_STATION_ID])]
# print(f"    Davon Ausreißer P: {len(tmp_df[COL_STATION_ID].unique())}")

show_num_of_station_for_param(df_d2_full, "F", "Windgeschwindigkeit (F)")
# tmp_df = df_d2_full[df_d2_full[COL_STATION_ID].isin(dwd_outlier_d2[COL_STATION_ID])]
# print(f"    Davon Ausreißer F: {len(tmp_df[COL_STATION_ID].unique())}")

# remove unused DWD-Param #
# remove pressure at Station_height
dwd_params.remove("P0")
# remove wind direction
dwd_params.remove("D")
# remove cloud coverage dwd Station
dwd_params.remove("V_N")
dwd_params.remove("V_N_I")
# add Station-Height
dwd_params.append(COL_STATION_HEIGHT)

# outside the loop, because V_N don't use for correlation analysis
print(f"\n~~~ V_N ~~~\n")
print(da.get_dwd_col_details(filtered_df, "V_N"))

# TODO: Filtern der dwd_station_all_param nach dem dwd_param & dwd_outlier_d2
# explorative dataanalysis for each dwd param
for dwd_param in dwd_params:
    print(f"\n~~~ {dwd_param} ~~~\n")
    # Contains only the values, who is filtered by dwd_param

    print(f"Anzahl Stationen (Ausreißer) von {dwd_param}: {len(filtered_df[COL_STATION_ID].unique())}")
    print(da.get_dwd_col_details(filtered_df, dwd_param))
    param_details = filtered_df[dwd_param].dropna()
    make_hist_qq_plot_compare(param_details,
                              f"Verteilung vom Parameter: {dwd_param}",
                              f"QQ-Plot vom Parameter: {dwd_param}",
                              _get_param_x_label(dwd_param),
                              "Anzahl Datenpunkte",
                              show_plot,
                              f".\\plots\\Hist_QQPlot_compare_DWD_Param_{dwd_param}.png")
    _, pvalue = da.normaltest(param_details)
    print(f"Normaltest von {dwd_param}: p-Value = {pvalue:.4f}")
    coef, pvaluer = da.calc_corr_coef(pvalue, df_d2_full, COL_ABS_ERROR, dwd_param)
    print_corr_results(pvalue, coef, pvaluer)

    # Shapiro - Data size must be < 5000
    # _, pvalue = da.shapiro(param_details)
    # print(f"Normaltest (shapiro) von {dwd_param}: p-Value = {pvalue:.4f}")

    # Anderson - Compare res.statistic with res.critical_values
    # res = da.anderson(param_details, dist='norm')
    # print(f"Normaltest (anderson) von: ")
    # print(f"Anderson-Darling-Teststatistik: {res.statistic}")
    # print(f"  Signifikanzniveaus:{res.significance_level}")
    # print(f"  Kritische Werte:   {res.critical_values}")
    # print(f"Teststatistik > Kritische Werte =  nicht normalverteilt")


print(f"\n~~~ Vergleich Instrumentmessung und Personenmessung - Bedeckungsgrad ~~~\n")
print(
    f"Hier werden nur RMSE, MAE und ME betrachtet, da ein Zusammenhang zwischen TCDC und V_N definitiv bestehen würde,"
    f" denn Beide beinhalten den Bedeckungsgrad.")
print(f"\nFehler: Instrumentmessung")
show_me_mae_rmse(v_n_i_df[v_n_i_df["V_N_I"] == "I"], "TCDC", "V_N")
print(f"\nFehler: Personenmessung")
show_me_mae_rmse(v_n_i_df[v_n_i_df["V_N_I"] == "P"], "TCDC", "V_N")

# calculate DWD-Station locations with idw radius von 0.04°
df_d2_idw_cloud_only = load(f".\\datas\\idw_data_ICON-D2.csv")
da.calc_abs_error(df_d2_idw_cloud_only, "TCDC", "V_N")
make_compare_violinplt(df_d2_cloud_only, "ICON-D2", df_d2_idw_cloud_only, "ICON-D2 mit IDW", show_plot,
                       f".\\plots\\VioPlt_MAE_Vergleich_ICON-D2_mit_ohne_IDW.svg")
