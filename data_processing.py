import os
import csv
from datetime import datetime

DATE_FORMAT = "%d-%m-%Y-%H-%M"
SUBFOLDER_PATH="./ref_data/"

# reads data from filename
def load_data_csv(filename):
    data_x = []
    data_y = []
    #fullname = SUBFOLDER_PATH + filename
    with open(filename, newline='') as f:
        reader = csv.reader(f)
        for row in reader:
            if (row[0]=='frequency'):
                date = datetime.strptime(row[2], DATE_FORMAT)
                print(date)
                continue
            x = int(row[0])
            y = int(row[1])
            data_x.append(x)
            data_y.append(y)
    return data_x, data_y

# Save data in format (x_vals, y_vals) to csv file specified by filename
def save_data_csv(filename, data):
    with open(filename, "w", newline='') as file:
        writer = csv.writer(file)
        datenow_str = datetime.now().strftime(DATE_FORMAT)
        writer.writerow(("frequency", "ADC value", datenow_str))
        for i in range(len(data[0])):
            row = data[0][i], data[1][i]
            writer.writerow(row)

def get_pwrtext(pwr):
    if pwr=="1":
        return "-4dBm"
    elif pwr=="2":
        return "-1dBm"
    elif pwr=="3":
        return "2dBm"
    elif pwr=="4":
        return "5dBm"
    else:
        print("Bad pwr in get_pwrtext")
        return None

def check_filename_available(filename, pwr):
    # checks if filename is a valid filename and if there is no other same file
    if (filename.split(".")[-1] != "csv"):
        filename += ".csv"
    pwrtext = get_pwrtext(pwr)
    if (pwrtext==None):
        return
    pwr_subfolder = pwrtext + "/"
    if (filename in os.listdir(SUBFOLDER_PATH+pwr_subfolder)):
        # collision
        #recursion but whatever
        newname =  "RENAMED_" + filename
        return check_filename_available(newname, pwr).split(".")[0]
    else:
        return filename.split(".")[0]

# return all reference data for specified power
def get_all_references_for_pwr(pwr):
    pwrtext = get_pwrtext(pwr)
    if (pwrtext==None):
        return
    pwr_subfolder = pwrtext + "/"
    full_subfolder = SUBFOLDER_PATH + pwr_subfolder
    files = os.listdir(full_subfolder)
    for file in files:
        # first check if file is csv file
        extension = file.split(".")[-1]
        if extension=="csv":
            if False:#file in globalCache[pwrtext]:
                # do not load
                pass
            else:
                # need to load file into cache
                data = load_data_csv(full_subfolder + file)
                globalCache[pwrtext][file] = data
    return globalCache[pwrtext]

# saves reference
def save_reference(refname, pwr, data):
    pwrtext = get_pwrtext(pwr)
    if (pwrtext==None):
        return
    if (refname==None):
        return
    pwr_subfolder = pwrtext + "/"
    fullname = SUBFOLDER_PATH + pwr_subfolder + refname
    # if user didnt enter csv after name add csv, otherwise let it be
    if (refname.split(".")[-1] != "csv"):
        fullname += ".csv"
    save_data_csv(fullname, data)

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

def trend_fun(x):
    #https://math.stackexchange.com/questions/1012707/how-to-invert-a-simple-exponential-growth-formula
    b = 1.1
    a = 1
    p = 9.3
    y = b-(1+p)**(x-a)
    return y

# get reflection coefficient
def get_RC(freq, ADC_reading, pwr_level):
    pwr_txt = str(pwr_level)
    short_data = get_cal_data("short", pwr_txt)
    match_data = get_cal_data("match", pwr_txt)
    # get short value at freq
    shot_val_i = short_data[0].index(freq)
    match_val_i = match_data[0].index(freq)
    short_val = short_data[1][shot_val_i]
    match_val = match_data[1][match_val_i]
    actual_val = ADC_reading
    # simplest algorithm get linear distance between match_val and short_val
    linear_val = ((actual_val-short_val)/(match_val-short_val))
    ref_coefficient = trend_fun(linear_val)
    #if ref_coefficient>1:
    #    ref_coefficient = 1
    #if ref_coefficient<0:
    #    ref_coefficient = 0
    return ref_coefficient

def get_SWR(freq, ADC_reading, pwr_level):
    rc = get_RC(freq, ADC_reading, pwr_level)
    SWR = (1+rc)/(1-rc)
    if SWR>10:
        SWR=10
    return SWR

globalCache = dict()
globalCache = {"5dBm": {},
               "2dBm": {},
                "-1dBm": {},
                "-4dBm": {}}