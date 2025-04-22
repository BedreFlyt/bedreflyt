import json
import sys
import requests
import random
import time
import argparse

import numpy as np

host = "localhost"
url = f"http://{host}:8090/api/v1"

def get_users():
    """Get all users."""
    response = requests.get(f"{url}/patients")
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Failed to get users: {response.status_code}")
        return []
    
def get_user(user_id):
    """Get a specific user by ID."""
    response = requests.get(f"{url}/patients/{user_id}")
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Failed to get user {user_id}: {response.status_code}")
        return None
    
def get_allocations():
    """Get all allocations."""
    response = requests.get(f"{url}/patient-allocations")
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Failed to get allocations: {response.status_code}")
        return []
    
def get_treatments():
    """Get all treatments."""
    response = requests.get(f"{url}/fuseki/treatments")
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Failed to get treatments: {response.status_code}")
        return []
    
def get_diagnoses():
    """Get all diagnoses."""
    response = requests.get(f"{url}/fuseki/diagnosis")
    if response.status_code == 200:
        diagnoses = response.json()
        # Remove G50.0 if present - we don't have a treatment for it
        diagnoses = [diagnosis for diagnosis in diagnoses if diagnosis.get("diagnosisName") != "G50.0"]
        return diagnoses
    else:
        print(f"Failed to get diagnoses: {response.status_code}")
        return []
    
def get_wards():
    """Get all wards."""
    response = requests.get(f"{url}/fuseki/wards")
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Failed to get wards: {response.status_code}")
        return []
    
def get_rooms():
    """Get all rooms."""
    response = requests.get(f"{url}/fuseki/rooms")
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Failed to get rooms: {response.status_code}")
        return []
    
def get_capacities(ward_name, hospital_code):
    rooms = get_rooms()
    if not rooms:
        return []
    # Filter rooms by ward name and hospital code
    filtered_rooms = [room for room in rooms if room['treatmentWard']['wardName'] == ward_name and room['hospital']['hospitalCode'] == hospital_code]
    if not filtered_rooms:
        print(f"No rooms found for ward {ward_name} in hospital {hospital_code}")
        return []
    # Get the capacities of the filtered rooms
    capacities = []
    for room in filtered_rooms:
        if 'capacity' in room:
            capacities.append(room['capacity'])
        else:
            print(f"No capacity found for room {room['roomName']}")
    if not capacities:
        print(f"No capacities found for ward {ward_name} in hospital {hospital_code}")
        return []
    return capacities

def delete_allocations():
    """Delete all allocations."""
    response = requests.delete(f"{url}/patient-allocations/all")
    if response.status_code == 200:
        print("Successfully deleted all allocations.")
    else:
        print(f"Failed to delete allocations: {response.status_code}")
    
def test_allocation(mode: str, mean: int, std: int, iterations: int):
    patients = get_users()
    if not patients:
        print("No patients found")
        return
    
    diagnoses = get_diagnoses()
    if not diagnoses:
        print("No diagnoses found")
        return
    
    assert False, "How to filter?"
    # TODO how to fiter?
    # Filter diagnosis based on mode
    if mode == "normal":
        diagnoses = [d for d in diagnoses if True]
    elif mode == "crisis":
        allocation_count = total_capacity
    elif mode == "variable":
        allocation_count = random.randint(int(total_capacity * 0.1), total_capacity)
    else:
        print(f"Invalid mode: {mode}")
        return
    
    total_capacities = []
    total_allocations = []

    allocations_number = 0
    for iteration in range(iterations):  # Perform 10 iterations
        print(f"Starting iteration {iteration + 1}")

        if iteration % 5 == 0:
            allocations_number = 0
            delete_allocations()
            print("Deleted all previous allocations")
        
        wards = get_wards()
        if not wards:
            print("No wards found")
            return
        
        capacities = {}
        for ward in wards:
            capacities[f"{ward['wardName']}_&_{ward['wardHospital']['hospitalCode']}"] = get_capacities(ward['wardName'], ward['wardHospital']['hospitalCode'])
        
        for ward_key, ward_capacities in capacities.items():
            if not ward_capacities:
                print(f"No capacities found for ward {ward_key}")
                continue
            
            total_capacity = sum(ward_capacities)
            
            allocation_count = np.random.normal(mean, std, 1) # one sample from random distribution with mean mean and standard deviation std
            selected_patients = random.sample(patients, min(allocation_count, len(patients)))
            
            allocations = []
            for patient in selected_patients:
                allocations.append({
                    "batch": int(iteration + 1),
                    "patientId": patient["patientId"],
                    "diagnosis": random.choice(diagnoses)["diagnosisName"]
                })
            
            
            ward_name, hospital_code = ward_key.split("_&_")
            ward_name = "Neurosurgery"
            print(f"Allocating {len(allocations)} patients for ward {ward_name} with total capacity {total_capacity}")
            allocations_number += len(allocations)
            payload = {
                "scenario": allocations,
                "mode": "worst",
                "smtMode": "changes",
                "wardName": ward_name,
                "hospitalCode": hospital_code,
                "iteration": iteration,
            }
            
            response = requests.post(f"{url}/allocation/allocate", json=payload)
            if response.status_code == 200:
                print(f"Successfully allocated patients for ward {ward_name} in hospital {hospital_code}")
            else:
                print(f"Failed to allocate patients for ward {ward_name} in hospital {hospital_code}: {response.status_code}")
            
            # Save the total capacity and allocations for this ward
            total_capacities.append({
                "iteration": iteration + 1,
                "ward": ward_key,
                "total_capacity": total_capacity
            })
            total_allocations.append({
                "iteration": iteration + 1,
                "ward": ward_key,
                "allocations": allocations_number
            })
        
        # Wait for 30 seconds before the next iteration
        time.sleep(30)
    
    # Write the capacities and allocations to a file
    output_data = {
        "capacities": total_capacities,
        "allocations": total_allocations
    }
    with open(f"allocation_results_{mode}.json", "w") as file:
        json.dump(output_data, file, indent=4)
    
    print("Execution completed. Results saved to 'allocation_results.json'.")
    
if __name__ == "__main__":
    # Test the event generator with different modes
    
    parser = argparse.ArgumentParser("event-generator.py")
    parser.add_argument("--std", help="Standard deviation", type=int, default="1")
    parser.add_argument("--mean", help="Mean", type=int, default="5")
    parser.add_argument("--mode", help="Mode", type=str, default="normal")
    parser.add_argument("--iterations", help="Iterations", type=int, default="10")
    args = parser.parse_args()
    
    if args.mode not in ["normal", "crisis", "variable"]:
        print("Usage: python event-generator.py [normal|crisis|variable]")
        sys.exit(1)

    test_allocation(args.mode, args.mean, args.std, args.iterations)
    
