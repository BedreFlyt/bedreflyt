from fastapi import FastAPI

from hospital import HospitalRoomAssignment
from pydantic import BaseModel

app = FastAPI()

class HospitalRoomResources(BaseModel):
    no_rooms: int
    capacities: list
    room_distances: list
    no_patients: int
    genders: list
    infectious: list
    patient_distances: list


@app.post("/api/solve")
def solve_hospital_assignment(request: HospitalRoomResources):
    hospital = HospitalRoomAssignment(request.no_rooms, request.capacities, request.room_distances, request.no_patients, request.genders, request.infectious, request.patient_distances)

    # Log the information arrived at the API
    print(f"Received request with {request.no_rooms} rooms, {request.no_patients} patients")
    print(f"Capacities: {request.capacities}, length: {len(request.capacities)}")
    print(f"Room distances: {request.room_distances}, length: {len(request.room_distances)}")
    print(f"Genders: {request.genders}, length: {len(request.genders)}")
    print(f"Infectious: {request.infectious}, length: {len(request.infectious)}")
    print(f"Patient distances: {request.patient_distances}, length: {len(request.patient_distances)}")

    assignment = hospital.assign_rooms()
    print(assignment)

    # return "Ok"
    return assignment

