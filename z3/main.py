from fastapi import FastAPI, HTTPException

from hospital import HospitalRoomAssignment, HospitalRoomAssignmentGlobal
from pydantic import BaseModel
from typing import List, Literal, Dict
from datetime import datetime

import os

from concurrent.futures import ThreadPoolExecutor

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
    penalties: List[int] = []
    contagious_allowed: List[bool] = []

executor = ThreadPoolExecutor(max_workers=int(os.getenv("MAX_WORKERS", 4)))

def solve_assignment(request):
    hospital = HospitalRoomAssignment(
        request.no_rooms, request.capacities, request.room_distances,
        request.no_patients, request.genders, request.infectious, request.patient_distances, request.previous,
        request.mode, request.penalties, request.contagious_allowed
    )

    return hospital.assign_rooms()


@app.post("/api/solve")
async def solve_hospital_assignment(request: HospitalRoomResources):
    print(f"Received a request at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    future = executor.submit(solve_assignment, request)
    result = future.result()

    print(f"Finished processing request at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # return "Ok"
    return result

class GlobalQuery(BaseModel):
    capacities: List[int]
    room_distances: List[int]
    genders: Dict[str, bool]
    infectious: Dict[str, bool]
    patient_distances: List[Dict[str, int]]
    mode: Literal["changes", "max"]

def solve_assignment_global(request: HospitalRoomAssignmentGlobal):

    return request.assign_rooms()

@app.post("/api/solve-global")
async def solve_global_assignment(request: GlobalQuery):
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

    future = executor.submit(solve_assignment_global, hospital_global)
    result = future.result()

    # assignment = hospital_global.assign_rooms()
    # print(assignment)
    

    return result

class RoomStructure(BaseModel):
    currentFreeCapacity: int
    incomingPatients: int
    capacities: List[int]
    penalties: List[int]

def room_opener(request: RoomStructure):
    from room_opener import RoomOpener

    room_opener = RoomOpener(
        request.currentFreeCapacity,
        request.incomingPatients,
        request.capacities,
        request.penalties
    )

    opened_rooms, total_penalty = room_opener.find_appropriate_rooms()

    return opened_rooms, total_penalty

@app.post("/api/room-opener")
async def room_opener_endpoint(request: RoomStructure):
    print(f"Received room opener request at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    future = executor.submit(room_opener, request)
    rooms, _ = future.result()

    print(f"Finished processing room opener request at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    if rooms is None:
        raise HTTPException(status_code=404, detail="No appropriate rooms found")

    return rooms