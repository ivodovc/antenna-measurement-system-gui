import os

# Load csv raw data reported by stm32
def load_data(filename):
    x_vals = []
    y_vals = []
    with open(filename, "r") as file:
        for line in file:
            graph_points = line.rstrip().split(";")
            for point in graph_points:
                if (len(point)<1):
                    continue
                x, y, voltage = point.split(",")
                try:
                    x_vals.append(int(x))
                    y_vals.append(int(y))
                except ValueError as e:
                    #print("error:", e)
                    pass
    return x_vals, y_vals

def calibrate():
    #25 az 2400 MHz
    for freq in range(25,2400):
        priamo_0db = get_value_at_freq("data_0dB_priamo.txt", freq)
        priamo_50Ohm = get_value_at_freq("data_50ohm.txt", freq)

        at_db = [0,2,4,6]
        at_filenames = ["data_" + str(db) + "dB_atenuator.txt" for db in at_db]
        at_hodnoty = [get_value_at_freq(filename, freq) for filename in at_filenames]
        cal_hodnoty = [None] * len(at_hodnoty)
        # rozdiel 0db priamo a 0db at
        rozdiel = at_hodnoty[0] - priamo_0db
        for i in range(len(at_db)):
            db = at_db[i]
            hodnota = at_hodnoty[i]
            cal_hodnota = hodnota-rozdiel
            cal_hodnoty[i] = cal_hodnota
            cal_values[str(db) + "dB_cal"][0].append(freq)
            cal_values[str(db) + "dB_cal"][1].append(cal_hodnota)

def calibrate_linear():
    #25 az 2400 MHz
    for freq in range(25,2000):
        priamo_0db = get_value_at_freq("data_0dB_priamo.txt", freq)
        priamo_50Ohm = get_value_at_freq("data_50ohm.txt", freq)
        at_12_db = get_value_at_freq("data_12dB_atenuator.txt", freq)
        at_0_db = get_value_at_freq("data_0dB_atenuator.txt", freq)

        at_db = [0,2,4,6,8,10,12]
        at_filenames = ["data_" + str(db) + "dB_atenuator.txt" for db in at_db]
        at_hodnoty = [get_value_at_freq(filename, freq) for filename in at_filenames]
        cal_hodnoty = [None] * len(at_hodnoty)
        # rozdiel 0db priamo a 0db at
        rozdiel = at_hodnoty[0] - priamo_0db
        for i in range(len(at_db)):
            db = at_db[i]
            hodnota = at_hodnoty[i]
            #print(freq)
            #print(at_12_db, at_0_db, hodnota)
            if (at_12_db - at_0_db)>0:
                norm_at = (hodnota - at_0_db) / (at_12_db - at_0_db)
            else:
                 norm_at = (hodnota - at_0_db) / 1
            cal_hodnota = priamo_0db + ((priamo_50Ohm - priamo_0db) * norm_at)
            cal_hodnoty[i] = cal_hodnota
            cal_values[str(db) + "dB_cal"][0].append(freq)
            cal_values[str(db) + "dB_cal"][1].append(cal_hodnota)

cal_values = {}
cal_values["0dB_cal"] = [list(), list()]
cal_values["2dB_cal"] = [list(), list()]
cal_values["4dB_cal"] = [list(), list()]
cal_values["6dB_cal"] = [list(), list()]
cal_values["8dB_cal"] = [list(), list()]
cal_values["10dB_cal"] = [list(), list()]
cal_values["12dB_cal"] = [list(), list()]
values = {}
def load_data_global():
    for file in os.listdir("vsetko"):
             if file.endswith(".txt"):
                x, y = load_data("vsetko/" + str(file))
                name = str(file)
                values[str(file)] = [x,y]

# find index of requested frequency and return y value for that frequency
def get_value_at_freq(filename, freq):
    all_values = values[filename]
    index = all_values[0].index(freq)
    return  all_values[1][index]
