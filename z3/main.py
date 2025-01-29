from fastapi import FastAPI

from hospital import HospitalRoomAssignment, HospitalRoomAssignmentGlobal
from pydantic import BaseModel
from typing import List, Literal, Dict

app = FastAPI()

class HospitalRoomResources(BaseModel):
    no_rooms: int
    capacities: List[int]
    room_distances: List[int]
    no_patients: int
    genders: List[bool]
    infectious: List[bool]
    patient_distances: List[int]
    previous: List[int]
    mode: Literal["changes", "max"]


@app.post("/api/solve")
def solve_hospital_assignment(request: HospitalRoomResources):
    hospital = HospitalRoomAssignment(
        request.no_rooms, request.capacities, request.room_distances,
        request.no_patients, request.genders, request.infectious, request.patient_distances, request.previous,
        request.mode
    )

    # Log the information arrived at the API
    print(f"Received request with {request.no_rooms} rooms, {request.no_patients} patients")
    print(f"Capacities: {request.capacities}, length: {len(request.capacities)}")
    print(f"Room distances: {request.room_distances}, length: {len(request.room_distances)}")
    print(f"Genders: {request.genders}, length: {len(request.genders)}")
    print(f"Infectious: {request.infectious}, length: {len(request.infectious)}")
    print(f"Patient distances: {request.patient_distances}, length: {len(request.patient_distances)}")
    print(f"Previous: {request.previous}")

    assignment = hospital.assign_rooms()
    print(assignment)

    # return "Ok"
    return assignment

class GlobalQuery(BaseModel):
    capacities: List[int]
    room_distances: List[int]
    genders: Dict[str, bool]
    infectious: Dict[str, bool]
    patient_distances: List[Dict[str, int]]
    mode: Literal["changes", "max"]

@app.post("/api/solve-global")
def solve_global_assignment(request: GlobalQuery):
    assert(len(request.capacities) == len(request.room_distances))
    assert(len(request.genders) == len(request.infectious))

    no_rooms = len(request.capacities)
    no_patients = len(request.genders)
    no_days = len(request.patient_distances)

    total_days = [{name: {"Cat": cat, "Gender": request.genders[name], "Contagious": request.infectious[name]}
                   for (name, cat) in day.items()}
                  for day in request.patient_distances ]

    hospital_global = HospitalRoomAssignmentGlobal(
        no_rooms, request.capacities, request.room_distances,
        total_days, request.mode
    )


    print(f"Received global request for:\n\t{no_rooms} rooms\n\t{no_days} days\n\t{no_patients} unique patients")

    assignment = hospital_global.assign_rooms()
    print(assignment)

    return assignment
