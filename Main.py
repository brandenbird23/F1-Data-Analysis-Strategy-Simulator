"""
To run this program you must install the Python Library FastF1
Install using pip
-pip install fastf1
"""

# Pandas is updating soon and posts lots of warnings about it
import warnings
warnings.simplefilter("ignore")

from matplotlib import pyplot as plt
from RaceDataRetriever import RaceDataRetriever
from RaceAnalysis import RaceAnalysis
from RaceStrategySimulator import RaceStrategySimulator
from Plotting import Plotting
import re

def main():
    while True:
        year, race = get_race_details()
        if not year or not race:
            continue  # Skip to the next iteration if race details are not properly fetched

        while True:
            user_choice = input("Enter '1' for Data Analysis or '2' for Race Strategy Simulation: ")
            
            if user_choice not in ['1', '2']:
                print("Invalid option selected. Please try again.")
                continue

            data_retriever = RaceDataRetriever(year, race)
            session = data_retriever.load_session()
            results = data_retriever.get_race_data()
            lap_data = data_retriever.get_lap_data()

            # Check if the session data was loaded successfully
            if not validate_data(session, results, lap_data):
                continue

            plotter = Plotting(year, race)
            plotter.draw_map_visual()

            if user_choice == '1':
                num_to_abbreviation, abbreviation_to_num = data_retriever.create_driver_mappings(results)
                data_retriever.display_driver_mappings(num_to_abbreviation)
                drivers_to_compare = get_drivers_to_analyze(num_to_abbreviation, abbreviation_to_num)
                race_analysis = RaceAnalysis(results)
                analyze_and_print_driver_data(race_analysis, data_retriever, drivers_to_compare, lap_data)
                # Ask user if they want to compare the selected drivers with the race winner
                if input("Would you like to compare the selected driver(s) with the race winner? (Yes/No): ").lower() == 'yes':
                    race_analysis.compare_with_winner(data_retriever)
            elif user_choice == '2':
                strategy_simulator = RaceStrategySimulator(year, race)
                strategy_simulator.run_simulation()
                
                plotter.load_and_initialize_data()
                plotter.plot_tyre_strategies(driver_code=strategy_simulator.driver_code, simulated_strategy=strategy_simulator.user_strategy)
            else:
                print("Invalid option selected. Please try again.")
                
            break

        if not continue_analysis():
            break



def validate_data(session, results, lap_data):
    if session is None or not hasattr(session, 'results') or session.results.empty:
        print(f"No data found for the race. The race might not have occurred.")
        return False
    if lap_data is None:
        print("Failed to load lap data.")
        return False
    if results.empty:
        print(f"No race results data available.")
        return False
    print(f"\nSuccessfully loaded data for the race.")
    return True



def get_drivers_to_analyze(num_to_abbreviation, abbreviation_to_num):
    while True:
        driver_input = input("\nEnter DriverID(s) to analyze or simulate (e.g., 'HAM' or '44') or type 'all' for all drivers: ").upper()
        inputted_drivers = re.split('[,; ]+', driver_input.upper())

        if driver_input.lower() == 'all':
            return list(abbreviation_to_num.keys())  # Return all driver abbreviations
        else:
            drivers_to_compare = []
            for driver in inputted_drivers:
                # Convert driver number to abbreviation if necessary
                if driver in num_to_abbreviation:
                    drivers_to_compare.append(num_to_abbreviation[driver])
                elif driver in abbreviation_to_num:
                    drivers_to_compare.append(driver)
            if drivers_to_compare:
                return drivers_to_compare
            else:
                print("Invalid DriverID(s). Please try again.")



def analyze_and_print_driver_data(race_analysis, data_retriever, drivers_to_compare, lap_data):
    for driver_code in drivers_to_compare:
        print(f"\nAnalysis for Driver {driver_code}:")
        driver_performance = race_analysis.analyze_driver_performance(driver_code, data_retriever)
        if isinstance(driver_performance, dict):
            for key, value in driver_performance.items():
                print(f"{key}: {value}")
        else:
            print(driver_performance)
        print_tire_and_compound_data(driver_code, race_analysis, lap_data)



def print_tire_and_compound_data(driver_code, race_analysis, lap_data):
    stint_and_compound_data = race_analysis.analyze_stint_and_compound_data(lap_data)
    if stint_and_compound_data is not None:
        driver_stint_data = stint_and_compound_data[stint_and_compound_data['Driver'] == driver_code]
        if not driver_stint_data.empty:
            print("Tire and Compound Data:")
            print(driver_stint_data.to_string(index=False))
        else:
            print("No tire and compound data available for the selected driver.")
    print("-" * 40)  # Separator for readability



def continue_analysis():
    user_response = input("\nWould you like to analyze another race? (Yes/No): ").lower()
    if user_response == 'yes':
        # Close all matplotlib pop ups
        plt.close('all')
    return user_response == 'yes'



def get_race_details():
    while True:
        try:
            year = int(input("Enter the race year (2018-Current): "))
            if year < 2018:
                print("Data can only be loaded for years 2018 and onwards. Please enter a valid year.")
                continue
            temp_data_retriever = RaceDataRetriever(year, None)
            
            # Fetch the race calendar for the year and display it
            calendar = temp_data_retriever.get_race_calendar()
            if calendar is not None:
                print("\nHere are the races for the selected year:")
                print(calendar.to_string(index=False))
                race = get_race_from_input(calendar)
                if race:
                    return year, race
            else:
                print("Failed to fetch the race calendar. Please try again.")
        except ValueError:
            print("Invalid input. Please enter a valid year.")



def get_race_from_input(calendar):
    while True:
        race_input = input("\nEnter the desired race (e.g., 'Monaco' or '6'): ")
        if race_input.isdigit():
            round_number = int(race_input)
            race_row = calendar[calendar['RoundNumber'] == round_number]
            if not race_row.empty:
                return race_row.iloc[0]['EventName']
            else:
                print("No race found for the provided round number. Please try again.")
        else:
            if race_input is None:
                print("Race name cannot be empty. Please try again.")
            elif not race_input.strip():
                print("No race found with the provided name. Please try again.")
            else:
                return race_input



if __name__ == "__main__":
    main()