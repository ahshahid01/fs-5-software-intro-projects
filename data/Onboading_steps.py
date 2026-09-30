import polars as pL
import matplotlib.pyplot as plt
import pyarrow.parquet as pq


pd = pL.read_parquet("C:\\Users\\Administrator\\fs-5-software-intro-projects\\data\\software-data.parquet")

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
plt.show()