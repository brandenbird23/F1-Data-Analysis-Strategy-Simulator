"""
    This class simulates and analyzes different user race strategies.
    Allows the user to input hypothetical strategies (e.g., different
    tire choices, pit stop times).
    Simulates the race outcome based on these variables and compares 
    them with actual race data.
    Analyzes the different strategies and how they impacted the 
    race outcome.
"""
import numpy as np
from RaceDataRetriever import RaceDataRetriever
from RaceAnalysis import RaceAnalysis
from Plotting import Plotting
import pandas as pd

class RaceStrategySimulator:
    def __init__(self, year, race):
        self.year = year
        self.race = race
        self.data_retriever = RaceDataRetriever(year, race)
        self.analysis = None
        self.user_strategy = []
        self.simulated_lap_times = []  # To store simulated lap times based on user strategy.
        self.total_laps = 0
        self.driver_code = None
        # for when we cant find averages of a compound
        self.compound_performance_factor = {
            'SOFT': 1.018,
            'MEDIUM': 1.038,
            'HARD': 1.058,
            'WET': 1.098,
            'INTERMEDIATE': 1.078
        }


    def load_and_initialize_data(self):
        session = self.data_retriever.load_session()
        if session and hasattr(session, 'laps'):
            self.analysis = RaceAnalysis(session.results)
            self.total_laps = session.laps['LapNumber'].max()
        else:
            print("Race data could not be initialized.")
        

    def input_strategy(self):
        # User inputs their strategy here
        # Example: [('Soft', 10), ('Medium', 20), ('Hard', 30)]
        print(f"There are {self.total_laps} total laps in the {self.race.capitalize()} Grand Prix of {self.year}.")
        while True:
            self.user_strategy = []  # Reset strategy each time we start the loop
            try:
                num_stints = int(input("\nHow many stints do you want to plan? (at least 2): "))
                if num_stints < 2:
                    print("You need to plan at least 2 stints. Please try again.")
                    continue

                for stint_num in range(1, num_stints + 1):
                    while True:
                        print("\nCompound options:\nSoft\nMedium\nHard\nWet\nIntermediate")
                        stint_info = input(f"Enter compound and laps for stint {stint_num} (e.g., 'Soft 20'): ")
                        compound, laps = stint_info.split()
                        laps = int(laps)

                        if laps <= 0:
                            print("Number of laps must be greater than zero. Please try again.")
                            continue

                        self.user_strategy.append((compound.upper(), laps))
                        break  # Break inner loop when a valid stint is entered

                total_strategy_laps = sum(laps for _, laps in self.user_strategy)
                if total_strategy_laps != self.total_laps:
                    print(f"\nThe total laps in your strategy ({total_strategy_laps}) do not match the race length of {self.total_laps} laps.")
                    print("Please revise your strategy.")
                else:
                    print("\nStrategy accepted.")
                    break  # Break outer loop when the total strategy is valid

            except ValueError:
                print("Invalid input. Please enter numerical values for the number of stints and laps.")
            except IndexError:
                print("Invalid format. Please use the format 'Compound Laps' for your strategy.")


    # Check if the driver finishes the full race or not
    def did_driver_finish(self, driver_code):
        # Ensure lap data is loaded
        if not hasattr(self.data_retriever, 'lap_data'):
            self.data_retriever.lap_data = self.data_retriever.get_lap_data()
        driver_laps = self.data_retriever.lap_data[self.data_retriever.lap_data['Driver'] == driver_code]
        return len(driver_laps) == self.total_laps


    def calculate_driver_averages(self, driver_code):
        # Check if lap data is loaded
        if not hasattr(self.data_retriever, 'lap_data'):
            self.data_retriever.lap_data = self.data_retriever.get_lap_data()

        lap_data = self.data_retriever.get_lap_data()

        driver_averages = {}
        for compound, _ in self.user_strategy:
            compound_upper = compound.upper()
            compound_laps = lap_data[(lap_data['Driver'] == driver_code) & 
                                    (lap_data['Compound'].str.upper() == compound_upper)]

            if not compound_laps.empty:
                driver_averages[compound_upper] = compound_laps['LapTime'].mean().total_seconds()
            else:
                print(f"No data for {compound_upper}, using average lap time.")
                driver_averages[compound_upper] = lap_data['LapTime'].mean().total_seconds()

        return driver_averages


    def simulate_lap_times(self, driver_code):
        if not self.did_driver_finish(driver_code):
            print(f"Driver {driver_code} did not finish the race and cannot be used for simulation.")
            return []

        driver_averages = self.calculate_driver_averages(driver_code)
        simulated_times = []
        for compound, laps in self.user_strategy:
            compound_upper = compound.upper()
            if compound_upper in driver_averages:
                base_lap_time = driver_averages[compound_upper]
                compound_factor = self.compound_performance_factor[compound_upper]

                for _ in range(laps):
                    # Introduce deviation up to +/- 0.05% of the base lap time
                    deviation = np.random.uniform(-0.005, 0.005) * base_lap_time
                    lap_time_with_deviation = base_lap_time * compound_factor + deviation
                    simulated_times.append(pd.Timedelta(seconds=lap_time_with_deviation))
            else:
                print(f"No average lap time found for compound '{compound_upper}'. Using default value.")
                for _ in range(laps):
                    # Introduce deviation up to +/- 0.05% of the default lap time (90 seconds in this case)
                    deviation = np.random.uniform(-0.005, 0.005) * 90
                    simulated_times.append(pd.Timedelta(seconds=90 + deviation))
        return simulated_times


    def compare_strategy(self, driver_code):
        # Retrieve the actual race data for the specified driver
        actual_race_time = self.analysis.get_driver_race_time(driver_code)
        # Calculate the total simulated race time
        total_simulated_time = sum(self.simulated_lap_times, pd.Timedelta(0))

        # Get actual stint and compound data for the driver for comparison
        actual_stint_data = self.analysis.analyze_stint_and_compound_data(self.data_retriever.get_lap_data())
        actual_stint_data = actual_stint_data[actual_stint_data['Driver'] == driver_code]

        max_stints = max(actual_stint_data['Stint'].max(), len(self.user_strategy))

        # Format
        actual_race_time_str = str(actual_race_time).split(' days ')[-1]  # This will take the time part after ' days '
        total_simulated_time_str = str(total_simulated_time).split(' days ')[-1]  # Same for the simulated time
        
        if actual_race_time is not None:
            # Print the side by side comparison of stints
            print("\nStint | Actual Compound (Laps) | Simulated Compound (Laps)")
            print("-" * 58)  # Adjust the number of dashes based on the width of your table
            for stint_number in range(1, int(max_stints) + 1):
                actual_compound, actual_laps = self.get_actual_stint_info(actual_stint_data, stint_number)
                if stint_number <= len(self.user_strategy):
                    sim_compound, sim_laps = self.user_strategy[stint_number - 1]
                else:
                    sim_compound, sim_laps = ('N/A', 'N/A')
                print(f"{stint_number:<5} | {actual_compound:<16} ({actual_laps:<3}) | {sim_compound:<16} ({sim_laps:<3})")

            print(f"\nActual total race time for driver {driver_code}: {actual_race_time_str}")
            print(f"Simulated total race time for driver {driver_code}: {total_simulated_time_str}")

            time_difference = total_simulated_time - actual_race_time
            time_difference_str = str(time_difference).split(' days ')[-1]
            if time_difference > pd.Timedelta(0):
                print(f"The simulated strategy is {time_difference_str} slower than the actual race time.\n")
            else:
                # When the simulated time is faster, time_difference will be negative, so multiply by -1 to make it positive before converting to string
                faster_time_str = str(-time_difference).split(' days ')[-1]
                print(f"The simulated strategy is {faster_time_str} faster than the actual race time.\n")

        else:
            print(f"No actual race time found for driver {driver_code}.")

    
    def get_actual_stint_info(self, actual_stint_data, stint_number):
        stint_info = actual_stint_data[actual_stint_data['Stint'] == stint_number]
        if not stint_info.empty:
            compound = stint_info.iloc[0]['Compound']
            laps = stint_info.iloc[0]['StintLength']
            return compound, laps
        return 'N/A', 'N/A'
    

    def get_drivers(self):
        if not self.data_retriever.session:
            self.load_and_initialize_data()

        results = self.data_retriever.get_race_data()

        num_to_abbreviation, abbreviation_to_num = self.data_retriever.create_driver_mappings(results)
        self.data_retriever.display_driver_mappings(num_to_abbreviation)
        
        while True:
            input_id = input("Enter the DriverID or Driver Number to simulate (e.g., 'HAM' or '44'): ").upper()
            if input_id in num_to_abbreviation:
                return num_to_abbreviation[input_id]  # Input is a driver number
            elif input_id in abbreviation_to_num:
                return input_id  # Input is already a driver abbreviation
            else:
                print("Invalid DriverID. Please try again.")
                



    def run_simulation(self):
         # Make sure the data is loaded before running simulation
        if not self.analysis:
            print("Loading and initializing race data.")
            self.load_and_initialize_data()
        if not self.analysis:
            print("Cannot run simulation without race data.")
            return
        
        self.driver_code = self.get_drivers()

        if not self.driver_code:
            print("Driver code could not be found. Exiting simulation.")
            return

        if not self.did_driver_finish(self.driver_code):
            print(f"Driver {self.driver_code} did not finish the race.")
            return

        self.input_strategy()
        self.simulated_lap_times = self.simulate_lap_times(self.driver_code)
        self.compare_strategy(self.driver_code)
            


if __name__ == "__main__":
    year = int(input("Enter the year of the race: "))
    race = input("Enter the name or location of the race: ")
    simulator = Plotting(year, race)
    simulator.load_and_initialize_data()

    strategy_simulator = RaceStrategySimulator(year, race)
    strategy_simulator.run_simulation()
    
    simulator.plot_tyre_strategies(driver_code=strategy_simulator.driver_code, simulated_strategy=strategy_simulator.user_strategy)