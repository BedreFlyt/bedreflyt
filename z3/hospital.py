from z3 import *

# Nevrokirurgisk avd, OUS
# Model   Bedpost info                                           Model 
# Roomnbr Romnr Antall senger	Eget bad?	Seksjon/type rom Category
# 0       2	1*      	x       	Sengepost        1
# 1       3	2       	x	        Sengepost        1
# 2       4	2	        x	        Sengepost        1
# 3       19	3	        x	        Sengepost        1
# 4       21	1*	        x	        Sengepost        1
# 5       22	4	        	        Sengepost        1
# 6       36	2	        x	        Sengepost        1
# 7       38	2	        x	        Sengepost        1
# 8       23	3	        	        Intermediær      2
# 9       28	2	 	                Intermediær      2
# 10      29	1*	        x	        Intermediær      2
# 11      31	3	        x	        Intermediær      2
# 12      6	3	        x	        Overvåkning      3
# 13      43	3	        	        Overvåkning      3
# 
NO_ROOMS = 14
C = [1, 2, 2, 3, 1, 4, 2, 2, 3, 2, 1, 3, 3, 3] # capacities of rooms (i.e., patient bay)
Dr = [1, 1, 1, 1, 1, 1, 1, 1, 2, 2, 2, 2, 3, 3] # Distance-categories of rooms

# NO_PATIENTS = 9
# G = [False, False, False, True, True, False, True, False, True] # genders of patients
# I = [True, False, False, False, False, False, False, False, False] # are patients infectious?
# Dp = [1, 2, 3, 2, 3, 3, 2, 2, 1] # Distance-categories of patients
NO_PATIENTS = 31
G = [ False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False ] # genders of patients
I = [ False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False ] # are patients infectious?
Dp = [ 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 2, 2, 2, 2 ] # Distance-categories of patients


assert len(C) == NO_ROOMS
assert len(G) == NO_PATIENTS
assert len(I) == NO_PATIENTS
assert len(Dp) == NO_PATIENTS
assert len(Dr) == NO_ROOMS

patients = [[ Bool('patient %s in room %s' % (i,j)) for j in range(NO_ROOMS)] for i in range(NO_PATIENTS)]
genders = [Bool('gender room %s' %i )for i in range(NO_ROOMS)]

print(patients, genders)

s = Solver()
s.set(unsat_core=True)

# Each patient in exactly one bed
for patient in range(NO_PATIENTS):
    s.assert_and_track(Sum(patients[patient]) == 1, f'patient assigned{patient}')

# room capacities are satisfies
for room in range(NO_ROOMS):
    s.assert_and_track(Sum([patients[i][room] for i in range(NO_PATIENTS)]) <= C[room], f'room capacity {room}')
    
# Gender constraints
for room in range(NO_ROOMS):
    for patient in range(NO_PATIENTS):
        s.assert_and_track(Implies(patients[patient][room], G[patient] == genders[room]), f'gender constraint room {room} patient {patient}')
        
# Infectious patients
for room in range(NO_ROOMS):
    for patient in range(NO_PATIENTS):
        s.assert_and_track(Implies(
                And(patients[patient][room], I[patient]), # patient in room is infectious
                    And([Not(patients[p][room]) for p in range(NO_PATIENTS) if p != patient]) # no other patient is in room
                    ), f'infectious patient {patient} room {room}'
        )
        
# Consider distance
for patient in range(NO_PATIENTS):
    for room in range(NO_ROOMS):
        s.assert_and_track(Implies(patients[patient][room], 
                      Dp[patient] <= Dr[room]), f'distance patient {patient} room {room}'
        )
        

print(s)
print(s.check())

if s.check() != sat:
    print("Model is unsat")
    print(s.unsat_core())
else:
    # Get model and format output
    m = s.model()
    assignment = {str(i) : [] for i in range(NO_ROOMS)}
    room_gender = {str(i) : None for i in range(NO_ROOMS)}

    for v in genders:
        room_gender[str(v).split(" ")[2]] = m.eval(v, model_completion=True)
        
    for patient in patients:
        for v in patient:
            if m.eval(v):
                assigned_room = str(v).split(" ")[-1]
                assigned_patient = str(v).split(" ")[1]
                assignment[assigned_room].append(assigned_patient) 
       
    print("Satisfying room order") 
    for k in assignment:
        print(f'Room {str(k)} is gender {room_gender[str(k)]} and holds patients {" ".join(assignment[k])}')
