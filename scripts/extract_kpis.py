#!/usr/bin/env python3
import xml.etree.ElementTree as ET
import statistics
import os
import math
import sys

def calculate_percentile(data, pct=0.85):
    """Calculates the given percentile of a list of numbers using linear interpolation."""
    if not data:
        return 0.0
    sorted_data = sorted(data)
    index = pct * (len(sorted_data) - 1)
    lower = sorted_data[math.floor(index)]
    upper = sorted_data[math.ceil(index)]
    return lower + (upper - lower) * (index - math.floor(index))

def calculate_variance(data):
    """Calculates the sample variance of a list of numbers, returning 0.0 if not enough data points."""
    if len(data) < 2:
        return 0.0
    return statistics.variance(data)

# ==========================================
# CONFIGURATION
# ==========================================
# Analysis Time Window (seconds)
# Minutes 15 to 75 -> 15*60 = 900s, 75*60 = 4500s
START_TIME = 900.0
END_TIME = 4500.0

# Thresholds for Safety KPIs
TTC_THRESHOLD = 1.0      # seconds (incidents if minTTC < threshold)
DRAC_THRESHOLD = 4.9     # m/s^2 (hard braking if maxDRAC >= threshold, ~0.5G)

# Dynamically set base folder from argument or default
target_folder = sys.argv[1] if len(sys.argv) > 1 else "Baseline 2021"
TRIPINFO_FILE = os.path.join(target_folder, "Tripinfo.xml")
SSM_FILE = os.path.join(target_folder, "SSM.xml")
# ==========================================

def analyze_safety(ssm_filepath):
    """Parses safety metrics from SSM log XML file."""
    if not os.path.exists(ssm_filepath):
        print(f"Error: SSM file not found at {ssm_filepath}")
        return None

    print(f"Parsing safety metrics from: {ssm_filepath}...")
    
    total_conflicts_in_window = 0
    ttc_incidents = 0
    hard_braking_events = 0
    
    # Use ElementTree to parse the file
    tree = ET.parse(ssm_filepath)
    root = tree.getroot()
    
    for conflict in root.findall('conflict'):
        begin_str = conflict.get('begin')
        if begin_str is None:
            continue
        
        begin_time = float(begin_str)
        # Filter by time window
        if not (START_TIME <= begin_time < END_TIME):
            continue
            
        total_conflicts_in_window += 1
        
        # Check minTTC
        min_ttc_elem = conflict.find('minTTC')
        if min_ttc_elem is not None:
            ttc_val_str = min_ttc_elem.get('value')
            if ttc_val_str is not None and ttc_val_str != 'NA':
                try:
                    ttc_val = float(ttc_val_str)
                    # TTC of -1 indicates no collision course, check positive valid TTC
                    if 0 <= ttc_val < TTC_THRESHOLD:
                        ttc_incidents += 1
                except ValueError:
                    pass
                    
        # Check maxDRAC
        max_drac_elem = conflict.find('maxDRAC')
        if max_drac_elem is not None:
            drac_val_str = max_drac_elem.get('value')
            if drac_val_str is not None and drac_val_str != 'NA':
                try:
                    drac_val = float(drac_val_str)
                    if drac_val >= DRAC_THRESHOLD:
                        hard_braking_events += 1
                except ValueError:
                    pass

    return {
        "total_conflicts": total_conflicts_in_window,
        "ttc_incidents": ttc_incidents,
        "hard_braking_events": hard_braking_events
    }

def analyze_tripinfo(tripinfo_filepath):
    """Parses travel times, speed, delay, and emissions from tripinfo XML file."""
    if not os.path.exists(tripinfo_filepath):
        print(f"Error: Tripinfo file not found at {tripinfo_filepath}")
        return None

    print(f"Parsing tripinfo metrics from: {tripinfo_filepath}...")
    
    # All vehicles lists
    all_durations = []
    all_speeds = []
    all_delays = []
    
    # Corridor (N1 <-> Port) vehicles lists
    corridor_durations = []
    corridor_speeds = []
    corridor_delays = []
    
    total_co2_mg = 0.0
    total_nox_mg = 0.0
    total_pm_mg = 0.0
    
    all_vehicle_count = 0
    corridor_vehicle_count = 0
    all_distance_m = 0.0
    
    tree = ET.parse(tripinfo_filepath)
    root = tree.getroot()
    
    for tripinfo in root.findall('tripinfo'):
        depart_str = tripinfo.get('depart')
        tripinfo_id = tripinfo.get('id', '')
        if depart_str is None:
            continue
            
        depart_time = float(depart_str)
        # Filter by departure time window
        if not (START_TIME <= depart_time < END_TIME):
            continue
            
        duration_str = tripinfo.get('duration')
        route_length_str = tripinfo.get('routeLength')
        time_loss_str = tripinfo.get('timeLoss')
        
        if duration_str is None or route_length_str is None or time_loss_str is None:
            continue
            
        duration = float(duration_str)
        route_length = float(route_length_str)
        time_loss = float(time_loss_str)
        
        # Guard against zero duration
        if duration <= 0:
            continue
            
        # Add to all vehicles
        all_vehicle_count += 1
        all_distance_m += route_length
        all_durations.append(duration)
        all_speeds.append(route_length / duration)
        all_delays.append(time_loss)
        
        # Check if vehicle is traveling on N1 <-> Port corridor
        veh_id_lower = tripinfo_id.lower()
        if "n1_port" in veh_id_lower or "port_n1" in veh_id_lower:
            corridor_vehicle_count += 1
            corridor_durations.append(duration)
            corridor_speeds.append(route_length / duration)
            corridor_delays.append(time_loss)
        
        # Parse emissions (for all vehicles in the simulation)
        emissions_elem = tripinfo.find('emissions')
        if emissions_elem is not None:
            co2_str = emissions_elem.get('CO2_abs')
            nox_str = emissions_elem.get('NOx_abs')
            pm_str = emissions_elem.get('PMx_abs')
            
            if co2_str is not None:
                total_co2_mg += float(co2_str)
            if nox_str is not None:
                total_nox_mg += float(nox_str)
            if pm_str is not None:
                total_pm_mg += float(pm_str)
                
    # Calculate stats
    mg_to_kg = 1e-6
    total_co2_kg = total_co2_mg * mg_to_kg
    total_nox_kg = total_nox_mg * mg_to_kg
    total_pm_kg = total_pm_mg * mg_to_kg
    all_vkt = all_distance_m / 1000.0
    
    results = {
        "all_vehicle_count": all_vehicle_count,
        "corridor_vehicle_count": corridor_vehicle_count,
        "all_vkt": all_vkt,
        "total_co2_kg": total_co2_kg,
        "total_nox_kg": total_nox_kg,
        "total_pm_kg": total_pm_kg
    }
    
    # Calculate all vehicle averages
    if all_vehicle_count > 0:
        results.update({
            "all_mean_travel_time": statistics.mean(all_durations),
            "all_median_travel_time": statistics.median(all_durations),
            "all_avg_speed": statistics.mean(all_speeds),
            "all_speed_85th": calculate_percentile(all_speeds, 0.85),
            "all_speed_variance": calculate_variance(all_speeds),
            "all_avg_delay": statistics.mean(all_delays)
        })
    else:
        results.update({
            "all_mean_travel_time": 0.0,
            "all_median_travel_time": 0.0,
            "all_avg_speed": 0.0,
            "all_speed_85th": 0.0,
            "all_speed_variance": 0.0,
            "all_avg_delay": 0.0
        })
        
    # Calculate corridor-specific averages
    if corridor_vehicle_count > 0:
        results.update({
            "corridor_mean_travel_time": statistics.mean(corridor_durations),
            "corridor_median_travel_time": statistics.median(corridor_durations),
            "corridor_avg_speed": statistics.mean(corridor_speeds),
            "corridor_speed_85th": calculate_percentile(corridor_speeds, 0.85),
            "corridor_speed_variance": calculate_variance(corridor_speeds),
            "corridor_avg_delay": statistics.mean(corridor_delays)
        })
    else:
        results.update({
            "corridor_mean_travel_time": 0.0,
            "corridor_median_travel_time": 0.0,
            "corridor_avg_speed": 0.0,
            "corridor_speed_85th": 0.0,
            "corridor_speed_variance": 0.0,
            "corridor_avg_delay": 0.0
        })
        
    return results

def main():
    # Resolve relative paths based on current directory
    current_dir = os.path.dirname(os.path.abspath(__file__))
    tripinfo_path = os.path.join(current_dir, TRIPINFO_FILE)
    ssm_path = os.path.join(current_dir, SSM_FILE)
    
    print("=" * 60)
    print(f"SUMO KPI Extraction (Time Window: {START_TIME}s to {END_TIME}s)")
    print("=" * 60)
    
    safety_results = analyze_safety(ssm_path)
    print()
    trip_results = analyze_tripinfo(tripinfo_path)
    
    print("\n" + "=" * 60)
    print("RESULTS")
    print("=" * 60)
    
    all_vkt = trip_results['all_vkt'] if trip_results else 0.0
    safe_vkt = all_vkt if all_vkt > 0 else 1.0  # Prevent division by zero

    if safety_results:
        print(f"--- Safety Metrics (SSM & Network-Wide) ---")
        print(f"Total Conflicts in Window:      {safety_results['total_conflicts']}")
        if trip_results:
            print(f"TTC Incidents (< {TTC_THRESHOLD}s):          {safety_results['ttc_incidents']} ({safety_results['ttc_incidents']/safe_vkt*1000:.2f} per 1000 VKT)")
            print(f"Hard Braking Events (>= {DRAC_THRESHOLD} m/s²): {safety_results['hard_braking_events']} ({safety_results['hard_braking_events']/safe_vkt*1000:.2f} per 1000 VKT)")
            print(f"Speed Variance (All Vehicles):  {trip_results['all_speed_variance']*12.96:.2f} (km/h)²")
        else:
            print(f"TTC Incidents (< {TTC_THRESHOLD}s):          {safety_results['ttc_incidents']}")
            print(f"Hard Braking Events (>= {DRAC_THRESHOLD} m/s²): {safety_results['hard_braking_events']}")
        print()
        
    if trip_results:
        print(f"--- Congestion & Efficiency Metrics (N1 <-> Port Corridor Only) ---")
        print(f"Analyzed Corridor Vehicles:     {trip_results['corridor_vehicle_count']} (out of {trip_results['all_vehicle_count']} total)")
        print(f"Mean Travel Time (Corridor):    {trip_results['corridor_mean_travel_time']/60:.2f} min")
        print(f"Median Travel Time (Corridor):  {trip_results['corridor_median_travel_time']/60:.2f} min")
        print(f"Average Speed (Corridor):       {trip_results['corridor_avg_speed']*3.6:.2f} km/h")
        print(f"85th Percentile Speed (Corr):   {trip_results['corridor_speed_85th']*3.6:.2f} km/h")
        print(f"Speed Variance (Corridor):      {trip_results['corridor_speed_variance']*12.96:.2f} (km/h)²")
        print(f"Average Delay (Corridor):       {trip_results['corridor_avg_delay']/60:.2f} min")
        print()
        print(f"--- Congestion & Efficiency Metrics (All Vehicles Network-Wide) ---")
        print(f"Mean Travel Time (All):         {trip_results['all_mean_travel_time']/60:.2f} min")
        print(f"Median Travel Time (All):       {trip_results['all_median_travel_time']/60:.2f} min")
        print(f"Average Speed (All):            {trip_results['all_avg_speed']*3.6:.2f} km/h")
        print(f"85th Percentile Speed (All):    {trip_results['all_speed_85th']*3.6:.2f} km/h")
        print(f"Average Delay (All):            {trip_results['all_avg_delay']/60:.2f} min")
        print()
        print(f"--- Emissions Metrics (Total Network-Wide) ---")
        print(f"Total Network VKT:              {all_vkt:.2f} km")
        print(f"Total CO2 Emissions:            {trip_results['total_co2_kg']:.2f} kg ({trip_results['total_co2_kg']/safe_vkt:.3f} kg/km)")
        print(f"Total NOx Emissions:            {trip_results['total_nox_kg']:.2f} kg ({trip_results['total_nox_kg']/safe_vkt*1000:.2f} g/km)")
        print(f"Total PM Emissions:             {trip_results['total_pm_kg']:.2f} kg ({trip_results['total_pm_kg']/safe_vkt*1000:.2f} g/km)")
        print("=" * 60)

if __name__ == "__main__":
    main()
