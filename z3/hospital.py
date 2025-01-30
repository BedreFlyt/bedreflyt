from z3 import *
import random 
random.seed(42)

import datetime

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
                            self.patient_distances[patient] <= self.room_distances[room])
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
            h = s.minimize(Sum([changes[p] for p in range(self.NO_PATIENTS)]))
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
            max_patients = Int('maximal patients')
            for room in range(self.NO_ROOMS):
                s.add(Sum([patients[i][room] for i in range(self.NO_PATIENTS)]) <= max_patients)
            h = s.minimize(max_patients)


        print(s.check())

        if s.check() != sat:
            print("Model is unsat")
            print(s.unsat_core())
            return "Model is unsat", s.unsat_core()
        else:
            # Get model and format output
            m = s.model()
            assert s.lower(h) == s.upper(h)
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
            for k in assignment:
                res_dic = {}
                res_dic[k] = {
                    'patients': assignment[k],
                    'gender': str(room_gender[str(k)])
                }
                result.append(res_dic)
                # result.append(f'Room {str(k)} is gender {room_gender[str(k)]} and holds patients {" ".join(assignment[k])}')
            return {"allocations": result, "changes": s.lower(h).as_long()}


class HospitalRoomAssignmentGlobal:
    def __init__(self, no_rooms, capacities, room_categories, patients, mode):
        # no_patients, genders, infectious, patient_distances, previous, mode):
        
        # fixed
        self.NO_ROOMS = no_rooms
        self.capacities = capacities
        self.room_distances = room_categories
        
        # day-depending
        self.patients = patients
        
        # self.no_patients = no_patients
        # self.genders = genders
        # self.infectious = infectious
        # self.patient_distances = patient_distances
        
        # self.previous = previous
        self.mode = mode
        
        self.days = range(len(patients))

    def assign_rooms(self):
        
        start = datetime.datetime.now()
        
        assert len(self.capacities) == self.NO_ROOMS
        assert len(self.room_distances) == self.NO_ROOMS
        
        # for d in range(self.days):
        #     assert len(self.genders[d]) == self.no_patients[d]
        #     assert len(self.infectious[d]) == self.no_patients[d]
        #     assert len(self.patient_distances[d]) == self.no_patients[d]
        #     assert len(self.previous[d]) == self.no_patients[d]

        # TODO set patients to ints
        # add sets of constraints?
        print("Construct variables")
        patients = [{patient : [Bool('patient %s in room %s on day %s' % (patient, room, day)) for room in range(self.NO_ROOMS)] for patient in self.patients[day]} for day in self.days]
        # patients = [[Int('patient %s on day %s' % (patient, day)) for patient in range(self.no_patients[day])] for day in range(self.days)]
        genders = [[Bool('gender room %s on day %s' %(i, day) ) for i in range(self.NO_ROOMS)] for day in self.days]
        changes = [{patient : Bool('Patient %s stayed on day %s' %(patient, day) ) for patient in self.patients[day]} for day in self.days]# encodes which patient had to change stations

        s = Optimize()

        print("Start building models")
        
        print("Patients")
        start = datetime.datetime.now()
        # Each patient in exactly one bed
        for day in self.days:
            for patient in self.patients[day]:
                s.add(Sum(patients[day][patient]) == 1)
        
        # constraints = [Sum(patients[day][patient]) == 1 for day in range(self.days) for patient in range(self.no_patients[day])]
        # s.add(constraints)
        print((datetime.datetime.now()-start).total_seconds())
        
        print("Rooms")
        start = datetime.datetime.now()
        # Room capacities are satisfied
        for day in self.days:
            for room in range(self.NO_ROOMS):
                s.add(Sum([patients[day][i][room] for i in self.patients[day]]) <= self.capacities[room])
        print((datetime.datetime.now()-start).total_seconds())

        print("Gender")
        start = datetime.datetime.now()
        # Gender constraints
        for day in self.days:
            for room in range(self.NO_ROOMS):
                for patient in self.patients[day]:
                    s.add(Implies(patients[day][patient][room], self.patients[day][patient]['Gender'] == genders[day][room]))
        print((datetime.datetime.now()-start).total_seconds())

        print("Infectious")
        start = datetime.datetime.now()
        # Infectious patients
        for day in self.days:
            for room in range(self.NO_ROOMS):
                for patient in self.patients[day]:
                    if self.patients[day][patient]['Contagious']:
                        s.add(Implies(
                            patients[day][patient][room], # patient in room is infectious
                                And([Not(patients[day][p][room]) for p in self.patients[day] if p != patient]) # no other patient is in room
                                )
                        )
                    # s.add(Implies(
                    #         And(patients[day][patient][room], self.infectious[day][patient]), # patient in room is infectious
                    #             And([Not(patients[day][p][room]) for p in range(self.no_patients[day]) if p != patient]) # no other patient is in room
                    #             )
                    # )
        print((datetime.datetime.now()-start).total_seconds())

        print("Distance")
        start = datetime.datetime.now()
        # Consider distance
        for day in self.days:
            for patient in self.patients[day]:
                for room in range(self.NO_ROOMS):
                    s.add(Implies(patients[day][patient][room], 
                                self.patients[day][patient]['Cat'] <= self.room_distances[room])
                    )
        print((datetime.datetime.now()-start).total_seconds())

        print("Previous")
        start = datetime.datetime.now()
        # Encode previous assignment
        for day in self.days[1:]: # dont care about the first day - no assignment given
            for patient in self.patients[day]:
                if patient in self.patients[day-1]: #!= -1: # patient should keep bed-station only if they had one previously
                    for room in range(self.NO_ROOMS):
                        s.add(Or(
                            Implies(patients[day-1][patient][room], patients[day][patient][room]), changes[day][patient])) 
        print((datetime.datetime.now()-start).total_seconds())

        
        
        # Find assignment with few moved patients     
        if "c" in self.mode:
            h = s.minimize(Sum([changes[day][p] for day in self.days for p in self.patients[day]])) # if self.previous[day][p] != -1
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
            max_patients = Int('maximal patients')
            for day in range(self.days):
                for room in range(self.NO_ROOMS):
                    s.add(Sum([patients[day][i][room] for i in self.patients[day]]) <= max_patients)
            h = s.minimize(max_patients)


        # print(s)
        
        print("Writing")
        start = datetime.datetime.now()
        # with open('problem_export.smt2', mode='w') as f:
        #     f.write(s.sexpr())
        print((datetime.datetime.now()-start).total_seconds())
        
        print("solving")
        start = datetime.datetime.now()
        print(s.check())
        print((datetime.datetime.now()-start).total_seconds())
        
        if s.check() != sat:
            print("Model is unsat")
            print(s.unsat_core())
            return "Model is unsat", s.unsat_core()
        else:
            # Get model and format output
            m = s.model()
            assert s.lower(h) == s.upper(h)
            print("Number of changes", s.lower(h))
            for day in self.days:
                assignment = {str(i) : [] for i in range(self.NO_ROOMS)}
                room_gender = {str(i) : None for i in range(self.NO_ROOMS)}

                print(f'day {day}')
                print("  genders")
                for v in genders[day]:
                    print("    ", str(v), m.eval(v, model_completion=True))
                    room_gender[str(v).split(" ")[2]] = m.eval(v, model_completion=True)
                    
                for patient in patients[day]:
                    print("  patient", patient)
                    # print("  ", " ".join(str(patient[0]).split(" ")[:2]))
                    for v in patients[day][patient]:
                        print("    ", str(v), m.eval(v, model_completion=True))
                        if m.eval(v):
                            assigned_room = str(v).split(" ")[-4]
                            assigned_patient = str(v).split(" ")[1]
                            assignment[assigned_room].append(assigned_patient) 

                result = []
                for k in assignment:
                    res_dic = {}
                    res_dic[k] = {
                        'patients': assignment[k],
                        'gender': str(room_gender[str(k)])
                    }
                    result.append(res_dic)
                    # result.append(f'Room {str(k)} is gender {room_gender[str(k)]} and holds patients {" ".join(assignment[k])}')
                # print(assignment)
                print(result)
            return s.lower(h).as_long()



# # Example usage:

# old main
# # This we get from the DB
# no_rooms = 17
# capacities = [2, 1, 2, 3, 1, 4, 4, 2, 3, 2, 1, 3, 3, 3, 1, 1, 1]
# room_distances = [1, 1, 1, 1, 1, 1, 1, 1, 2, 2, 2, 2, 3, 3, 4, 4, 4]

# # This we get from ABS
# # no_patients = 31
# # genders = [False] * 31
# # infectious = [False] * 31
# # patient_distances = [1] * 23 + [3] * 4 + [2] * 4

# # hospital = HospitalRoomAssignment(no_rooms, capacities, room_distances, no_patients, genders, infectious, patient_distances)
# # result = hospital.assign_rooms()
# # print(result)

# patientsData = {
#     'einar': {
#         'gender': True,
#         'infectious': False,
#     },
#     'rudi': {
#         'gender': True,
#         'infectious': False,
#     },
#     'lizeth': {
#         'gender': False,
#         'infectious': True,
#     },
#     'laura': {
#         'gender': False,
#         'infectious': False,
#     },
#     'riccardo': {
#         'gender': True,
#         'infectious': False,
#     }
# }

# # Read file
# with open('abs.txt', 'r') as f:
#     # Read all content
#     content = f.read()


# # EB - Split content by "------"
# scenarios = content.strip().split('------')

# # Iterate over scenarios
# for scenario in scenarios:
#     if (len(scenario) == 0):
#         continue

#     # Split scenario by newline
#     lines = scenario.split('\n')

#     genders = []
#     infectious = []
#     patient_distances = []

#     for line in lines:
#         patients = line.split(",")

#         if len(patients) != 2:
#             continue

#         genders.append(patientsData[patients[0]]['gender'])
#         infectious.append(patientsData[patients[0]]['infectious'])
#         patient_distances.append(int(patients[1]))

#     no_patients = len(genders)

#     print(genders)
#     print(infectious)
#     print(patient_distances)

#     hospital = HospitalRoomAssignment(no_rooms, capacities, room_distances, no_patients, genders, infectious, patient_distances)
#     result = hospital.assign_rooms()
#     print(result)
        

if __name__ == "__main__":
    no_rooms = 40 #4
    no_days = 100
    min_patients = 10
    max_patients = 100
    
    # capacities = [random.randint(1,10) for i in range(no_rooms)] #[1, 2, 3, 2]
    # room_distances = [random.randint(1,5) for i in range(no_rooms)] #[1, 2, 2, 1]
    
    # no_patients = [random.randint(min_patients, max_patients) for i in range(no_days)] # [5, 3]
    # genders = [[bool(random.getrandbits(1)) for j in range(no_patients[i])] for i in range(no_days)] # [[True, True, False, True, False], [True, False, False]]
    # infectious = [[bool(random.getrandbits(1)) for j in range(no_patients[i])] for i in range(no_days)] # [[True, False, False, True, False], [False, False, False]]
    # patient_distances = [[random.randint(1,5) for j in range(no_patients[i])] for i in range(no_days)] #[[1, 2, 3, 1, 2], [3, 2, 1]]
    
    # previous = [[-1 for j in range(no_patients[i])] for i in range(no_days)] # [[-1, -1, -1, -1, -1], [1,-1,-1]] # which patients are staying?
    
    # print("Total patients", sum(no_patients))
    # # random assignment
    no_rooms=17
    capacities=[1, 2, 2, 3, 1, 2, 1, 2, 3, 1, 1, 1, 4, 4, 3, 3, 3]
    room_distances=[4, 2, 5, 2, 5, 1, 1, 1, 3, 4, 1, 4, 5, 1, 3, 1, 2]
    
    no_patients = [5, 3]
    genders = [[True, True, False, True, False], [True, False, False]]
    contagious = [[True, False, False, True, False], [False, False, False]]
    patients_category = [[1, 2, 3, 1, 2], [3, 2, 1]]
    
    # previous = [[-1, -1, -1, -1, -1], [4, 2, -1]] # which patients are staying?
    
    # patients = [{'paul': {}}]
    
    names = [['a', 'b', 'c', 'd', 'e'], ['f', 'g', 'a']]
    
    def pat(gender, cont, cat):
        return {'Cat': cat, 'Gender': gender, 'Contagious': cont}
    
    # patients = [{names[day][i] : pat(genders[day][i], contagious[day][i], patients_category[day][i]) for i in range(no_patients[day])} for day in range(len(no_patients))]
    # print(patients)
    patients = [{'F3FE7CAD16C': {'Cat': 0, 'Gender': True, 'Contagious': False}, '6B3FA0DAE25': {'Cat': 0, 'Gender': True, 'Contagious': False}, '19D05E782ED': {'Cat': 0, 'Gender': True, 'Contagious': False}}, {'F3FE7CAD16C': {'Cat': 3, 'Gender': True, 'Contagious': False}, '6B3FA0DAE25': {'Cat': 1, 'Gender': True, 'Contagious': False}, '19D05E782ED': {'Cat': 1, 'Gender': True, 'Contagious': False}, '42FAE414A33': {'Cat': 0, 'Gender': True, 'Contagious': False}, '15263521BDE': {'Cat': 0, 'Gender': False, 'Contagious': False}}, {'F3FE7CAD16C': {'Cat': 3, 'Gender': True, 'Contagious': False}, '6B3FA0DAE25': {'Cat': 2, 'Gender': True, 'Contagious': False}, '19D05E782ED': {'Cat': 2, 'Gender': True, 'Contagious': False}, '42FAE414A33': {'Cat': 1, 'Gender': True, 'Contagious': False}, '15263521BDE': {'Cat': 1, 'Gender': False, 'Contagious': False}, 'F52E30F3061': {'Cat': 0, 'Gender': False, 'Contagious': False}, '7F85C2B78C6': {'Cat': 0, 'Gender': False, 'Contagious': False}, 'A14D487310C': {'Cat': 0, 'Gender': True, 'Contagious': False}}, {'F3FE7CAD16C': {'Cat': 3, 'Gender': True, 'Contagious': False}, '7F85C2B78C6': {'Cat': 3, 'Gender': False, 'Contagious': False}, '6B3FA0DAE25': {'Cat': 1, 'Gender': True, 'Contagious': False}, '19D05E782ED': {'Cat': 1, 'Gender': True, 'Contagious': False}, 'F52E30F3061': {'Cat': 1, 'Gender': False, 'Contagious': False}, 'A14D487310C': {'Cat': 1, 'Gender': True, 'Contagious': False}, '42FAE414A33': {'Cat': 2, 'Gender': True, 'Contagious': False}, '15263521BDE': {'Cat': 2, 'Gender': False, 'Contagious': False}, '3A366B7B687': {'Cat': 0, 'Gender': False, 'Contagious': False}, 'FAAB51D7D37': {'Cat': 0, 'Gender': False, 'Contagious': False}, 'E6D8A2118F8': {'Cat': 0, 'Gender': False, 'Contagious': False}}, {'F3FE7CAD16C': {'Cat': 3, 'Gender': True, 'Contagious': False}, 'F52E30F3061': {'Cat': 3, 'Gender': False, 'Contagious': False}, '7F85C2B78C6': {'Cat': 3, 'Gender': False, 'Contagious': False}, '6B3FA0DAE25': {'Cat': 1, 'Gender': True, 'Contagious': False}, '19D05E782ED': {'Cat': 1, 'Gender': True, 'Contagious': False}, '42FAE414A33': {'Cat': 1, 'Gender': True, 'Contagious': False}, '15263521BDE': {'Cat': 1, 'Gender': False, 'Contagious': False}, 'FAAB51D7D37': {'Cat': 1, 'Gender': False, 'Contagious': False}, 'A14D487310C': {'Cat': 2, 'Gender': True, 'Contagious': False}, '3A366B7B687': {'Cat': 2, 'Gender': False, 'Contagious': False}, 'E6D8A2118F8': {'Cat': 2, 'Gender': False, 'Contagious': False}, 'E41480D8DED': {'Cat': 0, 'Gender': True, 'Contagious': False}}, {'F3FE7CAD16C': {'Cat': 3, 'Gender': True, 'Contagious': False}, 'F52E30F3061': {'Cat': 3, 'Gender': False, 'Contagious': False}, '7F85C2B78C6': {'Cat': 3, 'Gender': False, 'Contagious': False}, '42FAE414A33': {'Cat': 1, 'Gender': True, 'Contagious': False}, 'A14D487310C': {'Cat': 1, 'Gender': True, 'Contagious': False}, '3A366B7B687': {'Cat': 2, 'Gender': False, 'Contagious': False}, 'FAAB51D7D37': {'Cat': 2, 'Gender': False, 'Contagious': False}, 'E6D8A2118F8': {'Cat': 2, 'Gender': False, 'Contagious': False}, 'E41480D8DED': {'Cat': 2, 'Gender': True, 'Contagious': False}}, {'F3FE7CAD16C': {'Cat': 3, 'Gender': True, 'Contagious': False}, 'F52E30F3061': {'Cat': 3, 'Gender': False, 'Contagious': False}, '7F85C2B78C6': {'Cat': 3, 'Gender': False, 'Contagious': False}, '42FAE414A33': {'Cat': 1, 'Gender': True, 'Contagious': False}, 'A14D487310C': {'Cat': 1, 'Gender': True, 'Contagious': False}, 'E6D8A2118F8': {'Cat': 2, 'Gender': False, 'Contagious': False}, 'E41480D8DED': {'Cat': 2, 'Gender': True, 'Contagious': False}}, {'F3FE7CAD16C': {'Cat': 3, 'Gender': True, 'Contagious': False}, '7F85C2B78C6': {'Cat': 3, 'Gender': False, 'Contagious': False}, 'A14D487310C': {'Cat': 1, 'Gender': True, 'Contagious': False}, 'E6D8A2118F8': {'Cat': 2, 'Gender': False, 'Contagious': False}}, {'F3FE7CAD16C': {'Cat': 3, 'Gender': True, 'Contagious': False}, '7F85C2B78C6': {'Cat': 3, 'Gender': False, 'Contagious': False}, 'E6D8A2118F8': {'Cat': 2, 'Gender': False, 'Contagious': False}}, {'F3FE7CAD16C': {'Cat': 3, 'Gender': True, 'Contagious': False}, '7F85C2B78C6': {'Cat': 3, 'Gender': False, 'Contagious': False}}, {'F3FE7CAD16C': {'Cat': 3, 'Gender': True, 'Contagious': False}, '7F85C2B78C6': {'Cat': 3, 'Gender': False, 'Contagious': False}}, {'F3FE7CAD16C': {'Cat': 3, 'Gender': True, 'Contagious': False}, '7F85C2B78C6': {'Cat': 3, 'Gender': False, 'Contagious': False}}, {'F3FE7CAD16C': {'Cat': 3, 'Gender': True, 'Contagious': False}, '7F85C2B78C6': {'Cat': 3, 'Gender': False, 'Contagious': False}}, {'F3FE7CAD16C': {'Cat': 3, 'Gender': True, 'Contagious': False}, '7F85C2B78C6': {'Cat': 3, 'Gender': False, 'Contagious': False}}, {'F3FE7CAD16C': {'Cat': 3, 'Gender': True, 'Contagious': False}, '7F85C2B78C6': {'Cat': 3, 'Gender': False, 'Contagious': False}}, {'F3FE7CAD16C': {'Cat': 3, 'Gender': True, 'Contagious': False}, '7F85C2B78C6': {'Cat': 3, 'Gender': False, 'Contagious': False}}, {'F3FE7CAD16C': {'Cat': 3, 'Gender': True, 'Contagious': False}}]
    
    mode = 'c'
    
    print("Call")
    hospital = HospitalRoomAssignmentGlobal(no_rooms, capacities, room_distances, patients, mode)
    result = hospital.assign_rooms()
