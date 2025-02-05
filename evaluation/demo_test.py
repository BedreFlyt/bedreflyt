import requests
import json
import time
import concurrent.futures

host = "http://localhost:8090"

class ScenarioRequest: 
    def __init__(self, batch, patientId, treatmentName):
        self.batch = batch
        self.patientId = patientId
        self.treatmentName = treatmentName

def post_scenario_request(scenario_requests):
    url = host + '/api/simulation/room-allocation-smol'
    payload = {
        'scenario': [],
        'mode': "sample"
    }
    for el in scenario_requests:
        payload['scenario'].append({
            'batch': el.batch,
            'patientId': el.patientId,
            'diagnosis': el.treatmentName
        })
    data = payload
    response = requests.post(url, json=data)
    return response.content

scenarios = []
file = "scenarios.txt"

with open(file, 'r') as file:
    for line in file:
        batch, patient_id, treatment_name = line.strip().split(' ')
        patient_id = patient_id if patient_id != "None" else None
        treatment_name = treatment_name if treatment_name != "None" else None
        scenarios.append(ScenarioRequest(int(batch), patient_id, treatment_name))

def execute_in_thread(scenarios):
    return post_scenario_request(scenarios)

result = post_scenario_request(scenarios)
parsed_response = json.loads(result)

for (i, day) in enumerate(parsed_response):
    print("Day: ", i+1)
    if "error" in day:
        print(day)
        continue
    for entry in day:
        if "warning" in entry:
            continue
        elif "error" in entry:
            print(entry["error"])
            continue
        else:
            for k, v in entry.items():
                if patients:= v['patients']:
                    print(f"\t{k}")
                    print(f"\t\tGender: {v['gender']}")
                    ppPatients = [f"name: {patient['patientId']} age: {patient['age']}"
                            for patient in patients]
                    print(f"\t\t{ppPatients}")
