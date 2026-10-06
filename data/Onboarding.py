import polars as pL
import matplotlib.pyplot as plt
import pyarrow.parquet as pq
from pathlib import Path


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
print(brake.describe())

#pick a threshold for braking "ETC_STATUS_BRAKE_SENSE_VOLTAGE"
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
axes[1].set_ylabel("Brake senor (raw)")
axes[1].grid(True)

plt.show()

