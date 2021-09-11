import datetime
import os
from shutil import copyfile

import numpy as np
import pandas as pd

from thesis.energy import get_tariff, get_dispatch_controlled, get_dispatch
from thesis.util import get_yaml, save_and_plot


def objective_function(bess_discharging, tariff):
    revenue = bess_discharging * tariff
    return revenue.sum()


def generate_random_population(n_chromosome: int, tariff):
    mask_zero = tariff == 0
    mask_not_zero = tariff > 0
    population = []
    for i in range(n_chromosome):
        solution = np.zeros(len(tariff))
        solution[mask_zero] = np.random.randint(0, 2, mask_zero.sum())
        solution[mask_not_zero] = np.random.randint(0, 3, mask_not_zero.sum())
        population.append([solution, 0.0])
    return population


def generate_pop_mutation(best_child, n_chromosome, n_mutation, tariff):
    mutation_idx_matrix = np.random.randint(0, len(best_child), (n_chromosome, n_mutation))
    mask_zero = tariff[mutation_idx_matrix] == 0
    mask_not_zero = tariff[mutation_idx_matrix] > 0
    mutation_value_matrix = np.zeros((n_chromosome, n_mutation))
    mutation_value_matrix[mask_zero] = np.random.randint(0, 2, mask_zero.sum())
    mutation_value_matrix[mask_not_zero] = np.random.randint(0, 3, mask_not_zero.sum())
    new_population = []
    for i in range(n_chromosome):
        new_child = best_child.copy()
        new_child[mutation_idx_matrix[i]] = mutation_value_matrix[i]
        new_population.append([new_child, 0.0])
    return new_population


if __name__ == '__main__':
    # Create Experiment folder
    output_folder = f"./output/scenario3_optim_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}/"
    os.makedirs(output_folder, exist_ok=True)
    # Get input and config data and copy files in the experiment folders
    input = get_yaml("./input/input1.yaml")
    copyfile("./input/input1.yaml", f"{output_folder}input.yaml")
    config = get_yaml("./config/config.yaml")
    copyfile("./config/config.yaml", f"{output_folder}config.yaml")

    # energy calculation
    duration = config["financial"]["duration"]
    scaling_factor = input["pv_size"] / input["pv_profile_size"]
    pv_gen = pd.read_csv(input["pv_profile_10mw_path"], header=None).to_numpy().T[0] * scaling_factor
    bess_capex = f"bess_capex_{input['bess_duration']}h"
    bess_degradation_type = f"bess_degradation_{input['bess_duration']}h"

    curtailed_pv = np.minimum(pv_gen, input["max_export"])
    tariff = get_tariff(input["tariff"], input["ppa"])

    n_generation = 1000  # number of iteration/trial
    n_chromosome = 1000  # number of solution created
    n_mutation = 50
    patience = 50
    patience_count = 0
    best_solution = None
    best_score = 0
    history = []
    # Get Dummy Control
    """
    _, _, _, control_dummy = get_dispatch(pv_gen, input["max_export"],
                                          input["bess_energy"],
                                          input["bess_power"],
                                          config["bess"]["max_soc"],
                                          config["bess"]["min_soc"], tariff)
    current_population = generate_pop_mutation(control_dummy, n_chromosome, n_mutation, tariff)
    """
    current_population = generate_random_population(n_chromosome, tariff)
    # Generazione Soluzioni iniziali randomiche
    for i in range(n_generation):
        for ch_i, ch in enumerate(current_population):
            soc_profile, charge_profile, discharge_profile = get_dispatch_controlled(pv_gen, input["max_export"],
                                                                                     input["bess_energy"],
                                                                                     input["bess_power"],
                                                                                     config["bess"]["max_soc"],
                                                                                     config["bess"]["min_soc"], ch[0])
            ch[1] = objective_function(discharge_profile, tariff)
        sorted_population = sorted(current_population, key=lambda ch: ch[1], reverse=True)
        best_child, score = sorted_population[0]
        history.append(score)
        print(f"Generation {i},\t score {score:.2f}")
        patience_count += 1
        if score > best_score:
            patience_count = 0
            best_score = score
            best_solution = best_child.copy()
            save_and_plot(best_solution, best_score, history, output_folder)
        if patience_count > patience:
            print(f"Patience is over!")
            break
        current_population = generate_pop_mutation(best_child, n_chromosome, n_mutation, tariff)
        current_population.append(sorted_population[0])
        pass
