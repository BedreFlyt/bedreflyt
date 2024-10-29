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


@app.post("/solve")
def solve_hospital_assignment(request: HospitalRoomResources):
    hospital = HospitalRoomAssignment(request.no_rooms, request.capacities, request.room_distances, request.no_patients, request.genders, request.infectious, request.patient_distances)

    return hospital.assign_rooms()

