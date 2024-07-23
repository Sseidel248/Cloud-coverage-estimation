"""
General Information:
______
- File name:      Rating_scheme.py
- Author:         Sebastian Seidel
- Date:           2024-07-19

Description:
______
Used to calculate the evaluation scheme of the data sources.
"""
# a - weighting spatial resolution
# b - weighting temporal resolution
# c - weighting used Lat. Lon
x_a = 0.6
x_b = 0.3
x_c = 0.1

# [spatial resolution [km], temporal resolution [min], used Lat. Lon]
dwd_station = [10, 60, 1]  # spatial resolution is different. Greater than and less than 10 km
icon = [13, 60, 1]
icon_eu = [6.5, 60, 1]
icon_d2 = [2.1, 60, 1]
dwd_sat = [2.5, 60, 0]
wetteronline_sat = [2.5, 180, 0]

rating_list = [dwd_station, icon, icon_eu, icon_d2, dwd_sat, wetteronline_sat]
rating_name = ["dwd_station", "icon", "icon_eu", "icon_d2", "dwd_sat", "wetteronline_sat"]

for elem, name in zip(rating_list, rating_name):
    # rating spatial resolution
    if elem[0] > 10:
        a = 0
    else:
        a = 1 - (elem[0]/10)

    # rating temporal resolution
    if elem[1] < 10:
        b = 1
    else:
        b = 10/elem[1]

    # rating used Lat. Lon
    c = elem[2]

    print(f"Rating parts of {name}: A={a:.3f}; B={b:.3f}; C={c:.3f}")
    e = a * x_a + b * x_b + c + x_c
    print(f"Rating of {name}: {e:.3f}\n")
