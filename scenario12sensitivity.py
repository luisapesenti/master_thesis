import matplotlib.pyplot as plt
import numpy as np
import numpy_financial as npf
import pandas as pd
import seaborn as sns

from scenario1onlypv import pv_only_scenario
from scenario2dummy import pv_bess_dummy
from thesis.energy import get_tariff, get_dispatch
from thesis.util import get_yaml

if __name__ == '__main__':
    # get input and config data
    input = get_yaml("./input/input1.yaml")
    config = get_yaml("./config/config.yaml")
    bess_kws = list(range(1000, 2100, 200))
    pv_sizes = list(range(15000, 25000, 1000))
    wacc_range= list(np.linspace(0.2, 0.8, 7))
    infl_range=list(np.linspace(0.002, 0.03, 7))
    heatmap = np.zeros((len(pv_sizes), len(bess_kws)))
    heatmap1 = np.zeros((len(wacc_range), len(infl_range)))
    for pv_i, pv in enumerate(pv_sizes):
        input["pv_size"] = pv
        lcoe_1, npv_1, irr_1, pbt_1 = pv_only_scenario(input, config)
        for bess_kw_i, bess_kw in enumerate(bess_kws):
            input["bess_power"] = bess_kw
            input["bess_energy"] = bess_kw * 4
            lcoe_2, npv_2, irr_2, pbt_2 = pv_bess_dummy(input, config)
            heatmap[pv_i][bess_kw_i] = (irr_2-irr_1)*100
    for wacc_i, wacc in enumerate(wacc_range):
        input["wacc"] = wacc
        lcoe_1, npv_1, irr_1, pbt_1 = pv_only_scenario(input, config)
        for infl_i, infl in enumerate(infl_range):
            config["financial"]["inflation"] = infl
            lcoe_2, npv_2, irr_2, pbt_2 = pv_bess_dummy(input, config)
            heatmap1[wacc_i][infl_i] = irr_2 * 100

    plt.subplots(figsize=(20, 10))
    plt.title("PV and battery size impact on IRR", fontsize=20)
    plt.rc('font', size=20)  # controls default text sizes
    ax = sns.heatmap(heatmap, linewidth=0.3, xticklabels=bess_kws, yticklabels=pv_sizes, annot=True)
    plt.tight_layout()
    plt.xlabel(" Battery's Power Capacity [kW]", fontsize=20)
    plt.ylabel("PV size [kW]", fontsize=20)
    plt.rc('axes', titlesize=20)
    plt.rc('figure', titlesize=20)
    plt.rc('axes', labelsize=20)  # fontsize of the x and y labels
    plt.rc('xtick', labelsize=20)  # fontsize of the tick labels
    plt.rc('ytick', labelsize=20)  # fontsize of the tick labels
    plt.rc('legend', fontsize=20)  # legend fontsize
    plt.show()

    plt.subplots(figsize=(20, 10))
    plt.title("WACC and Inflation Impact on Scenario 2")
    plt.rc('font', size=20)  # controls default text sizes
    ax = sns.heatmap(heatmap1, linewidth=0.3, xticklabels=infl_range, yticklabels=wacc_range, annot=True)
    plt.tight_layout()
    plt.xlabel(" Inflation Rate [%]", fontsize=20)
    plt.ylabel("WACC [%]", fontsize=20)
    plt.rc('axes', titlesize=20)
    plt.rc('figure', titlesize=20)
    plt.rc('axes', labelsize=20)  # fontsize of the x and y labels
    plt.rc('xtick', labelsize=20)  # fontsize of the tick labels
    plt.rc('ytick', labelsize=20)  # fontsize of the tick labels
    plt.rc('legend', fontsize=20)  # legend fontsize
    plt.show()