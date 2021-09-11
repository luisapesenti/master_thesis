import yaml
import numpy as np
import matplotlib.pyplot as plt


def get_yaml(file_path):
    with open(file_path, "r") as fp:
        content = yaml.safe_load(fp)
    return content


def save_and_plot(best_solution, best_score, history, output_dir):
    best_solution_array = np.array(best_solution)
    np.savetxt(f"{output_dir}best_solution.csv", best_solution_array, fmt="%.2f")
    all_scores = np.array(history)
    np.savetxt(f"{output_dir}all_scores.csv", all_scores, fmt="%.2f")
    x = np.arange(0, len(history))
    fig = plt.figure(figsize=(12, 5))
    plt.plot(x, history)
    plt.tight_layout()
    plt.savefig(f"{output_dir}score_chart.png", dpi=300)
    plt.close(fig)

    pass
