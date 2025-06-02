from z3 import *

class RoomOpener:
    def __init__(self, current_free_capacity, incoming_patients, room_numbers, capacities, penalties):
        self.current_free_capacity = current_free_capacity
        self.incoming_patients = incoming_patients
        self.room_numbers = room_numbers
        self.capacities = capacities
        self.penalties = penalties

    def find_appropriate_rooms(self):
        # Check if we need to open any rooms at all
        additional_capacity_needed = self.incoming_patients - self.current_free_capacity
        if additional_capacity_needed <= 0:
            return [], 0  # No rooms need to be opened
        
        # Create a Z3 solver instance
        solver = Optimize()  # Use Optimize instead of Solver for minimization

        # Ensure that the lengths of the lists are consistent
        assert len(self.capacities) == len(self.penalties), "Capacities and penalties must have the same length"
        assert len(self.room_numbers) == len(self.capacities), "Room numbers and capacities must have the same length"
        
        # Create Z3 variables for each room
        num_rooms = len(self.capacities)
        room_vars = [Bool(f'room_{i}') for i in range(num_rooms)]
        
        # Create a variable to track the total penalty
        total_penalty = Int('total_penalty')
        
        # Add constraints for the total penalty
        solver.add(total_penalty == Sum([If(room_vars[i], self.penalties[i], 0) for i in range(num_rooms)]))
        
        # Add constraints for the total capacity - we need enough additional capacity
        total_capacity = Sum([If(room_vars[i], self.capacities[i], 0) for i in range(num_rooms)])
        solver.add(total_capacity >= additional_capacity_needed)
        
        # Minimize the total penalty
        solver.minimize(total_penalty)

        # Check if the constraints are satisfiable
        if solver.check() == sat:
            model = solver.model()
            opened_room_indices = [i for i in range(num_rooms) if is_true(model[room_vars[i]])]
            opened_rooms = [self.room_numbers[i] for i in opened_room_indices]
            total_penalty_value = model[total_penalty].as_long()
            return opened_rooms, total_penalty_value
        else:
            return None, None

# Example usage:
if __name__ == "__main__":
    current_capacity = 50
    incoming_patients = 120
    rooms = [0, 318, 319, 320]
    capacities = [20, 30, 40, 50]
    penalties = [100, 200, 150, 300]

    room_opener = RoomOpener(current_capacity, incoming_patients, rooms, capacities, penalties)
    opened_rooms, total_penalty = room_opener.find_appropriate_rooms()

    if opened_rooms is not None:
        print(f"Opened rooms: {opened_rooms}, Total penalty: {total_penalty}")
        print(f"Required additional capacity: {max(0, incoming_patients - current_capacity)}")
        print(f"Current free capacity: {current_capacity}, Incoming patients: {incoming_patients}")
    else:
        print("No solution found.")