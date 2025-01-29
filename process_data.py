#!/usr/bin/env python3
import json
import requests
import argparse

class ScenarioRequest:
    def __init__(self, batch, patientId, diagnosis):
        self.batch = batch
        self.patientId = patientId
        self.diagnosis = diagnosis

def post_scenario_request(host, scenario_requests, mode):
    url = host + '/api/simulation/room-allocation-smol'
    scenario = [{'batch': el.batch,
                 'patientId': el.patientId,
                 'diagnosis': el.diagnosis}
                 for el in scenario_requests]
    payload = {
        'scenario': scenario,
        'mode': mode,
    }
    response = requests.post(url, json=payload)
    return response.content

def post_simulation_request(host, scenario_requests, repetitions, risk):
    url = host + '/api/simulation/simulate-many'
    scenario = [{'batch': el.batch,
                 'patientId': el.patientId,
                 'diagnosis': el.diagnosis}
                 for el in scenario_requests]

    payload = { 'scenario': scenario, 'repetitions': repetitions, 'risk': risk}
    response = requests.post(url, json=payload)
    return response.content

def countUnsatDays(run):
    return sum([sum([1 for entry in day if "error" in entry]) for day in run])

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
                        , default="results.json"
                        , help="path to stored results (will be created if it does not exist)"
                        )
    parser.add_argument('--risk'
                        , default=.5
                        , help="proportion of runs with non-worst case scenario [default: 0.5]"
                        )
    parser.add_argument('--repetitions'
                        , default=10
                        , help="number of simulations [default: 10]"
                        )

    args = parser.parse_args()

    scenarios = []
    with open(args.scenario, 'r') as file:
        for line in file:
            batch, patient_id, diagnosis = line.strip().split(' ')
            patient_id = patient_id if patient_id != "None" else None
            diagnosis = diagnosis if diagnosis != "None" else None
            scenarios.append(ScenarioRequest(int(batch), patient_id, diagnosis))

    try:
        with open(args.results, 'r') as f:
            simulation = json.load(f)
        print(f"From {len(simulation)} simulations on file:")
    except:
        reps = args.repetitions
        risk = args.risk
        simulation = json.loads(post_simulation_request(args.host, scenarios, reps, risk))

        with open(args.results, 'w') as f:
            json.dump(simulation, f)
        print(f"Successfully ran {reps} simulations with risk {risk}")

    unsatProportions = [countUnsatDays(sim["allocations"]) / len(sim["allocations"]) for sim in simulation]
    changes = [sim["changes"] for sim in simulation]

    print(f"\tAverage proportion of unsatisfiable days: {sum(unsatProportions) / len(unsatProportions):.2f}")
    print(f"\tAverage number of days in scenario: {sum([len(sim['allocations']) for sim in simulation]) / len(simulation):.2f}")
    print(f"\tAverage number of changes: {sum(changes) / len(simulation):.2f}")

    worst_case = json.loads(post_scenario_request(args.host, scenarios, "worst"))
    print(f"Worst case:")
    print(f"\t{countUnsatDays(worst_case['allocations'])} unsatisfiable days")
    print(f"\t{len(worst_case['allocations'])} total days")
    print(f"\tProportion: {countUnsatDays(worst_case['allocations']) / len(worst_case['allocations']):.2f}")
    print(f"\tChanges: {worst_case['changes']}")

    common_case = json.loads(post_scenario_request(args.host, scenarios, "common"))
    print(f"Common case:")
    print(f"\t{countUnsatDays(common_case['allocations'])} unsatisfiable days")
    print(f"\t{len(common_case['allocations'])} total days")
    print(f"\tProportion: {countUnsatDays(common_case['allocations']) / len(common_case['allocations']):.2f}")
    print(f"\tChanges: {common_case['changes']}")
