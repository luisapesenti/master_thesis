import matplotlib.pyplot as plt
import numpy as np
import numpy_financial as npf
import pandas as pd

from thesis.energy import get_tariff
from thesis.plotting import plot_day, plot_day_pvonly, plot_financial
from thesis.util import get_yaml


def pv_only_scenario(input, config, plot=False):
    # energy calculation
    scaling_factor = input["pv_size"] / input["pv_profile_size"]
    pv_gen = pd.read_csv(input["pv_profile_10mw_path"], header=None).to_numpy().T[0] * scaling_factor

    curtailed = np.minimum(pv_gen, input["max_export"])
    total_sold = curtailed.sum()
    total_not_sold = (pv_gen - curtailed).sum()
    percentage_rene= (total_sold/pv_gen.sum())*100
    tariff = get_tariff(input["tariff"], input["ppa"])
    revenue = tariff * curtailed
    total_revenue = revenue.sum()
    energy_base = curtailed[tariff == input["ppa"]["base"]].sum()
    energy_peak = curtailed[tariff == input["ppa"]["peak"]].sum()
    duration = config["financial"]["duration"]
    energy_sold_deg = np.zeros(duration + 1)
    energy_sold_deg[1:] = total_sold * (1 - config["pv_capex"]["degradation"]) ** (np.arange(1, duration + 1) - 1)
    # financial calculation
    ppa_levelized = (energy_peak * input["ppa"]["peak"] + energy_base * input["ppa"]["base"]) / (
            energy_peak + energy_base)
    # Capex and Opex
    modules = config["pv_capex"]["modules"] * input["pv_size"]
    BoS = config["pv_capex"]["bos"] * input["pv_size"]
    tracker = config["pv_capex"]["tracker"] * input["pv_size"]
    land = config["pv_capex"]["land_cost"] * config["pv_capex"]["land_pv"] * input["pv_size"]
    civil_work = config["pv_capex"]["civil_work"] * config["pv_capex"]["land_pv"] * input["pv_size"]
    engineering = config["pv_capex"]["engineering"] * input["pv_size"]
    total_capex = modules + BoS + tracker + land + engineering + civil_work
    total_opex = config["pv_capex"]["opex"] * input["pv_size"]

    capex = np.zeros(duration + 1)
    capex[0] = total_capex
    opex = np.zeros(duration + 1)
    opex[1:] = total_opex
    opex_with_inflation = opex * ((1 + config["financial"]["inflation"]) ** np.arange(0, duration + 1))

    # Cash In and Cash Out
    cash_in = ppa_levelized * energy_sold_deg
    cash_out = capex + opex_with_inflation
    # LCOE
    lcoe_pv = 1000 * npf.npv(input["wacc"], cash_out) / npf.npv(input["wacc"], energy_sold_deg)  # €/MWh

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
    print(f"Results for PV utility scale plant")
    print(f"LCOE :  {lcoe_pv:.2f} [€/MWh]")
    print(f"NPV :  {NPV:.2f} [€]")
    print(f"IRR :  {(IRR * 100):.2f} [%]")
    print(f"Payback time :  {payback_time} ")
    print(f"Energy curtailed year 1 :  {total_not_sold} [kWh]")
    print(f"Renewable penetration year 1 :  {percentage_rene} [%]")
    if plot:
        plot_financial(duration, cumulative_cashflow)
        plot_day_pvonly(210, 212, input["max_export"],pv_gen,curtailed)
    return lcoe_pv, NPV, IRR, payback_time


if __name__ == '__main__':
    # get input and config data
    input = get_yaml("./input/input1.yaml")
    config = get_yaml("./config/config.yaml")
    pv_only_scenario(input, config)
