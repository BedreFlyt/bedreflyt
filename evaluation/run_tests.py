#!/usr/bin/env python3

import json
import requests
import argparse
import datetime

import asyncio
import aiohttp

class ScenarioRequest:
    def __init__(self, batch, patientId, diagnosis):
        self.batch = batch
        self.patientId = patientId
        self.diagnosis = diagnosis

    def __str__(self):
        return f"{{batch={self.batch}, id={self.patientId}, diagnosis={self.diagnosis}}}"

# factoring out repeated request code
async def post_request(endpoint, scenario_requests, smtMode, mode=-1, risk=-1, repetitions=-1):
    scenario = [{"batch": el.batch,
                 "patientId": el.patientId,
                 "diagnosis": el.diagnosis}
                 for el in scenario_requests]
    payload = { "scenario": scenario,
                "smtMode": smtMode,
               }
    if risk != -1:
        payload["risk"] = risk
    if repetitions != -1:
        payload["repetitions"] = repetitions
    if mode != -1:
        payload["mode"] = mode

    async with aiohttp.ClientSession() as session:
        async with session.post(endpoint,
                                data=json.dumps(payload),
                                headers={"Content-type": "application/json"}
                                ) as response:
            if response.ok:
                return await response.json()
            else:
                raise Exception


async def post_scenario_request(host, scenario_requests, mode, smtMode="changes"):
    url = host + '/api/simulation/room-allocation-smol'
    return await post_request(url, scenario_requests, smtMode, mode)

async def post_simulation_request(host, scenario_requests, repetitions, risk, smtMode="changes"):
    url = host + '/api/simulation/simulate-many'
    return await post_request(url, scenario_requests, smtMode, risk=risk, repetitions=repetitions)

async def post_global_request(host, scenario_requests, mode="worst", smtMode="changes"):
    url = host + '/api/simulation/room-allocation-global'
    return await post_request(url, scenario_requests, smtMode, mode)

def getRooms(host):
    response = requests.get(host + "/api/fuseki/room/retrieve")
    return json.loads(response.content)

def countBedsOfCategory(rooms, category=3):
    return sum(room['capacity'] for room in rooms if room['roomCategory'] == category)

# returns true if there are non-cat 3 rooms
def roomsUpgradable(rooms):
    for room in rooms:
        if int(room["roomCategory"]) != 3:
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
    payload = [{"roomNumber":room['roomNumber'], "newRoom":room['roomCategory']} for room in rooms]
    updateReq = requests.patch(host + "/api/fuseki/room/update-multi",
                               data = json.dumps(payload),
                               headers={"Content-Type": "application/json"})
    return updateReq.ok


def countUnsatDays(run):
    return sum([sum([1 for entry in day if "error" in entry]) for day in run])

async def oneSimulation(host, scenario, risk, repetitions):
    print(f"\tRunning one simulation with risk {risk:.1f}")
    simulation = await post_simulation_request(host, scenario, repetitions, risk)
    changes = [sim["changes"] for sim in simulation]
    unsatProportions = [countUnsatDays(sim["allocations"]) / len(sim["allocations"]) for sim in simulation]

    return {
        'risk': risk,
        'avgChanges': sum(changes) / len(changes),
        'noDays': sum([len(sim['allocations']) for sim in simulation]) / len(simulation),
        'avgUnsatDays': sum(countUnsatDays(sim["allocations"]) for sim in simulation) / len(simulation),
        'avgUnsatProp': sum(unsatProportions) / len(unsatProportions)
    }

async def run_simulations(host, scenario, repetitions, result_file):
    sims = []
    for risk in range(11):
        sims.append(asyncio.create_task(oneSimulation(host, scenario, risk*.1, repetitions)))

    sim_results = await asyncio.gather(*sims, return_exceptions=False)

    results = {"scenario":[str(p) for p in scenario],
                "repetitions":repetitions,
                "simulations": sim_results}

    with open(result_file, "w") as f:
        json.dump(results, f, indent="")

    # if we have reached a threshold of beds where there are no more changes, we return True and break later
    return results["simulations"][10]["avgUnsatProp"] < 0.01

def main(host, original_rooms, scenario, results_file, repetitions):
    rooms = original_rooms
    i = 0
    while roomsUpgradable(rooms):
        cat_3_beds = countBedsOfCategory(rooms, 3)
        print(f"Running simulation {i+1} with {cat_3_beds} beds of category 3")
        if asyncio.run(run_simulations(host, scenarios, repetitions, results_file + f"/{cat_3_beds}.json")):
            break
        rooms = upgradeBeds(rooms, host)
        i += 1

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

    original_rooms = getRooms(args.host)
    try:
        main(args.host, original_rooms, scenarios, args.results, args.repetitions)
    finally:
        print(f"Resetting room ontology with:")
        for r in original_rooms:
            print(f"\t{r}")
        if resetRooms(original_rooms, args.host):
            print("✔")
        else:
            print("❌")

# ./run_tests.py --scenario new_scenario.txt --repetitions 10 --results nrec_results --host http://158.37.66.197:8090
