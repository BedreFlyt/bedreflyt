from z3 import *

# Nevrokirurgisk avd, OUS
# Model   Bedpost   info                                            Model 
# Roomnbr Romnr     Antall senger	Eget bad?	Seksjon/type rom    Category
# 0       2	        1*      	       x       	    Sengepost        1
# 1       3	        2       	       x	        Sengepost        1
# 2       4	        2	               x	        Sengepost        1
# 3       19	    3	               x	        Sengepost        1
# 4       21	    1*	               x	        Sengepost        1
# 5       22	    4	        	                Sengepost        1
# 6       36	    2	               x	        Sengepost        1
# 7       38	    2	               x	        Sengepost        1
# 8       23	    3	        	                Intermediær      2
# 9       28	    2	 	                        Intermediær      2
# 10      29	    1*	               x	        Intermediær      2
# 11      31	    3	               x	        Intermediær      2
# 12      6	        3	               x	        Overvåkning      3
# 13      43	    3	        	                Overvåkning      3
#
# hospital.py
class HospitalRoomAssignment:
    def __init__(self, no_rooms, capacities, room_distances, no_patients, genders, infectious, patient_distances):
        self.no_rooms = no_rooms
        self.capacities = capacities
        self.room_distances = room_distances
        self.no_patients = no_patients
        self.genders = genders
        self.infectious = infectious
        self.patient_distances = patient_distances

    def assign_rooms(self):
        assert len(self.capacities) == self.no_rooms
        assert len(self.genders) == self.no_patients
        assert len(self.infectious) == self.no_patients
        assert len(self.patient_distances) == self.no_patients
        assert len(self.room_distances) == self.no_rooms

        patients = [[Bool(f'patient {i} in room {j}') for j in range(self.no_rooms)] for i in range(self.no_patients)]
        genders = [Bool(f'gender room {i}') for i in range(self.no_rooms)]

        s = Solver()
        s.set(unsat_core=True)

        # Each patient in exactly one bed
        for patient in range(self.no_patients):
            s.assert_and_track(Sum(patients[patient]) == 1, f'patient assigned{patient}')

        # Room capacities are satisfied
        for room in range(self.no_rooms):
            s.assert_and_track(Sum([patients[i][room] for i in range(self.no_patients)]) <= self.capacities[room], f'room capacity {room}')

        # Gender constraints
        for room in range(self.no_rooms):
            for patient in range(self.no_patients):
                s.assert_and_track(Implies(patients[patient][room], self.genders[patient] == genders[room]), f'gender constraint room {room} patient {patient}')

        # Infectious patients
        for room in range(self.no_rooms):
            for patient in range(self.no_patients):
                s.assert_and_track(Implies(
                    And(patients[patient][room], self.infectious[patient]),  # patient in room is infectious
                    And([Not(patients[p][room]) for p in range(self.no_patients) if p != patient])  # no other patient is in room
                ), f'infectious patient {patient} room {room}')

        # Consider distance
        for patient in range(self.no_patients):
            for room in range(self.no_rooms):
                s.assert_and_track(Implies(patients[patient][room],
                                           self.patient_distances[patient] >= self.room_distances[room]), f'distance patient {patient} room {room}')

        if s.check() != sat:
            return "Model is unsat", s.unsat_core()
        else:
            # Get model and format output
            m = s.model()
            assignment = {str(i): [] for i in range(self.no_rooms)}
            room_gender = {str(i): None for i in range(self.no_rooms)}

            for v in genders:
                room_gender[str(v).split(" ")[2]] = m.eval(v, model_completion=True)

            for patient in patients:
                for v in patient:
                    if m.eval(v):
                        assigned_room = str(v).split(" ")[-1]
                        assigned_patient = str(v).split(" ")[1]
                        assignment[assigned_room].append(assigned_patient)

            result = []
            for k in assignment:
                result.append(f'Room {str(k)} is gender {room_gender[str(k)]} and holds patients {" ".join(assignment[k])}')
            return result

# # Example usage:
if __name__ == "__main__":
    # This we get from the DB
    no_rooms = 17
    capacities = [2, 1, 2, 3, 1, 4, 4, 2, 3, 2, 1, 3, 3, 3, 1, 1, 1]
    room_distances = [1, 1, 1, 1, 1, 1, 1, 1, 2, 2, 2, 2, 3, 3, 4, 4, 4]

    # This we get from ABS
    # no_patients = 31
    # genders = [False] * 31
    # infectious = [False] * 31
    # patient_distances = [1] * 23 + [3] * 4 + [2] * 4

    # hospital = HospitalRoomAssignment(no_rooms, capacities, room_distances, no_patients, genders, infectious, patient_distances)
    # result = hospital.assign_rooms()
    # print(result)

    patientsData = {
        'einar': {
            'gender': True,
            'infectious': False,
        },
        'rudi': {
            'gender': True,
            'infectious': False,
        },
        'lizeth': {
            'gender': False,
            'infectious': True,
        },
        'laura': {
            'gender': False,
            'infectious': False,
        },
        'riccardo': {
            'gender': True,
            'infectious': False,
        }
    }

    # Read file
    with open('abs.txt', 'r') as f:
        # Read all content
        content = f.read()


    # EB - Split content by "------"
    scenarios = content.strip().split('------')

    # Iterate over scenarios
    for scenario in scenarios:
        if (len(scenario) == 0):
            continue

        # Split scenario by newline
        lines = scenario.split('\n')

        genders = []
        infectious = []
        patient_distances = []

        for line in lines:
            patients = line.split(",")

            if len(patients) != 2:
                continue

            genders.append(patientsData[patients[0]]['gender'])
            infectious.append(patientsData[patients[0]]['infectious'])
            patient_distances.append(int(patients[1]))

        no_patients = len(genders)

        print(genders)
        print(infectious)
        print(patient_distances)

        hospital = HospitalRoomAssignment(no_rooms, capacities, room_distances, no_patients, genders, infectious, patient_distances)
        result = hospital.assign_rooms()
        print(result)
