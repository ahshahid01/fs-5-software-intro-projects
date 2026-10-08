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

# fig, axes = plt.subplots(2, 1, sharex=True)

# axes[0].plot(time, meters_second(rpm), label="Speed (m/s)")
# axes[0].set_ylabel("Speed (m/s)")
# axes[0].grid(True)

# axes[1].plot(time, brake, label="Brake Voltage (V)", color='orange')
# axes[1].set_xlabel("Time (s)")
# axes[1].set_ylabel("Brake sensor (raw)")
# axes[1].grid(True)

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
#for s, e in zip(acc_starts, acc_ends):
    #print(f"{s:.2f} - {e:.2f}")


bracking_starts, braking_ends = find_periods(braking)
#for s, e in zip(bracking_starts, braking_ends):
    #print(f"{s:.2f} - {e:.2f}")

coasting_starts, coasting_ends = find_periods(coasting)
#for s, e in zip(coasting_starts, coasting_ends):
    #print(f"{s:.2f} - {e:.2f}")


# fig, axes = plt.subplots(3, 1, sharex=True)

# axes[0].plot(time, meters_second(rpm), label="Speed (m/s)")
# axes[0].set_ylabel("Speed (m/s)")
# axes[0].grid(True)
# axes[0].set_title("Coasting")
# for s, e in zip(coasting_starts, coasting_ends):
#     axes[0].axvspan(s, e, color='blue', alpha=0.3)

# axes[1].plot(time, brake, label="Braking", color='orange')
# axes[1].set_ylabel("Brake sensor (raw)")
# axes[1].grid(True)
# axes[1].set_title("Braking")
# for s, e in zip(bracking_starts, braking_ends):
#     axes[1].axvspan(s, e, color='red', alpha=0.3)

# axes[2].plot(time, pedal, label="Acceleration", color='green')
# axes[2].set_xlabel("Time (s)")
# axes[2].set_ylabel("Pedal sensor %")
# axes[2].grid(True)
# axes[2].set_title("Accelerating")
# for s, e in zip(acc_starts, acc_ends):
#     axes[2].axvspan(s, e, color='green', alpha=0.3)

# plt.tight_layout()


lati = pd["VDM_GPS_Latitude"]
longi = pd["VDM_GPS_Longitude"]
altitude = pd["VDM_GPS_ALTITUDE"]

# plt.figure(figsize=(8, 6))
# plt.plot(longi, lati)
# plt.xlabel("Longitude")
# plt.ylabel("Latitude")
# plt.title("Vehicle GPS Path")
# plt.grid(True)
# plt.axis('equal')

# # plt.figure(figsize=(8, 6))
# # plt.plot(time, altitude)
# # plt.xlabel("Time (s)")
# # plt.ylabel("Altitude (m)")
# # plt.title("Vehicle Altitude")
# # plt.grid(True)

# plt.figure(figsize=(8, 6))
# plt.scatter(longi, lati, c=time, cmap='viridis', s=10)
# plt.colorbar(label='Time (s)')
# plt.xlabel("Longitude")
# plt.ylabel("Latitude")
# plt.title("Vehicle GPS Path with Time")
# plt.grid(True)
# plt.axis('equal')
# # plt.tight_layout()
# plt.savefig("gps_path_with_time.png", dpi=300)
# plt.xticks(rotation=45)

# plt.figure(figsize=(8, 6))
# plt.plot(time, longi, label="Longitude")
# plt.xlabel("Time (s)")
# plt.ylabel("Longitude")
# plt.title("Vehicle GPS Path with Time")
# plt.grid(True)


# fig, axes = plt.subplots(2, 1, sharex=True)

# axes[0].plot(time, longi, label="Longitude")
# axes[0].set_ylabel("Longitude")
# axes[0].grid(True)
# axes[0].set_title("Longitude Over Time")

# axes[1].plot(time, speed, label="Speed (m/s)", color='orange')
# axes[1].set_xlabel("Time (s)")
# axes[1].set_ylabel("Speed (m/s)")
# axes[1].grid(True)
# axes[1].set_title("Speed Over Time")

after_start_1 = (time >= 20)
before_end_1 = (time <= 68)
after_start_2 = (time >= 95)
before_end_2 = (time <= 133)

lap_mask = after_start_1 & before_end_1
lap1_times = time.filter(lap_mask)
lap1_speed = speed.filter(lap_mask)

lap_mask2 = after_start_2 & before_end_2
lap2_times = time.filter(lap_mask2)
lap2_speed = speed.filter(lap_mask2)

delta_speed_1 = lap1_speed.diff()
delta_time_1 = lap1_times.diff()

acceleration = delta_speed_1 / delta_time_1

row_number = acceleration.arg_max()

for j in range(row_number - 10, row_number + 11):
    print(f"{lap1_times[j]:.3f} - {lap1_speed[j]:.3f} - {acceleration[j]:.3f}")

# print(lap1_times.first(), lap1_times.last(), lap1_speed.max())
# print(lap1_times.count(), lap1_times, lap1_speed)
# print("")

# print(lap2_times.first(), lap2_times.last(), lap2_speed.max())
# print(lap2_times.count(), lap2_times, lap2_speed)
# print("")

plt.show()






