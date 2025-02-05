#!/usr/bin/env python3

import random

with open("patient_names/patients_3000.txt", "r") as name_file:
    names = set([name.rstrip() for name in name_file])
diagnoses = [d["diagnosisName"] for d in [{"diagnosisName":"D320"},{"diagnosisName":"S065"},{"diagnosisName":"D352"},{"diagnosisName":"G912"},{"diagnosisName":"M500"},{"diagnosisName":"I60"},{"diagnosisName":"G500"},{"diagnosisName":"I601"},{"diagnosisName":"C713"},{"diagnosisName":"I671"}]]

patients_per_day = 5

with open ("new_scenario.txt", "w") as scenario_file:
    day = 0
    while True:
        for _ in range(patients_per_day):
            scenario_file.write(f"{day} {names.pop()} {random.choice(diagnoses)}\n")
            day += 1
            if len(names) == 0:
                break
        else:
            continue
        break
