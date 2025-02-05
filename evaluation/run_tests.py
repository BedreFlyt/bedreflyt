#!/usr/bin/env python3

import json
import requests
import argparse
import datetime
import subprocess

class ScenarioRequest:
    def __init__(self, batch, patientId, diagnosis):
        self.batch = batch
        self.patientId = patientId
        self.diagnosis = diagnosis

# factoring out repeated request code
def post_request(endpoint, scenario_requests, smtMode, mode=-1, risk=-1, repetitions=-1):
    scenario = [{'batch': el.batch,
                 'patientId': el.patientId,
                 'diagnosis': el.diagnosis}
                 for el in scenario_requests]
    payload = { 'scenario': scenario,
                'smtMode': smtMode,
               }
    if risk != -1:
        payload['risk'] = risk
    if repetitions != -1:
        payload['repeptitions'] = repetitions
    if mode != -1:
        payload['mode'] = mode

    response = requests.post(endpoint, json=payload)
    return response.content


def post_scenario_request(host, scenario_requests, mode, smtMode="changes"):
    url = host + '/api/simulation/room-allocation-smol'
    return post_request(url, scenario_requests, smtMode, mode)

def post_simulation_request(host, scenario_requests, repetitions, risk, smtMode="changes"):
    url = host + '/api/simulation/simulate-many'
    return post_request(url, scenario_requests, smtMode, risk, repetitions)

def post_global_request(host, scenario_requests, mode="worst", smtMode="changes"):
    url = host + '/api/simulation/room-allocation-global'
    return post_request(url, scenario_requests, smtMode, mode)

def getRooms(host):
    response = requests.get(host + "/api/fuseki/room/retrieve")
    return json.loads(response.content)

def countBedsOfCategory(rooms, category=3):
    return sum(room['capacity'] for room in rooms if room['roomCategory'] == category)

# returns true if there are non-cat 3 rooms
def roomsUpgradable(rooms):
    for room in rooms:
        if room["roomCategory"] != 3:
            return True
    return False

# finds the smallest non-category 3 room, upgrades it to category 3, and returns the new room list
def upgradeBeds(rooms, host):
    smallest = min([room for room in rooms if room["roomCategory"] < 3], key=lambda room: room['capacity'])
    updateReq = requests.patch(host + "/api/fuseki/room/update",
                               # it is important that the inner quotation marks are double, otherwise the API 403s
                               # do not ask how long this took to figure out
                               data=f'{{"roomNumber":{smallest["roomNumber"]}, "newRoom":3}}',
                               headers={"Content-Type": "application/json"})
    return getRooms(host)

def resetRooms(rooms, host):
    payload = [{"roomNumber":room['roomNumber'], "newRoom":room['roomCategory']} for room in roms]
    updateReq = requests.patch(host + "/api/fuseki/room/update-multi",
                               data = str(payload),
                               headers={"Content-Type": "application/json"})
    return updateReq.ok


def countUnsatDays(run):
    return sum([sum([1 for entry in day if "error" in entry]) for day in run])

def oneSimulation(host, scenario, risk, repetitions):
        simulation = json.loads(post_simulation_request(host, scenario, repetitions, risk))
        changes = [sim["changes"] for sim in simulation]
        unsatProportions = [countUnsatDays(sim["allocations"]) / len(sim["allocations"]) for sim in simulation]

        return {
            # 'risk': risk,
            'repetitions': repetitions,
            'avgChanges': sum(changes) / len(changes),
            'noDays': sum([len(sim['allocations']) for sim in simulation]) / len(simulation),
            'avgUnsatDays': sum(countUnsatDays(sim["allocations"]) for sim in simulation) / len(simulation),
            'avgUnsatProp': sum(unsatProportions) / len(unsatProportions)
        }

def run_simulations(host, scenario, repetitions, result_file):
    results = {}
    for risk in range(11):
        print(f"\tRunning one simulation with risk {risk*.1}")
        results[risk*.1] = oneSimulation(host, scenario, risk*.1, repetitions)

    with open(result_file, "w") as f:
        json.dump(results, f)

if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument('--host'
                        , default="http://localhost:8090"
                        , help="host address of simulation"
                        )
    parser.add_argument('--scenario'
                        , default="scenarios.txt"
                        , help="path to scenario file"
                        )
    parser.add_argument('--results'
                        , default="results"
                        , help="path to directory to store results"
                        )
    parser.add_argument('--repetitions'
                        , default=5
                        , help="number of reps per simulation [default: 5]"
                        )

    args = parser.parse_args()

    scenarios = []
    with open(args.scenario, 'r') as file:
        for line in file:
            batch, patient_id, diagnosis = line.strip().split(' ')
            patient_id = patient_id if patient_id != "None" else None
            diagnosis = diagnosis if diagnosis != "None" else None
            scenarios.append(ScenarioRequest(int(batch), patient_id, diagnosis))

    i = 0
    originial_rooms = rooms = getRooms(args.host)
    while roomsUpgradable(rooms):
        cat_3_beds = countBedsOfCategory(rooms, 3)
        print(f"Running simulation {i+1} with {cat_3_beds} beds of category 3")
        run_simulations(args.host, scenarios, args.repetitions, args.results + f"/{cat_3_beds}.json")
        rooms = upgradeBeds(rooms, args.host)
        i += 1

    print(f"Resetting room ontology with:")
    for r in original_rooms:
        print(f"\t{r}")
    if resetRooms(originial_rooms, args.host):
        print("✔")
    else:
        print("❌")
