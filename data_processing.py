"""
    Antenna Measurement system GUI control program
    Copyright (C) 2023

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <https://www.gnu.org/licenses/>
"""

import os
import csv
from datetime import datetime

DATE_FORMAT = "%d-%m-%Y-%H-%M"
SUBFOLDER_PATH = "./ref_data/"


# reads data from filename
def load_data_csv(filename):
    data_x = []
    data_y = []
    # fullname = SUBFOLDER_PATH + filename
    with open(filename, newline='') as f:
        reader = csv.reader(f)
        for row in reader:
            if (row[0] == 'frequency'):
                # skip first row
                continue
            x = float(row[0])
            y = float(row[1])
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
    if pwr == "1":
        return "-4dBm"
    elif pwr == "2":
        return "-1dBm"
    elif pwr == "3":
        return "2dBm"
    elif pwr == "4":
        return "5dBm"
    else:
        print("Bad pwr in get_pwrtext")
        return None


def check_filename_available(filename, pwr):
    # checks if filename is a valid filename and if there is no other same file
    if (filename.split(".")[-1] != "csv"):
        filename += ".csv"
    pwrtext = get_pwrtext(pwr)
    if (pwrtext is None):
        return
    pwr_subfolder = pwrtext + "/"
    if (filename in os.listdir(SUBFOLDER_PATH+pwr_subfolder)):
        # collision
        # recursion but whatever
        newname = "RENAMED_" + filename
        return check_filename_available(newname, pwr).split(".")[0]
    else:
        return filename.split(".")[0]


# return all reference data for specified power
def get_all_references_for_pwr(pwr):
    pwrtext = get_pwrtext(pwr)
    if (pwrtext is None):
        return
    pwr_subfolder = pwrtext + "/"
    full_subfolder = SUBFOLDER_PATH + pwr_subfolder
    files = os.listdir(full_subfolder)
    for file in files:
        # first check if file is csv file
        extension = file.split(".")[-1]
        if extension == "csv":
            data = load_data_csv(full_subfolder + file)
            globalCache[pwrtext][file] = data
    return globalCache[pwrtext]


# saves reference
def save_reference(refname, pwr, data):
    pwrtext = get_pwrtext(pwr)
    if (pwrtext is None):
        return
    if (refname is None):
        return
    pwr_subfolder = pwrtext + "/"
    fullname = SUBFOLDER_PATH + pwr_subfolder + refname
    # if user didnt enter csv after name add csv, otherwise let it be
    if (refname.split(".")[-1] != "csv"):
        fullname += ".csv"
    save_data_csv(fullname, data)


def trend_fun(x):
    # https://math.stackexchange.com/questions/1012707/how-to-invert-a-simple-exponential-growth-formula
    b = 1.1
    a = 1
    p = 9.3
    y = b-(1+p)**(x-a)
    return y


globalCache = dict()
globalCache = {"5dBm": {},
               "2dBm": {},
               "-1dBm": {},
               "-4dBm": {}}
