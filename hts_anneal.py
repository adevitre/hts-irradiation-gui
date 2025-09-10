# A library to process annealing experiments in the i3HTS chamber at MIT's Plasma Science & Fusion Center
# @author Alexis Devitre
# @last-mod July 31st, 2025

import scipy, pandas as pd, numpy as np, matplotlib.pyplot as plt


def fname_to_timestamp(fname):
    y, m, d = [int(n) for n in fname.split('_')[1].split('-')]
    hh, mm, us = fname.split('_')[2].split('-')
    hh, mm, ss, us = int(hh), int(mm), int(us[:2]), int(us[2:])
    return pd.Timestamp(year=y, month=m, day=d, hour=hh, minute=mm, second=ss, microsecond=us)

def readEnvironmentFile(fpath):
    return pd.read_csv(fpath, sep='\s+', parse_dates={'datetime' : [0, 1]}, date_format={'date':'%d/%m/%y', 'timestamp':'%H:%M:%S.%f'})

def replace_zeros_with_nearest_avg(values, window=10):
    non_zero_indices = np.where(values != 0)[0]
    new_values = []
    
    if len(non_zero_indices) < window:
        raise ValueError("Not enough non-zero elements to compute average.")

    for i, value in enumerate(values):
        if value == 0:
            distances = np.abs(non_zero_indices - i)
            nearest_indices = non_zero_indices[np.argsort(distances)[:window]]
            new_values.append(np.mean(values[nearest_indices]))
        else:
            new_values.append(values[i])
    return new_values

def concatenateEnvironmentFiles(fpaths, vb=False):
    i, deltaT = 0, 0
    data = readEnvironmentFile(fpaths[0])

    for fpath in fpaths[1:]:
        nextdata = readEnvironmentFile(fpath)
        deltaT = (nextdata.iloc[0].datetime-data.iloc[-1].datetime).total_seconds()
        nextdata['time_s'] += data.time_s.values[-1] + deltaT
        missing_times = np.arange(data.time_s.values[-1], nextdata.time_s.values[0], data.time_s[-20:].diff().mean())

        data = pd.concat([data, pd.DataFrame({'time_s': missing_times}), nextdata], ignore_index=True)
        data = data.sort_values('time_s').interpolate(method='linear').reset_index(drop=True)
    
    if vb:
        fig, ax = plt.subplots(figsize=(9, 4))
        if 'temperature' in fpaths[0]:
            ax.plot(data.time_s, data.targetT_K, color='r')
            ax.plot(data.time_s, data.sampleT_K, color='b')
            ax.set_ylim(0, 300)
            ax.set_xlim(0, data.time_s.max())
        else:
            ax.semilogy(data.time_s, data.pressure_torr, color='g')
            ax.set_ylim(1e-8, 1e3)
            ax.set_xlim(0, data.time_s.max())
    return data


def get_thermal_budget(step_data, Ea=0.08, vb=True):
    '''
        get_thermal_buget obtains the characteristic quantities from an anneal cycle
        
        input
        -------
        step_data (pandas.Dataframe) - contains at least 3 columns named sampleT_K, datetime, and setpt_K
        Ea (float)                   - activation energy for the annealing process
        
        returns
        -------
        anneal_time (float)               - time at temperature
        anneal_temperature_mean (float)   - mean anneal temeprature
        anneal_temperature_std (float)    - standard deviation of the anneal temperature
        thermal_budget (float)            - time integral of exp(-Ea/kb*T)
        tstart (datetime)                 - Start of the range over which thermal budget is calculated
        tstop (datetime)                  - End of the range over which thermal budget is calculated
    '''
    
    step_data['temperature'] = replace_zeros_with_nearest_avg(step_data.sampleT_K.copy().values)
    step_data_upper_part = step_data[0.9*step_data.temperature.max() < step_data.temperature]
    derivative = (1e3*step_data_upper_part.temperature.diff()/step_data_upper_part.time_s.diff()).rolling(40).mean()
    step_data_top_shelf = step_data_upper_part[derivative.abs() < 3]
    
    anneal_temperature_median = step_data_top_shelf.temperature.median()
    anneal_temperature_std = step_data_top_shelf.temperature.std()
    
    step_data_above_median = step_data[(anneal_temperature_median - anneal_temperature_std) <= step_data.temperature]
    
    thermal_budget = np.trapz(y=np.exp(-Ea*scipy.constants.electron_volt/(scipy.constants.Boltzmann*step_data.temperature)), x=step_data.time_s)
    anneal_temperature_mean = step_data_above_median.temperature.mean()
    anneal_temperature_std = step_data_above_median.temperature.std()
    anneal_time = step_data_above_median.datetime.iloc[-1] - step_data_above_median.datetime.iloc[0]
    
    if vb:
        
        fig, ax = plt.subplots()
        ax.set_ylim(-50, 450)
        ax.set_xlabel('Time stamp')
        ax.set_ylabel('Temperature [K]')
        ax.set_title('Thermal budget analysis')
        ax.plot(step_data.datetime, step_data.setpt_K, color='gray', alpha=.3, label='Setpoint')
        ax.plot(step_data.datetime, step_data.temperature, color='k', zorder=0, label='step data')
        ax.plot(step_data_upper_part.datetime, step_data_upper_part.temperature, color='k', linewidth=8, zorder=-2, label='Above 90% step')
        ax.plot(step_data_upper_part.datetime, derivative, color='r', label='Derivative step upper part')
        ax.plot(step_data_top_shelf.datetime, step_data_top_shelf.temperature, color='white', zorder=1, linewidth=1, label='|Derivative| < 3 K/s')
        ax.plot(step_data_above_median.datetime, step_data_above_median.temperature, color='r', linewidth=4, zorder=-1, label='Above median-std')
        ax.legend(loc='upper center')
        
    return anneal_time.total_seconds(), anneal_temperature_mean, anneal_temperature_std, thermal_budget