import matplotlib.pyplot as plt
import numpy as np


def plot_day(start_day, end_day, max_export, pv_profile, soc_profile, discharge_profile, charge_profile):
    start_day = start_day * 24
    end_day = end_day * 24 + 24
    day_range = np.arange(start_day, end_day)
    fig, ax1 = plt.subplots(figsize=(10, 5))
    plt.title("PV and BESS profiles")
    plt.xlabel("Hour of the year [h]")
    plt.ylabel("Power [kW]")
    ax1.plot(day_range, pv_profile[day_range], label="PV", color="r")
    ax1.plot(day_range, discharge_profile[day_range], label="Discharge", color="g")
    ax1.plot(day_range, charge_profile[day_range], label="Charge", color="b")
    ax1.axhline(max_export, color="y", linestyle="-.")
    plt.grid()
    ax1.legend(loc="upper left")
    ax2 = ax1.twinx()
    ax2.plot(day_range, soc_profile[day_range] * 100, label="SoC", color="k", linestyle="--")
    plt.ylabel("BESS Energy Status [%]")
    ax2.legend(loc="upper right")
    plt.tight_layout()
    plt.show()


def plot_day_pvonly(start_day, end_day, max_export, pv_profile, pv_curt):
    start_day = start_day * 24
    end_day = end_day * 24 + 24
    day_range = np.arange(start_day, end_day)
    fig, ax1 = plt.subplots(figsize=(12, 6))
    plt.title("PV generation")
    plt.xlabel("Hour of the year [h]")
    plt.ylabel("Power [kW]")
    ax1.plot(day_range, pv_profile[day_range], label="PV", color="r")
    ax1.plot(day_range, pv_curt[day_range], label="PV Sold", color="b")
    ax1.axhline(max_export, color="g", linestyle="-.")
    plt.grid()
    plt.tight_layout()
    plt.show()


def plot_financial(duration, cumulative_cashflow):
    fig, ax1 = plt.subplots(figsize=(12, 6))
    ax1.bar(range(duration + 1), cumulative_cashflow)
    plt.title("Cumulative Cash-Flow and Break-Even Point")
    plt.xlabel(" Time [years]")
    plt.ylabel("Cash-flow [€]")
    plt.show()
