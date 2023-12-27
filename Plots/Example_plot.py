import numpy as np
import DataPlot as dPlt


# Cloud Data [eighth]
data_ref = np.array([8, 8, 7, 8, 7, 6, 3])
data_ref = data_ref/8 * 100  # [%]
# ICON-D2 Data [%]
data_model = np.array([100, 98, 92, 92, 88, 80, 64])
# Calc model accuracy
accuracy = dPlt.calc_accuracy(data_ref, data_model)
# Number of Datas > 90% accuracy
print(f"Number of Datapoints with Accuracy >= 90%: {np.sum(accuracy >= 90)}")
print(f"Total accuracy: {np.sum(accuracy >= 90)/len(accuracy) * 100:.2f} %")
# show box plot
dPlt.make_boxplot(accuracy,
                  title="Accuracy between ICON-D2 and measuring station",
                  y_label="Accuracy [%]",
                  value_name="ICON-D2")
# show 2 boxplots
accuracy2 = accuracy * 0.95
dPlt.make_2boxplots(accuracy, accuracy2,
                    title="Accuracy between ICON-D2 and measuring station",
                    y_label="Accuracy [%]",
                    value_names=["ICON-D2", "ICON-EU"])
