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
# Return maximum of a vector; error if empty
# https://stackoverflow.com/questions/67043494/max-and-min-of-a-set-of-variables-in-z3py
def Max(vs):
  m = vs[0]
  for v in vs[1:]:
    m = If(v > m, v, m)
  return m

class HospitalRoomAssignment:
    def __init__(self, no_rooms, capacities, room_distances, no_patients, genders, infectious, patient_distances, previous, mode):
        self.NO_ROOMS = no_rooms
        self.capacities = capacities
        self.room_distances = room_distances
        self.NO_PATIENTS = no_patients
        self.genders = genders
        self.infectious = infectious
        self.patient_distances = patient_distances
        self.previous = previous
        self.mode = mode

    def assign_rooms(self):
        assert len(self.capacities) == self.NO_ROOMS
        assert len(self.genders) == self.NO_PATIENTS
        assert len(self.infectious) == self.NO_PATIENTS
        assert len(self.patient_distances) == self.NO_PATIENTS
        assert len(self.room_distances) == self.NO_ROOMS
        assert len(self.previous) == self.NO_PATIENTS

        patients = [[ Bool('patient %s in room %s' % (i,j)) for j in range(self.NO_ROOMS)] for i in range(self.NO_PATIENTS)]
        genders = [Bool('gender room %s' %i ) for i in range(self.NO_ROOMS)]
        changes = [Bool('Patient %s stayed' %i ) for i in range(self.NO_PATIENTS)] # encodes which patient had to change stations

        s = Optimize()

        # Each patient in exactly one bed
        for patient in range(self.NO_PATIENTS):
            s.add(Sum(patients[patient]) == 1)

        # Room capacities are satisfied
        for room in range(self.NO_ROOMS):
            s.add(Sum([patients[i][room] for i in range(self.NO_PATIENTS)]) <= self.capacities[room])

        # Gender constraints
        for room in range(self.NO_ROOMS):
            for patient in range(self.NO_PATIENTS):
                s.add(Implies(patients[patient][room], self.genders[patient] == genders[room]))

        # Infectious patients
        for room in range(self.NO_ROOMS):
            for patient in range(self.NO_PATIENTS):
                s.add(Implies(
                        And(patients[patient][room], self.infectious[patient]), # patient in room is infectious
                            And([Not(patients[p][room]) for p in range(self.NO_PATIENTS) if p != patient]) # no other patient is in room
                            )
                )

        # Consider distance
        for patient in range(self.NO_PATIENTS):
            for room in range(self.NO_ROOMS):
                s.add(Implies(patients[patient][room], 
                            self.patient_distances[patient] >= self.room_distances[room])
                )

        # Encode previous assignment
        for patient in range(self.NO_PATIENTS):
            if self.previous[patient] != -1: # patient should keep bed-station only if they had one previously
                bed = self.previous[patient]
                if bed < len(patients[patient]):  # Check if bed index is within range
                    s.add(Or(patients[patient][bed], changes[patient]))
                else:
                    # Handle the case where bed index is out of range
                    print(f"Warning: Bed index {bed} out of range for patient {patient}")

        # Find assignment with few moved patients     
        if "c" in self.mode:
            h = s.minimize(Sum([changes[p] for p in range(self.NO_PATIENTS) if self.previous[p] != -1]))
        # too encode maximal number of changes
        # s.add(Sum([changes[p] for p in range(NO_PATIENTS) if Previous[p] != -1]) == 2)

        # Trying to minimize the average number of patients per room instead, but Z3 is very fickle about int/real expressions
        # room j is empty = Sum(patients[i][room] for i in range(self.NO_PATIENTS)) == 0
        # number of empty rooms = Sum(1 for room in rooms if Sum(patients[i][room] for i in range(self.NO_PATIENTS)) == 0)
        # average number of people in a room = (number of non-empty rooms) / (number of patients)
        # h = s.minimize(((self.NO_ROOMS - Sum([1 for room in range(self.NO_ROOMS) if Sum([patients[i][room] for i in range(self.NO_PATIENTS)]) == 0])) / self.NO_PATIENTS))

        # New plan: minimize the MAXIMAL number of patients in a room
        # number of patients in room j = Sum([patients[i][j] for i in range(self.NO_PATIENTS)])
        if "m" in self.mode:
            h = s.minimize(Max([Sum([patients[i][room] for i in range(self.NO_PATIENTS)]) for room in range(self.NO_ROOMS)]))


        print(s)
        print(s.check())

        if s.check() != sat:
            print("Model is unsat")
            print(s.unsat_core())
            return "Model is unsat", s.unsat_core()
        else:
            # Get model and format output
            m = s.model()
            print("Number of changes", s.lower(h))
            assignment = {str(i) : [] for i in range(self.NO_ROOMS)}
            room_gender = {str(i) : None for i in range(self.NO_ROOMS)}

            for v in genders:
                room_gender[str(v).split(" ")[2]] = m.eval(v, model_completion=True)
                
            for patient in patients:
                for v in patient:
                    if m.eval(v):
                        assigned_room = str(v).split(" ")[-1]
                        assigned_patient = str(v).split(" ")[1]
                        assignment[assigned_room].append(assigned_patient) 

            result = []
            # res_dic = {}
            for k in assignment:
                res_dic = {}
                res_dic[k] = {
                    'patients': assignment[k],
                    'gender': str(room_gender[str(k)])
                }
                result.append(res_dic)
                # result.append(f'Room {str(k)} is gender {room_gender[str(k)]} and holds patients {" ".join(assignment[k])}')
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
