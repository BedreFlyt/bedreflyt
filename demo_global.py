import requests
import json
import time
import concurrent.futures

host = "http://localhost:8090"

class ScenarioRequest: 
    def __init__(self, batch, patientId, diagnosis):
        self.batch = batch
        self.patientId = patientId
        self.diagnosis = diagnosis

def post_scenario_request(scenario_requests):
    url = host + '/api/simulation/room-allocation-global'
    scenario = [{'batch': el.batch,
                 'patientId': el.patientId,
                 'diagnosis': el.diagnosis}
                 for el in scenario_requests]

    payload = { 'scenario': scenario, 'mode':"common" }
    response = requests.post(url, json=payload)
    return response.content

if __name__ == "__main__":
    scenarios = []
    file = "example_scenario.txt"

    with open(file, 'r') as file:
        for line in file:
            batch, patient_id, diagnosis = line.strip().split(' ')
            patient_id = patient_id if patient_id != "None" else None
            diagnosis = diagnosis if diagnosis != "None" else None
            scenarios.append(ScenarioRequest(int(batch), patient_id, diagnosis))

    result = post_scenario_request(scenarios)
    parsed_response = json.loads(result)

    print(parsed_response)
