import numpy as np


def get_tariff(t_profile, ppa):
    tariff_profile = t_profile.copy()
    for i, x in enumerate(tariff_profile):
        tariff_profile[i] = ppa[x]
    tariff_profile = np.array(tariff_profile)
    tariff = tariff_profile
    for _ in range(364):
        tariff = np.append(tariff, tariff_profile)
    return tariff


def get_dispatch(pv_profile: np.ndarray, max_export: float, bess_energy: float, bess_power: float, max_soc: float,
                 min_soc: float, tariff_profile: np.ndarray):
    soc = min_soc
    charge_profile = np.zeros(len(pv_profile))
    discharge_profile = np.zeros(len(pv_profile))
    soc_profile = np.zeros(len(pv_profile))
    control = np.zeros(len(pv_profile))
    excess_profile = pv_profile - max_export
    for i, excess in enumerate(excess_profile):
        if excess < 0 and tariff_profile[i] > 0 and soc > min_soc:
            available_energy = (soc - min_soc) * bess_energy
            discharged_energy = np.min((-excess, bess_power, available_energy))
            soc = soc - discharged_energy / bess_energy
            discharge_profile[i] = discharged_energy
            control[i] = 2
        elif excess > 0 and soc < max_soc:
            available_space = (max_soc - soc) * bess_energy
            charged_energy = np.min((available_space, bess_power, excess))
            soc = soc + charged_energy / bess_energy
            charge_profile[i] = charged_energy
            control[i] = 1
        soc_profile[i] = soc
    return soc_profile, charge_profile, discharge_profile, control


def get_dispatch_controlled(pv_profile: np.ndarray, max_export: float, bess_energy: float, bess_power: float,
                            max_soc: float,
                            min_soc: float, control: np.ndarray):
    soc = min_soc
    charge_profile = np.zeros(len(pv_profile))
    discharge_profile = np.zeros(len(pv_profile))
    soc_profile = np.zeros(len(pv_profile))
    excess_profile = pv_profile - max_export
    for i, excess in enumerate(excess_profile):
        # if control[i] == 0 do nothing
        if control[i] == 1 and excess > 0 and soc < max_soc:  # charging
            available_space = (max_soc - soc) * bess_energy
            charged_energy = np.min((available_space, bess_power, excess))
            soc = soc + charged_energy / bess_energy
            charge_profile[i] = charged_energy
        if control[i] == 2 and excess < 0 and soc > min_soc:  # discharging
            available_energy = (soc - min_soc) * bess_energy
            discharged_energy = np.min((-excess, bess_power, available_energy))
            soc = soc - discharged_energy / bess_energy
            discharge_profile[i] = discharged_energy
        soc_profile[i] = soc
    return soc_profile, charge_profile, discharge_profile
