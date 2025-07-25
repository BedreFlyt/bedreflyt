import json
import sys
import requests
import random
import time
import argparse
import os

import numpy as np

host = "localhost"
url = f"http://{host}:8090/api/v1"
headers = {
    'Content-Type': 'application/json',
    'Accept': 'application/json'
}

neurosurgery_oslo_rooms = []

def create_room(room_number, capacity, ward, hospital, category_description):
    create_url = url + "/fuseki/rooms"
    payload = {
        "roomNumber": room_number,
        "capacity": capacity,
        "penalty": 0.0,
        "ward": ward,
        "hospital": hospital,
        "categoryDescription": category_description
    }
    response = requests.post(create_url, json=payload, headers=headers)
    if response.status_code == 200:
        print(f"Room {room_number} created successfully")
    else:
        print("Error creating room")

def create_rooms(payload):
    create_url = url + "/fuseki/rooms/multi"
    response = requests.post(create_url, json=payload, headers=headers)
    if response.status_code == 200:
        print(f"Rooms created successfully")
    else:
        print("Error creating room")

def create_rooms_for_neurosurgery_oslo():
    """Create a list of rooms for Neurosurgery in Oslo."""
    payload = []
    for room in neurosurgery_oslo_rooms:
        # set a capacity of a random number between 1 and 15
        capacity = random.randint(1, 15)
        payload.append({
            "roomNumber": room,
            "capacity": capacity,
            "penalty": 0.0,
            "ward": "Neurosurgery",
            "hospital": "OSL-RH",
            "categoryDescription": "Sengepost"
        })
    create_rooms(payload=payload)

def delete_room(room_number, ward_name, hospital_code):
    """Delete a room by its number, ward name, and hospital code."""
    delete_url = f"{url}/fuseki/rooms/{room_number}/{ward_name}/{hospital_code}"
    response = requests.delete(delete_url, headers=headers)
    if response.status_code == 200:
        print(f"Room {room_number} deleted successfully")
    else:
        print(f"Error deleting room {room_number}: {response.status_code}")

def delete_rooms_for_neurosurgery_oslo():
    """Delete all rooms for Neurosurgery in Oslo."""
    for room in neurosurgery_oslo_rooms:
        delete_room(room, "Neurosurgery", "OSL-RH")

def set_host(new_host):
    """Set the host for the API."""
    global host, url
    host = new_host
    url = f"http://{host}:8090/api/v1"
    print(f"Host set to {host}. URL is now {url}")

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
    response = requests.get(f"{url}/patient-allocations/simulated")
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

def get_capacity(ward_name, hospital_code):
    """Get the size of the allocation for a specific ward and hospital."""
    return sum([el["capacity"] for el in requests.get(f"{url}/fuseki/rooms/{ward_name}/{hospital_code}").json() if "capacity" in el])
    
iteration_times = []  # List to store iteration times
def test_allocation(mode: str, mean: int, std: int, iterations: int):
    patients = get_users()
    if not patients:
        print("No patients found")
        return
    
    diagnoses = get_diagnoses()
    if not diagnoses:
        print("No diagnoses found")
        return
    
    # Filter diagnosis based on mode
    if mode == "normal":
        diagnoses = diagnoses
    elif mode == "crisis":
        diagnoses = [{
                "diagnosisName": "C71.2"
            }, {
                "diagnosisName": "I60.1"
            }, {
                "diagnosisName": "I60.0"
            }]
    elif mode == 'medium-crisis':
        diagnoses = [{
                "diagnosisName": "C71.2"
            }, {
                "diagnosisName": "I60.1"
            }, {
                "diagnosisName": "I60.0"
            }]
        for diagnosis in random.sample(diagnoses, k=2):
            diagnoses.append({"diagnosisName": diagnosis["diagnosisName"]})
    else:
        print(f"Invalid mode: {mode}")
        assert False
    
    total_capacities = []
    total_allocations = []

    allocations_number = 0
    for iteration in range(iterations):  # Perform 10 iterations
        start_time = time.time()  # Start timing the iteration
        print(f"Starting iteration {iteration + 1}")

        # if iteration % 5 == 0:
        #     allocations_number = 0
        #     delete_allocations()
        #     print("Deleted all previous allocations")
        
        wards = get_wards()
        if not wards:
            print("No wards found")
            return
        
        capacities = {}
        for ward in wards:
            capacities[f"{ward['wardName']}_&_{ward['wardHospital']['hospitalCode']}"] = get_capacities(ward['wardName'], ward['wardHospital']['hospitalCode']) if ward['wardName'] == "Neurosurgery" else []
        
        for ward_key, ward_capacities in capacities.items():
            if not ward_capacities:
                print(f"No capacities found for ward {ward_key}")
                continue
            
            total_capacity = sum(ward_capacities)
            
            allocation_count = max(0, int(np.random.normal(mean, std, 1)[0]))  # Ensure allocation_count is non-negative
            selected_patients = random.sample(patients, min(allocation_count, len(patients)))
            
            allocations = []
            for patient in selected_patients:
                allocations.append({
                    "batch": int(iteration + 1),
                    "patientId": patient["patientId"],
                    "diagnosis": random.choice(diagnoses)["diagnosisName"]
                })
            
            
            ward_name, hospital_code = ward_key.split("_&_")
            # ward_name = "Neurosurgery"
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
            
            # os.system("redis-cli FLUSHALL")  # Clear Redis cache before each allocation
            response = requests.post(f"{url}/allocation/simulate", json=payload)
            if response.status_code == 200:
                print(f"Successfully allocated patients for ward {ward_name} in hospital {hospital_code}")
            else:
                print(f"Failed to allocate patients for ward {ward_name} in hospital {hospital_code}: {response.status_code}")
            
            # Save the total capacity and allocations for this ward
            total_capacities.append({
                "iteration": iteration + 1,
                "ward": ward_key,
                "total_capacity": get_capacity(ward_name, hospital_code)
            })
            total_allocations.append({
                "iteration": iteration + 1,
                "ward": ward_key,
                "allocations": len(get_allocations())
            })
        
        end_time = time.time()  # End timing the iteration
        iteration_duration = end_time - start_time
        iteration_times.append({"iteration": iteration + 1, "duration": iteration_duration})
        print(f"Iteration {iteration + 1} took {iteration_duration:.2f} seconds")

        # Wait for 30 seconds before the next iteration
        time.sleep(30)

    # Write the capacities, allocations, and iteration times to files
    output_data = {
        "capacities": total_capacities,
        "allocations": total_allocations
    }
    with open(f"allocation_results_{mode}_{mean}_{std}_{iterations}.json", "w") as file:
        json.dump(output_data, file, indent=4)

    with open(f"iteration_times_{mode}_{mean}_{std}_{iterations}.json", "w") as file:
        json.dump(iteration_times, file, indent=4)

    print("Execution completed. Results saved to 'allocation_results.json' and 'iteration_times.json'.")

if __name__ == "__main__":
    # Test the event generator with different modes
    
    parser = argparse.ArgumentParser("event-generator.py")
    parser.add_argument("--host", help="Host to connect to", type=str, default="localhost")
    parser.add_argument("--std", help="Standard deviation", type=int, default="1")
    parser.add_argument("--mean", help="Mean", type=int, default="5")
    parser.add_argument("--mode", help="Mode from [normal, crisis, medium-crisis]", type=str, default="normal")
    parser.add_argument("--iterations", help="Iterations", type=int, default="10")
    parser.add_argument("--time_steps", help="Time steps to run", type=int, default="10")
    parser.add_argument("--rooms", help="Create rooms for Neurosurgery in Oslo", type=int, default=0)
    args = parser.parse_args()
    
    if args.mode not in ["normal", "crisis", "medium-crisis", "variable"]:
        print("Usage: python event-generator.py [normal|crisis|medium-crisis|variable]")
        sys.exit(1)

    if args.host:
        set_host(args.host)

    for iteration in range(args.iterations):
        if args.rooms > 0:
            # if args.rooms > 70:
            #     print("You can only create up to 70 rooms for Neurosurgery in Oslo")
            #     sys.exit(1)
            for i in range(args.rooms):
                neurosurgery_oslo_rooms.append(330 + i)
            print(f"Creating {args.rooms} rooms for Neurosurgery in Oslo")
            create_rooms_for_neurosurgery_oslo()
            # os.system("redis-cli FLUSHALL")

        delete_allocations()
        print("Deleted all previous allocations")
        print("Waiting for 10 seconds to reset before starting the allocation test...")
        time.sleep(10)
        print("Starting allocation test")

        test_allocation(args.mode, args.mean, args.std, args.time_steps)

        delete_rooms_for_neurosurgery_oslo()

