# https://deeplearningcourses.com/c/artificial-intelligence-reinforcement-learning-in-python
# https://www.udemy.com/artificial-intelligence-reinforcement-learning-in-python
from __future__ import print_function, division

import pickle
from builtins import range
from matplotlib.pyplot import cm
# Note: you may need to update your version of future
# sudo pip install -U future

import numpy as np
import matplotlib.pyplot as plt
import random
import csv


# Constants used thorough the training env
# Data from https://saft4u.saftbatteries.com/en/iot/simulator/result/4919

# Real battery used: LSH 20
# Project parameters
#
#     Environment: Smart Agriculture & Environmental Preservation
#     Application: Air quality monitoring
#     Location: Outdoor
#     Geographic zone: Europe
#     Connectivity solution: LoRa
#     Data transmission: Every 10'
#     Life duration: 5 years
#     Cut-off Voltage: 2,2 V
#
# Consumption profile
#
#     Maximal peak current: 50 mA
#     Yearly consumption: 1,29 Ah
#     Total consumption: 6.45 Ah
#
import plot


T = 600  # seconds
BW = 125  # KHz
TDC = 1 / 100  # 1%
Q = 0.051  # Seconds
QMAX = 3600*TDC/Q
QR = T*TDC/Q
PACKET_SIZE = 26*8  # Bits
CAPACITY = 6.45  # Ah
VOLTAGE = 3.6  # V
CUT_OFF_VOLTAGE = 2.2  # V
MAX_BATTERY_LEVEL = CAPACITY * (VOLTAGE-CUT_OFF_VOLTAGE) * 3600  # J
ALL_ACTIONS = {
    "a1": {'CR': 4/5, 'SF': 7, 'alpha': -30.2580, 'beta': 0.2857, 'TXR': 3410, 'SNR': 0.0001778279},
    "a2": {'CR': 4/5, 'SF': 8, 'alpha': -77.1002, 'beta': 0.2993, 'TXR': 1841, 'SNR': 0.0000999999},
    "a3": {'CR': 4/5, 'SF': 9, 'alpha': -244.6424, 'beta': 0.3223, 'TXR': 1015, 'SNR': 0.0000562341},
    "a4": {'CR': 4/5, 'SF': 10, 'alpha': -725.9556, 'beta': 0.3340, 'TXR': 507, 'SNR': 0.0000316227},
    "a5": {'CR': 4/5, 'SF': 11, 'alpha': -2109.8064, 'beta': 0.3407, 'TXR': 253, 'SNR': 0.0000177827},
    "a6": {'CR': 4/5, 'SF': 12, 'alpha': -4452.3653, 'beta': 0.2217, 'TXR': 127, 'SNR': 0.0000099999},
    "a7": {'CR': 4/7, 'SF': 7, 'alpha': -105.1966, 'beta': 0.3746, 'TXR': 2663, 'SNR': 0.0001778279},
    "a8": {'CR': 4/7, 'SF': 8, 'alpha': -289.8133, 'beta': 0.3756, 'TXR': 1466, 'SNR': 0.0000999999},
    "a9": {'CR': 4/7, 'SF': 9, 'alpha': -1114.3312, 'beta': 0.3969, 'TXR': 816, 'SNR': 0.0000562341},
    "a10": {'CR': 4/7, 'SF': 10, 'alpha': -4285.4440, 'beta': 0.4116, 'TXR': 408, 'SNR': 0.0000316227},
    "a11": {'CR': 4/7, 'SF': 11, 'alpha': -20771.6945, 'beta': 0.4332, 'TXR': 204, 'SNR': 0.0000177827},
    "a12": {'CR': 4/7, 'SF': 12, 'alpha': -98658.1166, 'beta': 0.4485, 'TXR': 102, 'SNR': 0.0000099999}
}

def battery_life(action, N, MAX_BATTERY_LEVEL, T):
    config = list(ALL_ACTIONS.values())[action]
    cr = config.get("CR")
    sf = config.get("SF")
    payload = N*PACKET_SIZE/8  # bytes
    n_p = 8
    t_pr = (4.25 + n_p) * pow(2, sf) / BW
    p_sy = 8 + max(((8 * payload - 4 * sf + 44 - 20 * 1) / (4 * (sf - 2 * 1))) * (cr + 4), 0)
    t_pd = p_sy * pow(2, sf) / BW
    t = t_pr + t_pd
    e_pkt = 0.0924 * t  # J or Ws using Pt = 13 dBm
    battery_life = MAX_BATTERY_LEVEL * T / (e_pkt * 60 * 24 * 365)
    return battery_life

def plot_battery_life():
    N = np.linspace(1, 20, 40)
    labels = ['SF = 7', 'SF = 8', 'SF = 9', 'SF = 10', 'SF = 11', 'SF = 12']
    fig, ax1 = plt.subplots(nrows=1, ncols=1, figsize=(6, 3))
    ax1.grid()
    for a in range(round(len(ALL_ACTIONS) / 2)):
        y = []
        for i,n in enumerate(N):
            y.append(battery_life(a, n, MAX_BATTERY_LEVEL, T))
        ax1.plot(N, y, label=labels[a])
    ax1.set_ylabel('Battery life (Years)')
    ax1.set_xlabel('Number of external nodes (N)')
    ax1.set_xticks([1, 5, 10, 15, 20])
    plt.suptitle('Battery life (T = 600 s, CR = 4/5)')
    ax1.legend(loc='best')
    plt.tight_layout()
    plt.savefig('battery_life.png', dpi=400)
    plt.show()

def plot_pdr():
    pdr_opt = np.loadtxt('results/pdr_opt.txt', dtype=float, delimiter=',')
    pdr_1_1 = np.loadtxt('results/pdr_1_1.txt', dtype=float, delimiter=',')
    pdr_5_1 = np.loadtxt('results/pdr_5_1.txt', dtype=float, delimiter=',')
    pdr_10_1 = np.loadtxt('results/pdr_10_1.txt', dtype=float, delimiter=',')
    pdr_15_1 = np.loadtxt('results/pdr_15_1.txt', dtype=float, delimiter=',')
    pdr_20_1 = np.loadtxt('results/pdr_20_1.txt', dtype=float, delimiter=',')
    pdr_1_2 = np.loadtxt('results/pdr_1_2.txt', dtype=float, delimiter=',')
    pdr_5_2 = np.loadtxt('results/pdr_5_2.txt', dtype=float, delimiter=',')
    pdr_10_2 = np.loadtxt('results/pdr_10_2.txt', dtype=float, delimiter=',')
    pdr_15_2 = np.loadtxt('results/pdr_15_2.txt', dtype=float, delimiter=',')
    pdr_20_2 = np.loadtxt('results/pdr_20_2.txt', dtype=float, delimiter=',')
    pdr_1_3 = np.loadtxt('results/pdr_1_3.txt', dtype=float, delimiter=',')
    pdr_5_3 = np.loadtxt('results/pdr_5_3.txt', dtype=float, delimiter=',')
    pdr_10_3 = np.loadtxt('results/pdr_10_3.txt', dtype=float, delimiter=',')
    pdr_15_3 = np.loadtxt('results/pdr_15_3.txt', dtype=float, delimiter=',')
    pdr_20_3 = np.loadtxt('results/pdr_20_3.txt', dtype=float, delimiter=',')
    pdr_1_4 = np.loadtxt('results/pdr_1_4.txt', dtype=float, delimiter=',')
    pdr_5_4 = np.loadtxt('results/pdr_5_4.txt', dtype=float, delimiter=',')
    pdr_10_4 = np.loadtxt('results/pdr_10_4.txt', dtype=float, delimiter=',')
    pdr_15_4 = np.loadtxt('results/pdr_15_4.txt', dtype=float, delimiter=',')
    pdr_20_4 = np.loadtxt('results/pdr_20_4.txt', dtype=float, delimiter=',')
    pdr_1_5 = np.loadtxt('results/pdr_1_5.txt', dtype=float, delimiter=',')
    pdr_5_5 = np.loadtxt('results/pdr_10_5.txt', dtype=float, delimiter=',')
    pdr_10_5 = np.loadtxt('results/pdr_10_5.txt', dtype=float, delimiter=',')
    pdr_15_5 = np.loadtxt('results/pdr_15_5.txt', dtype=float, delimiter=',')
    pdr_20_5 = np.loadtxt('results/pdr_20_5.txt', dtype=float, delimiter=',')
    pdr_1_6 = np.loadtxt('results/pdr_1_6.txt', dtype=float, delimiter=',')
    pdr_5_6 = np.loadtxt('results/pdr_5_6.txt', dtype=float, delimiter=',')
    pdr_10_6 = np.loadtxt('results/pdr_10_6.txt', dtype=float, delimiter=',')
    pdr_15_6 = np.loadtxt('results/pdr_15_6.txt', dtype=float, delimiter=',')
    pdr_20_6 = np.loadtxt('results/pdr_20_6.txt', dtype=float, delimiter=',')

    np.warnings.filterwarnings('ignore', category=np.VisibleDeprecationWarning)
    nodes = [1, 5, 10, 15, 20]
    array = np.array([[pdr_opt, pdr_1_1, pdr_1_2, pdr_1_3, pdr_1_4, pdr_1_5, pdr_1_6],
                      [pdr_opt, pdr_5_1, pdr_5_2, pdr_5_3, pdr_5_4, pdr_5_5, pdr_5_6],
                      [pdr_opt, pdr_10_1, pdr_10_2, pdr_10_3, pdr_10_4, pdr_10_5, pdr_10_6],
                      [pdr_opt, pdr_15_1, pdr_15_2, pdr_15_3, pdr_15_4, pdr_15_5, pdr_15_6],
                      [pdr_opt, pdr_20_1, pdr_20_2, pdr_20_3, pdr_20_4, pdr_20_5, pdr_20_6]], dtype=object)
    color = ['black', 'burlywood', 'dimgray', 'cornflowerblue','thistle', 'mediumpurple', 'indigo']
    label_a = ['OPTIMAL', 'SF=7', 'SF=8', 'SF=9', 'SF=10', 'SF=11', 'SF=12']
    alpha = [0.8]
    shift = [-1.5, -1, -0.5, 0, 0.5, 1, 1.5]
    fig, ax1 = plt.subplots(nrows=1, ncols=1, figsize=(6, 4))
    ax1.grid(True)

    for n, node in enumerate(nodes):
        data = []
        for i in range(0, 7):
            ber = []
            data = array[n][i]
            for v in range(len(data)):
                ber.append(data[v])
            ber_mean = np.mean(ber)
            ber_std = np.std(ber)
            ax1.bar(nodes[n] + shift[i], ber_mean, yerr=ber_std,
                    error_kw=dict(ecolor='black', elinewidth=0.5, lolims=False), capsize=2, width=0.5, zorder=5,
                    color=color[i], alpha=alpha[0], label=label_a[i] if n == 0 else "")
        ax1.plot([], [], lw=5, color=color[i])
    ax1.set_ylabel('PDR')
    ax1.set_xlabel('NODES')
    ax1.legend(loc='best')
    ax1.set_ylim(0, 1)
    ax1.set_xlim(-5, 30)
    plt.tight_layout()
    plt.savefig('pdr.png', dpi=400)
    plt.show()

def plot_prr():
    prr_opt = np.loadtxt('results/prr_opt.txt', dtype=float, delimiter=',')
    prr_1_1 = np.loadtxt('results/prr_1_1.txt', dtype=float, delimiter=',')
    prr_5_1 = np.loadtxt('results/prr_5_1.txt', dtype=float, delimiter=',')
    prr_10_1 = np.loadtxt('results/prr_10_1.txt', dtype=float, delimiter=',')
    prr_15_1 = np.loadtxt('results/prr_15_1.txt', dtype=float, delimiter=',')
    prr_20_1 = np.loadtxt('results/prr_20_1.txt', dtype=float, delimiter=',')
    prr_1_2 = np.loadtxt('results/prr_1_2.txt', dtype=float, delimiter=',')
    prr_5_2 = np.loadtxt('results/prr_5_2.txt', dtype=float, delimiter=',')
    prr_10_2 = np.loadtxt('results/prr_10_2.txt', dtype=float, delimiter=',')
    prr_15_2 = np.loadtxt('results/prr_15_2.txt', dtype=float, delimiter=',')
    prr_20_2 = np.loadtxt('results/prr_20_2.txt', dtype=float, delimiter=',')
    prr_1_3 = np.loadtxt('results/prr_1_3.txt', dtype=float, delimiter=',')
    prr_5_3 = np.loadtxt('results/prr_5_3.txt', dtype=float, delimiter=',')
    prr_10_3 = np.loadtxt('results/prr_10_3.txt', dtype=float, delimiter=',')
    prr_15_3 = np.loadtxt('results/prr_15_3.txt', dtype=float, delimiter=',')
    prr_20_3 = np.loadtxt('results/prr_20_3.txt', dtype=float, delimiter=',')
    prr_1_4 = np.loadtxt('results/prr_1_4.txt', dtype=float, delimiter=',')
    prr_5_4 = np.loadtxt('results/prr_5_4.txt', dtype=float, delimiter=',')
    prr_10_4 = np.loadtxt('results/prr_10_4.txt', dtype=float, delimiter=',')
    prr_15_4 = np.loadtxt('results/prr_15_4.txt', dtype=float, delimiter=',')
    prr_20_4 = np.loadtxt('results/prr_20_4.txt', dtype=float, delimiter=',')
    prr_1_5 = np.loadtxt('results/prr_1_5.txt', dtype=float, delimiter=',')
    prr_5_5 = np.loadtxt('results/prr_10_5.txt', dtype=float, delimiter=',')
    prr_10_5 = np.loadtxt('results/prr_10_5.txt', dtype=float, delimiter=',')
    prr_15_5 = np.loadtxt('results/prr_15_5.txt', dtype=float, delimiter=',')
    prr_20_5 = np.loadtxt('results/prr_20_5.txt', dtype=float, delimiter=',')
    prr_1_6 = np.loadtxt('results/prr_1_6.txt', dtype=float, delimiter=',')
    prr_5_6 = np.loadtxt('results/prr_5_6.txt', dtype=float, delimiter=',')
    prr_10_6 = np.loadtxt('results/prr_10_6.txt', dtype=float, delimiter=',')
    prr_15_6 = np.loadtxt('results/prr_15_6.txt', dtype=float, delimiter=',')
    prr_20_6 = np.loadtxt('results/prr_20_6.txt', dtype=float, delimiter=',')

    np.warnings.filterwarnings('ignore', category=np.VisibleDeprecationWarning)
    nodes = [1, 5, 10, 15, 20]
    array = np.array([[prr_opt, prr_1_1, prr_1_2, prr_1_3, prr_1_4, prr_1_5, prr_1_6],
                      [prr_opt, prr_5_1, prr_5_2, prr_5_3, prr_5_4, prr_5_5, prr_5_6],
                      [prr_opt, prr_10_1, prr_10_2, prr_10_3, prr_10_4, prr_10_5, prr_10_6],
                      [prr_opt, prr_15_1, prr_15_2, prr_15_3, prr_15_4, prr_15_5, prr_15_6],
                      [prr_opt, prr_20_1, prr_20_2, prr_20_3, prr_20_4, prr_20_5, prr_20_6]], dtype=object)
    color = ['black', 'burlywood', 'dimgray', 'cornflowerblue','thistle', 'mediumpurple', 'indigo']
    label_a = ['OPTIMAL', 'SF=7', 'SF=8', 'SF=9', 'SF=10', 'SF=11', 'SF=12']
    alpha = [0.8]
    shift = [-1.5, -1, -0.5, 0, 0.5, 1, 1.5]
    fig, ax1 = plt.subplots(nrows=1, ncols=1, figsize=(7, 4))
    ax1.grid(True)

    for n, node in enumerate(nodes):
        data = []
        for i in range(0, 7):
            ber = []
            data = array[n][i]
            for v in range(len(data)):
                ber.append(data[v])
            ber_mean = np.mean(ber)
            ber_std = np.std(ber)
            ax1.bar(nodes[n] + shift[i], ber_mean, yerr=ber_std,
                    error_kw=dict(ecolor='black', elinewidth=0.5, lolims=False), capsize=2, width=0.5, zorder=5,
                    color=color[i], alpha=alpha[0], label=label_a[i] if n == 0 else "")
        ax1.plot([], [], lw=5, color=color[i])
    ax1.set_ylabel('PRR')
    ax1.set_xlabel('NODES')
    ax1.legend(loc='best')
    ax1.set_ylim(0, 1)
    ax1.set_xlim(-5, 30)
    plt.tight_layout()
    plt.savefig('prr.png', dpi=400)
    plt.show()

def plot_ber():
    ber_opt = np.loadtxt('results/ber_opt.txt', dtype=float, delimiter=',')
    ber_1_1 = np.loadtxt('results/ber_1_1.txt', dtype=float, delimiter=',')
    ber_5_1 = np.loadtxt('results/ber_5_1.txt', dtype=float, delimiter=',')
    ber_10_1 = np.loadtxt('results/ber_10_1.txt', dtype=float, delimiter=',')
    ber_15_1 = np.loadtxt('results/ber_15_1.txt', dtype=float, delimiter=',')
    ber_20_1 = np.loadtxt('results/ber_20_1.txt', dtype=float, delimiter=',')
    ber_1_2 = np.loadtxt('results/ber_1_2.txt', dtype=float, delimiter=',')
    ber_5_2 = np.loadtxt('results/ber_5_2.txt', dtype=float, delimiter=',')
    ber_10_2 = np.loadtxt('results/ber_10_2.txt', dtype=float, delimiter=',')
    ber_15_2 = np.loadtxt('results/ber_15_2.txt', dtype=float, delimiter=',')
    ber_20_2 = np.loadtxt('results/ber_20_2.txt', dtype=float, delimiter=',')
    ber_1_3 = np.loadtxt('results/ber_1_3.txt', dtype=float, delimiter=',')
    ber_5_3 = np.loadtxt('results/ber_5_3.txt', dtype=float, delimiter=',')
    ber_10_3 = np.loadtxt('results/ber_10_3.txt', dtype=float, delimiter=',')
    ber_15_3 = np.loadtxt('results/ber_15_3.txt', dtype=float, delimiter=',')
    ber_20_3 = np.loadtxt('results/ber_20_3.txt', dtype=float, delimiter=',')
    ber_1_4 = np.loadtxt('results/ber_1_4.txt', dtype=float, delimiter=',')
    ber_5_4 = np.loadtxt('results/ber_5_4.txt', dtype=float, delimiter=',')
    ber_10_4 = np.loadtxt('results/ber_10_4.txt', dtype=float, delimiter=',')
    ber_15_4 = np.loadtxt('results/ber_15_4.txt', dtype=float, delimiter=',')
    ber_20_4 = np.loadtxt('results/ber_20_4.txt', dtype=float, delimiter=',')
    ber_1_5 = np.loadtxt('results/ber_1_5.txt', dtype=float, delimiter=',')
    ber_5_5 = np.loadtxt('results/ber_10_5.txt', dtype=float, delimiter=',')
    ber_10_5 = np.loadtxt('results/ber_10_5.txt', dtype=float, delimiter=',')
    ber_15_5 = np.loadtxt('results/ber_15_5.txt', dtype=float, delimiter=',')
    ber_20_5 = np.loadtxt('results/ber_20_5.txt', dtype=float, delimiter=',')
    ber_1_6 = np.loadtxt('results/ber_1_6.txt', dtype=float, delimiter=',')
    ber_5_6 = np.loadtxt('results/ber_5_6.txt', dtype=float, delimiter=',')
    ber_10_6 = np.loadtxt('results/ber_10_6.txt', dtype=float, delimiter=',')
    ber_15_6 = np.loadtxt('results/ber_15_6.txt', dtype=float, delimiter=',')
    ber_20_6 = np.loadtxt('results/ber_20_6.txt', dtype=float, delimiter=',')

    np.warnings.filterwarnings('ignore', category=np.VisibleDeprecationWarning)
    nodes = [1, 5, 10, 15, 20]
    array = np.array([[ber_opt, ber_1_1, ber_1_2, ber_1_3, ber_1_4, ber_1_5, ber_1_6],
                      [ber_opt, ber_5_1, ber_5_2, ber_5_3, ber_5_4, ber_5_5, ber_5_6],
                      [ber_opt, ber_10_1, ber_10_2, ber_10_3, ber_10_4, ber_10_5, ber_10_6],
                      [ber_opt, ber_15_1, ber_15_2, ber_15_3, ber_15_4, ber_15_5, ber_15_6],
                      [ber_opt, ber_20_1, ber_20_2, ber_20_3, ber_20_4, ber_20_5, ber_20_6]], dtype=object)
    color = ['black', 'burlywood', 'dimgray', 'cornflowerblue','thistle', 'mediumpurple', 'indigo']
    label_a = ['OPTIMAL', 'SF=7', 'SF=8', 'SF=9', 'SF=10', 'SF=11', 'SF=12']
    alpha = [0.8]
    shift = [-1.5, -1, -0.5, 0, 0.5, 1, 1.5]
    fig, ax1 = plt.subplots(nrows=1, ncols=1, figsize=(6, 4))
    ax1.grid(True)

    for n, node in enumerate(nodes):
        data = []
        for i in range(0, 7):
            ber = []
            data = array[n][i]
            for v in range(len(data)):
                ber.append(data[v])
            ber_mean = np.mean(ber)
            ber_std = np.std(ber)
            ax1.bar(nodes[n] + shift[i], ber_mean, yerr=ber_std,
                    error_kw=dict(ecolor='black', elinewidth=0.5, lolims=False), capsize=2, width=0.5, zorder=5,
                    color=color[i], alpha=alpha[0], label=label_a[i] if n == 0 else "")
        ax1.plot([], [], lw=5, color=color[i])
    ax1.set_ylabel('BER')
    ax1.set_xlabel('NODES')
    ax1.legend(loc='best')
    ax1.set_ylim(0.00000, 0.00030)
    ax1.set_xlim(-5, 30)
    plt.tight_layout()
    plt.savefig('ber.png', dpi=400)
    plt.show()

def plot_energy():
    energy_opt = np.loadtxt('results/energy_opt.txt', dtype=float, delimiter=',')
    energy_1_1 = np.loadtxt('results/energy_1_1.txt', dtype=float, delimiter=',')
    energy_5_1 = np.loadtxt('results/energy_5_1.txt', dtype=float, delimiter=',')
    energy_10_1 = np.loadtxt('results/energy_10_1.txt', dtype=float, delimiter=',')
    energy_15_1 = np.loadtxt('results/energy_15_1.txt', dtype=float, delimiter=',')
    energy_20_1 = np.loadtxt('results/energy_20_1.txt', dtype=float, delimiter=',')
    energy_1_2 = np.loadtxt('results/energy_1_2.txt', dtype=float, delimiter=',')
    energy_5_2 = np.loadtxt('results/energy_5_2.txt', dtype=float, delimiter=',')
    energy_10_2 = np.loadtxt('results/energy_10_2.txt', dtype=float, delimiter=',')
    energy_15_2 = np.loadtxt('results/energy_15_2.txt', dtype=float, delimiter=',')
    energy_20_2 = np.loadtxt('results/energy_20_2.txt', dtype=float, delimiter=',')
    energy_1_3 = np.loadtxt('results/energy_1_3.txt', dtype=float, delimiter=',')
    energy_5_3 = np.loadtxt('results/energy_5_3.txt', dtype=float, delimiter=',')
    energy_10_3 = np.loadtxt('results/energy_10_3.txt', dtype=float, delimiter=',')
    energy_15_3 = np.loadtxt('results/energy_15_3.txt', dtype=float, delimiter=',')
    energy_20_3 = np.loadtxt('results/energy_20_3.txt', dtype=float, delimiter=',')
    energy_1_4 = np.loadtxt('results/energy_1_4.txt', dtype=float, delimiter=',')
    energy_5_4 = np.loadtxt('results/energy_5_4.txt', dtype=float, delimiter=',')
    energy_10_4 = np.loadtxt('results/energy_10_4.txt', dtype=float, delimiter=',')
    energy_15_4 = np.loadtxt('results/energy_15_4.txt', dtype=float, delimiter=',')
    energy_20_4 = np.loadtxt('results/energy_20_4.txt', dtype=float, delimiter=',')
    energy_1_5 = np.loadtxt('results/energy_1_5.txt', dtype=float, delimiter=',')
    energy_5_5 = np.loadtxt('results/energy_10_5.txt', dtype=float, delimiter=',')
    energy_10_5 = np.loadtxt('results/energy_10_5.txt', dtype=float, delimiter=',')
    energy_15_5 = np.loadtxt('results/energy_15_5.txt', dtype=float, delimiter=',')
    energy_20_5 = np.loadtxt('results/energy_20_5.txt', dtype=float, delimiter=',')
    energy_1_6 = np.loadtxt('results/energy_1_6.txt', dtype=float, delimiter=',')
    energy_5_6 = np.loadtxt('results/energy_5_6.txt', dtype=float, delimiter=',')
    energy_10_6 = np.loadtxt('results/energy_10_6.txt', dtype=float, delimiter=',')
    energy_15_6 = np.loadtxt('results/energy_15_6.txt', dtype=float, delimiter=',')
    energy_20_6 = np.loadtxt('results/energy_20_6.txt', dtype=float, delimiter=',')

    np.warnings.filterwarnings('ignore', category=np.VisibleDeprecationWarning)
    nodes = [1, 5, 10, 15, 20]
    array = np.array([[energy_opt, energy_1_1, energy_1_2, energy_1_3, energy_1_4, energy_1_5, energy_1_6],
                      [energy_opt, energy_5_1, energy_5_2, energy_5_3, energy_5_4, energy_5_5, energy_5_6],
                      [energy_opt, energy_10_1, energy_10_2, energy_10_3, energy_10_4, energy_10_5, energy_10_6],
                      [energy_opt, energy_15_1, energy_15_2, energy_15_3, energy_15_4, energy_15_5, energy_15_6],
                      [energy_opt, energy_20_1, energy_20_2, energy_20_3, energy_20_4, energy_20_5, energy_20_6]], dtype=object)
    color = ['black', 'burlywood', 'dimgray', 'cornflowerblue', 'thistle', 'mediumpurple', 'indigo']
    label_a = ['OPTIMAL', 'SF=7', 'SF=8', 'SF=9', 'SF=10', 'SF=11', 'SF=12']
    alpha = [0.8]
    shift = [-1.5, -1, -0.5, 0, 0.5, 1, 1.5]
    fig, ax1 = plt.subplots(nrows=1, ncols=1, figsize=(7, 4))
    ax1.grid(True)

    for n, node in enumerate(nodes):
        data = []
        for i in range(0, 7):
            ber = []
            data = array[n][i]
            for v in range(len(data)):
                ber.append(data[v])
            ber_mean = np.mean(ber)
            ber_std = np.std(ber)
            ax1.bar(nodes[n] + shift[i], ber_mean, yerr=ber_std,
                    error_kw=dict(ecolor='black', elinewidth=0.5, lolims=False), capsize=2, width=0.5, zorder=5,
                    color=color[i], alpha=alpha[0], label=label_a[i] if n == 0 else "")
        ax1.plot([], [], lw=5, color=color[i])
    ax1.set_ylabel('ENERGY (J)')
    ax1.set_xlabel('NODES')
    ax1.legend(loc='best')
    ax1.set_xlim(-5, 30)
    plt.tight_layout()
    plt.savefig('energy.png', dpi=400)
    plt.show()

def plot_energy_iterations():
    energy_opt = np.loadtxt('results/energy_opt.txt', dtype=float, delimiter=',')
    energy_1_1 = np.loadtxt('results/energy_1_1.txt', dtype=float, delimiter=',')
    energy_10_1 = np.loadtxt('results/energy_10_1.txt', dtype=float, delimiter=',')
    energy_20_1 = np.loadtxt('results/energy_20_1.txt', dtype=float, delimiter=',')
    energy_1_3 = np.loadtxt('results/energy_1_3.txt', dtype=float, delimiter=',')
    energy_10_3 = np.loadtxt('results/energy_10_3.txt', dtype=float, delimiter=',')
    energy_20_3 = np.loadtxt('results/energy_20_3.txt', dtype=float, delimiter=',')
    energy_1_6 = np.loadtxt('results/energy_1_6.txt', dtype=float, delimiter=',')
    energy_10_6 = np.loadtxt('results/energy_10_6.txt', dtype=float, delimiter=',')
    energy_20_6 = np.loadtxt('results/energy_20_6.txt', dtype=float, delimiter=',')

    array = np.array([energy_opt, energy_1_1, energy_10_1, energy_20_1, energy_1_3, energy_10_3, energy_20_3, energy_1_6,energy_10_6, energy_20_6], dtype=object)

    z = []  # array para coger las iteraciones de cada array
    for a, algorithm in enumerate(array):
        values = algorithm
        lengths = len(algorithm)
        z.append(lengths)
    labels = ['OPTIMAL', 'SF=7 N=1', 'SF=7 N=10', 'SF=7 N=20', 'SF=9 N=1', 'SF=9 N=10', 'SF=9 N=20', 'SF=12 N=1',
              'SF=12 N=10', 'SF=12 N=20']
    fig, ax1 = plt.subplots(nrows=1, ncols=1, figsize=(7, 5))
    ax1.grid()
    for r, ar in enumerate(array):
        y = []
        energy = array[r]
        for i in range(len(energy)):
            y.append(energy[i])
        N = np.linspace(0, z[r], z[r])
        ax1.plot(N, y, label=labels[r])
    ax1.set_ylabel('ENERGY (J)')
    ax1.set_xlabel('Iterations')
    ax1.legend(loc='best')
    ax1.set_ylim(0, 32500)
    ax1.set_xlim(0, 5000)
    plt.tight_layout()
    plt.savefig('Energy_iterations.png', dpi=400)
    plt.show()

#plot_battery_life()
plot_pdr()
#plot_prr()
#plot_ber()
#plot_energy()
#plot_energy_iterations()
