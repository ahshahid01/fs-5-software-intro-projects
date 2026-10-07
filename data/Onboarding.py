import polars as pL
import numpy as np
import matplotlib.pyplot as plt
import pyarrow.parquet as pq
from pathlib import Path

#pL.Config.set_tbl_rows(-1)


data_path = Path(__file__).parent / "software-data.parquet"
pd = pL.read_parquet(data_path)
pd = pd.fill_null(strategy="forward")

rpm = pd["SME_TRQSPD_Speed"]
time = pd["Time"]

gear_ratio = 12/41
radius = .2                             #in meters
diameter = 2 * radius                   #in meters
diamter_inches = diameter * 39.3701     #in inches


def meters_second(rpm):
    speed_mps = (rpm * gear_ratio * 2 * 3.14159 * radius) / 60  # Convert rpm to m/s
    return speed_mps

plt.plot(time, meters_second(rpm))
plt.xlabel("Time (s)")
plt.ylabel("Speed (m/s)")
plt.title("Vehicle Speed Over Time")
plt.grid(True)

brake = pd["ETC_STATUS_BRAKE_SENSE_VOLTAGE"]
#print(brake.describe())

#pick a threshold for braking "ETC_STATUS_BRAKE_SENSE_VOLTAGE"
#   - threshold given is 375
#use "ETC_STATUS_PEDAL_TRAVEL" to find acceleration
#   - also needs a threshold
#Find coasting if niether is true
#overlay on graph to label

fig, axes = plt.subplots(2, 1, sharex=True)

axes[0].plot(time, meters_second(rpm), label="Speed (m/s)")
axes[0].set_ylabel("Speed (m/s)")
axes[0].grid(True)

axes[1].plot(time, brake, label="Brake Voltage (V)", color='orange')
axes[1].set_xlabel("Time (s)")
axes[1].set_ylabel("Brake sensor (raw)")
axes[1].grid(True)

#plt.show()

pedal = pd["ETC_STATUS_PEDAL_TRAVEL"]
#print(time.filter((pedal > 0) & (pedal < 5)))

speed = meters_second(rpm)
moving = speed > 0.1
braking = (brake > 375) & moving                # brake pressed and car moving
accelerating = (pedal > 0) & moving             # throttle pressed and car moving
coasting = (moving) & ~braking & ~accelerating  # no throttle/brake but moving
parked = ~moving                                # car not moving


def find_periods(condition):
    total_periods = time.filter(condition)
    gaps = total_periods.diff()
    starts = total_periods.filter(gaps > .1)
    ends = total_periods.shift(1).filter(gaps > .1)
    
    starts = starts.to_list()
    ends = ends.to_list()
    total_periods = total_periods.to_list()
    starts = [total_periods[0]] + starts
    ends = ends + [total_periods[-1]]

    filtered_starts = []
    filtered_ends = []
    for s, e in zip(starts, ends):
        if e - s > 0.7:
            filtered_starts.append(s)
            filtered_ends.append(e)

    return filtered_starts, filtered_ends
        


acc_starts, acc_ends = find_periods(accelerating)
for s, e in zip(acc_starts, acc_ends):
    print(f"{s:.2f} - {e:.2f}")
print("")

bracking_starts, braking_ends = find_periods(braking)
for s, e in zip(bracking_starts, braking_ends):
    print(f"{s:.2f} - {e:.2f}")
print("")

coasting_starts, coasting_ends = find_periods(coasting)
for s, e in zip(coasting_starts, coasting_ends):
    print(f"{s:.2f} - {e:.2f}")
print("")

fig, axes = plt.subplots(3, 1, sharex=True)

axes[0].plot(time, meters_second(rpm), label="Speed (m/s)")
axes[0].set_ylabel("Speed (m/s)")
axes[0].grid(True)
axes[0].set_title("Coasting")
for s, e in zip(coasting_starts, coasting_ends):
    axes[0].axvspan(s, e, color='blue', alpha=0.3)

axes[1].plot(time, brake, label="Braking", color='orange')
axes[1].set_ylabel("Brake sensor (raw)")
axes[1].grid(True)
axes[1].set_title("Braking")
for s, e in zip(bracking_starts, braking_ends):
    axes[1].axvspan(s, e, color='red', alpha=0.3)

axes[2].plot(time, pedal, label="Acceleration", color='green')
axes[2].set_xlabel("Time (s)")
axes[2].set_ylabel("Pedal sensor %")
axes[2].grid(True)
axes[2].set_title("Accelerating")
for s, e in zip(acc_starts, acc_ends):
    axes[2].axvspan(s, e, color='green', alpha=0.3)

plt.tight_layout()
plt.show()

#print(braking.sum())
#print(accelerating.sum())
#print(coasting.sum())
#print(parked.sum())




