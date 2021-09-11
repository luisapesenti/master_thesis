import matplotlib.pyplot as plt
import numpy as np
import numpy_financial as npf
import pandas as pd

from thesis.energy import get_tariff, get_dispatch
from thesis.plotting import plot_day, plot_financial
from thesis.util import get_yaml


def pv_bess_dummy(input, config, plot=False):
    # energy calculation
    duration = config["financial"]["duration"]
    scaling_factor = input["pv_size"] / input["pv_profile_size"]
    pv_gen = pd.read_csv(input["pv_profile_10mw_path"], header=None).to_numpy().T[0] * scaling_factor
    bess_capex = f"bess_capex_{input['bess_duration']}h"
    bess_degradation_type = f"bess_degradation_{input['bess_duration']}h"
    curtailed_pv = np.minimum(pv_gen, input["max_export"])
    tariff = get_tariff(input["tariff"], input["ppa"])
    bess_degradation_curve = config[bess_degradation_type]
    discharge_profile_yearly = np.zeros(duration + 1)
    for i in range(1, duration + 1):
        pv_gen_adjusted = pv_gen * (1 - config["pv_capex"]["degradation"]) ** (i - 1)
        bess_energy_adjusted = input["bess_energy"] * bess_degradation_curve[i - 1]
        soc_profile_i, charge_profile_i, discharge_profile_i, _ = get_dispatch(pv_gen_adjusted, input["max_export"],
                                                                            bess_energy_adjusted,
                                                                            input["bess_power"],
                                                                            config["bess"]["max_soc"],
                                                                            config["bess"]["min_soc"], tariff)
        if i == 1:
            soc_profile_y1 = soc_profile_i
            charge_profile_y1 = charge_profile_i
            discharge_profile_y1 = discharge_profile_i
            if plot:
                plot_day(210, 212, input["max_export"], pv_gen_adjusted, soc_profile_y1, discharge_profile_y1,
                         charge_profile_y1)
        discharge_profile_yearly[i] = config["bess"]["rte"] * discharge_profile_i.sum()
    cycles = discharge_profile_y1.sum() / input["bess_energy"]
    total_sold_y1 = curtailed_pv + discharge_profile_y1
    revenue_y1 = tariff * total_sold_y1  # useless
    total_revenue_y1 = revenue_y1.sum()  # useless
    energy_base = total_sold_y1[tariff == input["ppa"]["base"]].sum()
    energy_peak = total_sold_y1[tariff == input["ppa"]["peak"]].sum()
    pv_sold_deg = np.zeros(duration + 1)
    pv_sold_deg[1:] = curtailed_pv.sum() * (1 - config["pv_capex"]["degradation"]) ** (np.arange(1, duration + 1) - 1)
    sold_deg = pv_sold_deg + discharge_profile_yearly
    energy_not_sold=pv_gen.sum()-total_sold_y1.sum()
    percentage_rene=(sold_deg[1]/pv_gen.sum())*100
    # financial calculation
    ppa_levelized = (energy_peak * input["ppa"]["peak"] + energy_base * input["ppa"]["base"]) / (
            energy_peak + energy_base)
    # Capex and Opex PV
    modules = config["pv_capex"]["modules"] * input["pv_size"]
    BoS = config["pv_capex"]["bos"] * input["pv_size"]
    tracker = config["pv_capex"]["tracker"] * input["pv_size"]
    land = config["pv_capex"]["land_cost"] * config["pv_capex"]["land_pv"] * input["pv_size"]
    civil_work = config["pv_capex"]["civil_work"] * config["pv_capex"]["land_pv"] * input["pv_size"]
    engineering = config["pv_capex"]["engineering"] * input["pv_size"]
    total_capex_pv = modules + BoS + tracker + land + engineering + civil_work
    total_opex_pv = config["pv_capex"]["opex"] * input["pv_size"]
    # Capex and Opex BESS
    modules = config[bess_capex]["modules_inverters"] * input["bess_energy"]
    BoS = config[bess_capex]["bos"] * input["bess_power"]
    civil_work = config[bess_capex]["civil_work"] * input["bess_energy"]
    engineering = config[bess_capex]["engineering"] * input["bess_energy"]
    total_capex_bess = modules + BoS + engineering + civil_work
    total_opex_bess = config[bess_capex]["opex"] * input["bess_energy"]
    # Total Capex and Opex
    total_capex = (total_capex_bess + total_capex_pv) * (1 - config["colocation"]["reduction"])
    total_opex = total_opex_pv + total_opex_bess

    capex = np.zeros(duration + 1)
    capex[0] = total_capex
    opex = np.zeros(duration + 1)
    opex[1:] = total_opex
    opex_with_inflation = opex * ((1 + config["financial"]["inflation"]) ** np.arange(0, duration + 1))

    # Cash In and Cash Out
    cash_in = ppa_levelized * sold_deg
    cash_out = capex + opex_with_inflation
    # LCOE
    lcoe = 1000 * npf.npv(input["wacc"], cash_out) / npf.npv(input["wacc"], sold_deg)  # €/MWh

    # NPV and IRR calculation
    net_cashflow = cash_in - cash_out
    NPV = npf.npv(input["wacc"], net_cashflow)
    IRR = npf.irr(net_cashflow)

    # payback time
    cumulative_cashflow = net_cashflow.cumsum()
    payback_time = f">{duration} years"
    for x in range(duration + 1):
        if cumulative_cashflow[x] > 0:
            payback_time = f"{x} years"
            break
    print(f"Results for PV+BESS (dummy) utility scale plant")
    print(f"LCOE :  {lcoe:.2f} [€/MWh]")
    print(f"NPV :  {NPV:.2f} [€]")
    print(f"IRR :  {(IRR * 100):.2f} [%]")
    print(f"Payback time :  {payback_time} ")
    print(f"Energy curtailed year 1 :  {energy_not_sold} [kWh]")
    print(f"Renewable penetration year 1 :  {percentage_rene} [%]")

    if plot:
        plot_financial(duration, cumulative_cashflow)
    return lcoe, NPV, IRR, payback_time


if __name__ == '__main__':
    # get input and config data
    input = get_yaml("./input/input1.yaml")
    config = get_yaml("./config/config.yaml")
    pv_bess_dummy(input, config, True)
