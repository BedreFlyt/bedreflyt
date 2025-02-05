from deap import base
from deap import creator
from deap import tools

import pandas as pd

import zlib
import argparse
import random
import multiprocessing
import copy

from hospital import HospitalRoomAssignmentGlobal, HospitalRoomAssignment

import json
import base64

no_rooms=17
capacities=[1, 3, 1, 1, 4, 3, 1, 3, 2, 1, 4, 2, 2, 3, 1, 3, 2]
room_distances=[2, 3, 1, 2, 1, 3, 3, 1, 1, 2, 3, 3, 1, 2, 1, 2, 2]
mode = 'c'
    
def individual(names, categories, genders, contagiousness):
        return_dict = {}
        for n in range(len(names)):
            return_dict[names[n]] = {'Cat': categories[n], 'Gender': genders[n], 'Contagious':contagiousness[n]}
        return return_dict
    
def random_individuals(patients_day, patient_names):
        return_dict = {}
        chosen_names = []
        for i in range(patients_day):
            name = random.randint(1,patient_names)
            while name in chosen_names:
                name = random.randint(1,patient_names)
            chosen_names.append(name)    
            cat = random.randint(1,3)
            gender = bool(random.randint(0,1))
            contagious = bool(random.randint(0,1))
            return_dict[name] = {'Cat': cat, 'Gender': gender, 'Contagious': contagious}
        return return_dict
    
def evalPatients(individual):
        hospital = HospitalRoomAssignmentGlobal(no_rooms, capacities, room_distances, individual, mode)
        result = hospital.assign_rooms()
        if type(result) == int:
            return [result]
        else:
            return [-1]
        
def evaluate_local(days):
        total_changes = 0
        # for days in population:
        patients = [p for p in days[0]]
        patient_names_before = []
        
        for i in range(len(days)):
            day = days[i]                
                
            patient_names = [p for p in day]
            patients = [day[p] for p in patient_names]
            genders = [bool(p['Gender']) for p in patients]
            contagious = [bool(p['Contagious']) for p in patients]
            patient_categories = [p['Cat'] for p in patients]
            
            # define previous based on day before - fields are not updated yet and result still holds previous assignment
            previous = [-1 if p not in patient_names_before else assignment_patient_names_to_room[p] for p in patient_names]
                            
            hospital = HospitalRoomAssignment(no_rooms, capacities, room_distances, len(patients), genders, contagious, patient_categories, previous, mode)
            r = hospital.assign_rooms()
            
            if type(r) == tuple:
                return -1
            
            result = r['allocations']
            changes = r['changes']
            
            assignment_patient_names_to_room = {patient_names[p] : [room for room in range(len(result)) if str(p) in result[room][str(room)]['patients']][0] for p in range(len(patient_names))}
            assert len(result) == no_rooms
            assert len(patient_names) == len(assignment_patient_names_to_room)
            
            patient_names_before = copy.deepcopy(patient_names)
            
            total_changes += changes
    
        return total_changes
    
if __name__ == "__main__":
    parser = argparse.ArgumentParser(
                prog = 'genetic_instances.py',
                description = "File to generate feasible, but hard SMT problems for bedreflyt")
    parser.add_argument('-p', '--population', help = "Population size", type=int, default = 300)
    parser.add_argument('-d', '--days', help = "Number of days to generate patients for", type=int, default = 5) 
    parser.add_argument('-pd', '--patient_day', help = "Number of patients per day", type=int, default = 10) 
    parser.add_argument('-pn', '--patient_names', help = "Number of patients in total", type=int, default = 50) 
    parser.add_argument('-c', '--cores', help = "Cores to use", type=int, default = 6) 
    parser.add_argument('-g', '--generations', help = "Genetic algorithm generations", type=int, default = 500) 
    args = parser.parse_args() 
    
    pool = multiprocessing.Pool(args.cores)
    
    creator.create("FitnessMax", base.Fitness, weights=(1.0,))
    creator.create("Individual", list, fitness=creator.FitnessMax)
    toolbox = base.Toolbox()
    toolbox.register("map", pool.map)
    toolbox.register("attr_patients", random_individuals, args.patient_day, args.patient_names)
    
    toolbox.register("individual", tools.initRepeat, creator.Individual, toolbox.attr_patients, args.days)
    toolbox.register("population", tools.initRepeat, list, toolbox.individual)
    
    toolbox.register("evaluate", evalPatients)
    toolbox.register("mate", tools.cxTwoPoint)
    toolbox.register("mutate", tools.mutInversion)
    toolbox.register("select", tools.selTournament, tournsize=3)

    pop = toolbox.population(n=args.population)
    
    # Evaluate the entire population
    fitnesses = list(toolbox.map(toolbox.evaluate, pop))
    for ind, fit in zip(pop, fitnesses):
        ind.fitness.values = fit
        
    # CXPB  is the probability with which two individuals
    #       are crossed
    #
    # MUTPB is the probability for mutating an individual
    CXPB, MUTPB = 0.5, 0.2
    
    fits = [ind.fitness.values[0] for ind in pop]
    
    g = 0
    means_global = []
    means_online = []
    result_dict = {'problem':[], 'optimal': [], 'online' : [], 'days': [], 'population': [], 'patients_day':[], 'patient_names':[], 'generation':[]}

    
    while g < args.generations:
        # A new generation
        g = g + 1
        print("-- Generation %i --" % g)
        
        # Select the next generation individuals
        offspring = toolbox.select(pop, len(pop))
        # Clone the selected individuals
        offspring = list(map(toolbox.clone, offspring))
        
        # Apply crossover and mutation on the offspring
        for child1, child2 in zip(offspring[::2], offspring[1::2]):
            if random.random() < CXPB:
                toolbox.mate(child1, child2)
                del child1.fitness.values
                del child2.fitness.values

        for mutant in offspring:
            if random.random() < MUTPB:
                toolbox.mutate(mutant)
                del mutant.fitness.values
                
        # Evaluate the individuals with an invalid fitness
        invalid_ind = [ind for ind in offspring] # if not ind.fitness.valid

        fitnesses = toolbox.map(toolbox.evaluate, invalid_ind)
        for ind, fit in zip(invalid_ind, fitnesses):
            ind.fitness.values = fit        
        
        pop[:] = offspring
        
        # Gather all the fitnesses in one list and print the stats
        fits = [ind.fitness.values[0] for ind in pop]
        
        # Store new population
        pop_list = [p for p in pop]
        online_changes = toolbox.map(evaluate_local, pop_list)
        global_changes = toolbox.map(evalPatients, pop_list)
        mean_online = sum(online_changes)/len(pop_list)
        
        # write to csv file
        for i in range(len(pop_list)):
            p = pop_list[i]
            # assert evalPatients(p)[0] == p.fitness.values[0], f'{evalPatients(p)[0]} != {p.fitness.values[0]}, for {p}'
            # assert global_changes[i][0] == evalPatients(p)[0], f'{global_changes[i][0]} != {evalPatients(p)[0]}, for {p}'
            # if p.fitness.values[0] > online_changes[i]:
            #     print("problem")
            #     # assert evaluate_local(p) == online_changes[i]
            #     print(f'### Error online {online_changes[i]}, global {p.fitness.values[0]}, {p}')
            #     assert(False)
            # assert p.fitness.values[0] > online_changes[i], f'{p.fitness.values[0]}, {online_changes[i]}, {p}'
            result_dict['problem'].append(base64.b64encode(zlib.compress(json.dumps(p).encode())).decode())
            result_dict['optimal'].append(global_changes[i][0])
            result_dict['online'].append(online_changes[i])
            result_dict['days'].append(args.days)
            result_dict['population'].append(args.population)
            result_dict['patients_day'].append(args.patient_day)
            result_dict['patient_names'].append(args.patient_names)
            result_dict['generation'].append(g)
            
            # assert result_dict['optimal'][-1] <= result_dict['online'][-1], f'Error opt: {result_dict["optimal"][-1]} online: {result_dict["online"][-1]} for {p}'
        
        length = len(pop)
        mean = sum(fits) / length
        sum2 = sum(x*x for x in fits)
        std = abs(sum2 / length - mean**2)**0.5

        print("  Min %s" % min(fits))
        print("  Max %s" % max(fits))
        print("  Avg %s" % mean)
        print("  Std %s" % std)
        print("online mean", mean_online)
        
        means_global.append(mean)
        means_online.append(mean_online)
    
    # store results
    df = pd.DataFrame(result_dict)
    df.to_csv(f'out/summary_{args.days}_{args.population}_{args.patient_day}_{args.patient_names}.csv')