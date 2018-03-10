#!/usr/bin/env python
import psutil
import time
import matplotlib.pyplot as plt
import sys
#https://pypi.python.org/pypi/psutil

plot_time = int(sys.argv[1]) if len(sys.argv) > 1 else 3
plot_folder = sys.argv[2] if len(sys.argv) > 2 else '.'
plot=[]
for v in psutil.cpu_times():
    plot.append([])
for i in range(plot_time):
    print (psutil.cpu_times())
    for i, v in enumerate(psutil.cpu_times()):
        plot[i].append(v)
    time.sleep(1)

for i, label in enumerate(['user','nice','system','idle', 'iowait', 'irq', 'softirq', 'steal', 'guest', 'guest_nice']):
    avg = sum(plot[i]) / len(plot[i])
    plt.plot(plot[i], label=label+" %.0f" % avg)
plt.legend(loc=2, prop={'size': 6})
plt.savefig(plot_folder+'/cpu.png', dpi=200)
