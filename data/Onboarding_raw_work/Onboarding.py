import polars as pL
import numpy as np
import matplotlib.pyplot as plt
import pyarrow.parquet as pq
from pathlib import Path


data_path = Path(__file__).parent / "software-data.parquet"
pd = pL.read_parquet(data_path)
pd = pd.fill_null(strategy="forward")
print(pd)

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

fig, axes = plt.subplots(2, 1, sharex=True)

axes[0].plot(time, meters_second(rpm), label="Speed (m/s)")
axes[0].set_ylabel("Speed (m/s)")
axes[0].grid(True)

axes[1].plot(time, brake, label="Brake Voltage (V)", color='orange')
axes[1].set_xlabel("Time (s)")
axes[1].set_ylabel("Brake sensor (raw)")
axes[1].grid(True)

pedal = pd["ETC_STATUS_PEDAL_TRAVEL"]

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


bracking_starts, braking_ends = find_periods(braking)
for s, e in zip(bracking_starts, braking_ends):
    print(f"{s:.2f} - {e:.2f}")

coasting_starts, coasting_ends = find_periods(coasting)
for s, e in zip(coasting_starts, coasting_ends):
    print(f"{s:.2f} - {e:.2f}")


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


lati = pd["VDM_GPS_Latitude"]
longi = pd["VDM_GPS_Longitude"]
altitude = pd["VDM_GPS_ALTITUDE"]

plt.figure(figsize=(8, 6))
plt.plot(longi, lati)
plt.xlabel("Longitude")
plt.ylabel("Latitude")
plt.title("Vehicle GPS Path")
plt.grid(True)
plt.axis('equal')

plt.figure(figsize=(8, 6))
plt.plot(time, altitude)
plt.xlabel("Time (s)")
plt.ylabel("Altitude (m)")
plt.title("Vehicle Altitude")
plt.grid(True)

plt.figure(figsize=(8, 6))
plt.scatter(longi, lati, c=time, cmap='viridis', s=10)
plt.colorbar(label='Time (s)')
plt.xlabel("Longitude")
plt.ylabel("Latitude")
plt.title("Vehicle GPS Path with Time")
plt.grid(True)
plt.axis('equal')
# plt.tight_layout()
plt.savefig("gps_path_with_time.png", dpi=300)
plt.xticks(rotation=45)

plt.figure(figsize=(8, 6))
plt.plot(time, longi, label="Longitude")
plt.xlabel("Time (s)")
plt.ylabel("Longitude")
plt.title("Vehicle GPS Path with Time")
plt.grid(True)


fig, axes = plt.subplots(2, 1, sharex=True)

axes[0].plot(time, longi, label="Longitude")
axes[0].set_ylabel("Longitude")
axes[0].grid(True)
axes[0].set_title("Longitude Over Time")

axes[1].plot(time, speed, label="Speed (m/s)", color='orange')
axes[1].set_xlabel("Time (s)")
axes[1].set_ylabel("Speed (m/s)")
axes[1].grid(True)
axes[1].set_title("Speed Over Time")

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

n = 42
delta_speed_1 = lap1_speed.diff(n)
delta_time_1 = lap1_times.diff(n)

acceleration = delta_speed_1 / delta_time_1
print(acceleration.max())
print(acceleration.arg_max())

delta_speed_2 = lap2_speed.diff(n)
delta_time_2 = lap2_times.diff(n)
acceleration2 = delta_speed_2 / delta_time_2
print(acceleration2.max())
print(acceleration2.arg_max())



full_acceleration = speed.diff(n) / time.diff(n)
gaining_speed = full_acceleration > 0

# find_periods merges gaps under 0.1 s and drops periods under 0.7 s
gain_starts, gain_ends = find_periods(gaining_speed)
for s, e in zip(gain_starts, gain_ends):
    print(f"gaining speed: {s:.2f} - {e:.2f}  ({e - s:.2f} s)")


def time_in_lap(starts, ends, lap_start, lap_end):
    # clip each period to the lap window, skip ones fully outside, add up the rest
    total = 0
    for s, e in zip(starts, ends):
        s = max(s, lap_start)
        e = min(e, lap_end)
        if e > s:
            print(f"   {s:.2f} - {e:.2f}  ({e - s:.2f} s)")
            total += e - s
    return total


print("Lap 1 time accelerating:")
lap1_acc_time = time_in_lap(gain_starts, gain_ends, 20, 68)
print(f"   total: {lap1_acc_time:.2f} s")

print("Lap 2 time accelerating:")
lap2_acc_time = time_in_lap(gain_starts, gain_ends, 95, 133)
print(f"   total: {lap2_acc_time:.2f} s")

# Step 5 coasting: no throttle, no brake, still moving (speed can go up or down, e.g. downhill)
no_throttle = pedal == 0
no_brake = brake <= 375
coasting_5 = no_throttle & no_brake & moving

coast_starts, coast_ends = find_periods(coasting_5)

print("Lap 1 time coasting:")
lap1_coast_time = time_in_lap(coast_starts, coast_ends, 20, 68)
print(f"   total: {lap1_coast_time:.2f} s")

print("Lap 2 time coasting:")
lap2_coast_time = time_in_lap(coast_starts, coast_ends, 95, 133)
print(f"   total: {lap2_coast_time:.2f} s")


# speed cut first, then the 1 s check on what's left
in_laps = lap_mask | lap_mask2
fast_enough = speed >= 5
coast_6 = coasting_5 & in_laps & fast_enough

c6_starts, c6_ends = find_periods(coast_6)

clean_starts = []
clean_ends = []
for s, e in zip(c6_starts, c6_ends):
    if e - s >= 1:
        clean_starts.append(s)
        clean_ends.append(e)

# keep each coast as its own time + speed segment (Step 7 needs dv/dt inside each one)
coast_segments = []
print("Step 6 clean coasts:")
for s, e in zip(clean_starts, clean_ends):
    seg_mask = (time >= s) & (time <= e) & fast_enough   # also drop the few dips under 5 m/s
    seg_time = time.filter(seg_mask)
    seg_speed = speed.filter(seg_mask)
    coast_segments.append((seg_time, seg_speed))
    print(f"   {s:.2f} - {e:.2f}  ({e - s:.2f} s)  speed {seg_speed.max():.2f} -> {seg_speed.min():.2f} m/s")


# done inside each coast so dv/dt never jumps from one coast to the next
all_dvdt = []
all_v2 = []
for seg_time, seg_speed in coast_segments:
    dvdt = seg_speed.diff() / seg_time.diff()   # real dt, segments have small holes
    v2 = seg_speed ** 2
    keep = dvdt.is_not_null()                   # first row of each segment has no previous reading
    all_dvdt += dvdt.filter(keep).to_list()
    all_v2 += v2.filter(keep).to_list()

all_dvdt = pL.Series(all_dvdt)
all_v2 = pL.Series(all_v2)
print(f"Step 7 points: {len(all_dvdt)}  (dv/dt mean {all_dvdt.mean():.3f} m/s^2)")

plt.figure(figsize=(8, 6))
plt.scatter(all_v2, all_dvdt, s=8, alpha=0.3)   # lots of overlapping points, so make them see-through
plt.axhline(0, color='gray', linewidth=1)
plt.xlabel("v^2 (m^2/s^2)")
plt.ylabel("dv/dt (m/s^2)")
plt.title("Coastdown: dv/dt vs v^2")
plt.grid(True)

# straight line fit: dv/dt = slope * v^2 + intercept
slope, intercept = np.polyfit(all_v2.to_numpy(), all_dvdt.to_numpy(), 1)

air_density = 1.225     # kg/m^3
mass = 221.4            # kg
m_eff = 244.08          # kg
g = 9.81                # m/s^2

drag_term = -slope * m_eff              # .5 * p * Cd * A
cda = drag_term / (0.5 * air_density)   # Cd * A in m^2
crr = -intercept * m_eff / (mass * g)

print(f"slope: {slope:.6f}  intercept: {intercept:.4f}")
print(f".5*p*Cd*A: {drag_term:.4f}  Cd*A: {cda:.4f} m^2  Crr: {crr:.4f}")

line_x = np.linspace(all_v2.min(), all_v2.max(), 100)
plt.plot(line_x, slope * line_x + intercept, color='red', linewidth=2, label="fit")

# each coast's average slowdown as a big dot, so the trend shows through the noise
for seg_time, seg_speed in coast_segments:
    avg_v2 = (seg_speed ** 2).mean()
    avg_dvdt = (seg_speed[-1] - seg_speed[0]) / (seg_time[-1] - seg_time[0])
    plt.scatter(avg_v2, avg_dvdt, s=80, color='black', zorder=3)
plt.scatter([], [], s=80, color='black', label="coast average")   # one legend entry for the dots
plt.legend()
plt.savefig("step7_dvdt_vs_v2.png", dpi=150)

# zoomed-in copy so the line and coast averages are readable
plt.ylim(-1, 0.5)
plt.savefig("step7_dvdt_vs_v2_zoom.png", dpi=150)


plt.show()






