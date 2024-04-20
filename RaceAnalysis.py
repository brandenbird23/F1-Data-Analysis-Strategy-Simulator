"""
    This class analyzes the race data for key insights.
    Analyzes driver performances, including lap times and positions.
    Provides detailed analysis of tire usage, pit stop strategies, 
    and the impact those had on the race.
    Compares performances between drivers.
"""
import pandas as pd

class RaceAnalysis:
    def __init__(self, results):
        self.results = results
        

    # Calls other methods to performancee specirfic tasks to create the performance analysis for drivers
    def analyze_driver_performance(self, driver_code, race_data_retriever):
        # Grab race results for the given driver
        driver_results = self.get_driver_results(driver_code)
        if driver_results is None:
            # Return an error message in a dictionary so the calling code can iterate over it
            return {"error": f"No results for driver code {driver_code}"}   
             
        performance_output = self.format_driver_performance(driver_results)

        fastest_lap_performance = self.analyze_fastest_lap(driver_code, race_data_retriever)
        performance_output.update(fastest_lap_performance)

        return performance_output
    

    # Helper method to retrive race results for specific drivers.
    def get_driver_results(self, driver_code):
        try:
            driver_result = self.results.loc[self.results['Abbreviation'] == driver_code]
            return driver_result.iloc[0] if not driver_result.empty else None
        except KeyError:
            return None
        

    def format_driver_performance(self, driver_result):
        # Format time to not be TimeDelta
        time_str = driver_result.get('Time', pd.NaT)
        if not pd.isnull(time_str):
            time_str = str(time_str).split('days')[-1].strip()

        return {
            'Driver': driver_result.get('Abbreviation', 'N/A'),
            'Number': driver_result.get('DriverNumber', 'N/A'),
            'Grid Position': driver_result.get('GridPosition', 'N/A'),
            'Position': driver_result.get('Position', 'N/A'),
            'Points': driver_result.get('Points', 'N/A'),
            'Time': time_str,
        }
    

    def analyze_stint_and_compound_data(self, laps):
        if laps is not None:    
            stints = laps[['Driver', 'Stint', 'Compound', 'LapNumber']].dropna()
            stints = stints.groupby(['Driver', 'Stint', 'Compound'])
            stints = stints.count().reset_index()
            stints = stints.rename(columns={'LapNumber': 'StintLength'})
            return stints
        return None
    

    def analyze_fastest_lap(self, driver_code, race_data_retriever):
        fastest_lap_time, top_speed = race_data_retriever.get_fastest_lap_data(driver_code)
        if fastest_lap_time is not None:
            # Remove the 'days' part if present
            fastest_lap_str = str(fastest_lap_time).split('days')[-1].strip()
            return {
                'Fastest Lap Time': fastest_lap_str,
                'Top Speed during Fastest Lap': f"{top_speed} km/h" if top_speed else 'N/A'
            }
        else:
            return {
                'Fastest Lap Time': 'N/A',
                'Top Speed during Fastest Lap': 'N/A'
            }


    # Ask if they want to compare to the driver who came first place
    def compare_with_winner(self, race_data_retriever):
        # Retrieve the winner's data based on position 1
        winner_result = self.get_driver_position(1)
        if winner_result is None or winner_result.empty:
            print("Winner data not available.")
            return
        
        # Use the format_driver_performance method to print the winner's details consistently
        print("\nDriver performance of race winner:")
        winner_performance = self.format_driver_performance(winner_result)
        for key, value in winner_performance.items():
            print(f"{key}: {value}")

        winner_fastest_lap_performance = self.analyze_fastest_lap(winner_result['Abbreviation'], race_data_retriever)
        for key, value in winner_fastest_lap_performance.items():
            print(f"{key}: {value}")

        winner_stint_and_compound = self.analyze_stint_and_compound_data(race_data_retriever.get_lap_data())
        winner_stint_data = winner_stint_and_compound[winner_stint_and_compound['Driver'] == winner_result['Abbreviation']]
        if not winner_stint_data.empty:
            print(winner_stint_data.to_string(index=False))
        else:
            print("No tire and compound data available for the winner.")


    # Helper method to find the position of each driver
    def get_driver_position(self, position):
        try:
            driver_result = self.results.loc[self.results['Position'] == position]
            return driver_result.iloc[0] if not driver_result.empty else None
        except KeyError:
            return None
        

    def get_driver_race_time(self, driver_code):
        # Session's winner data
        winner_data = self.results[self.results['Position'] == 1].iloc[0]
        winner_code = winner_data['Abbreviation']
        # Get the winner's total race time
        winner_race_time = self.get_winner_race_time()

        if winner_race_time is None:
            print("Cannot determine the actual race time without the winner's time.")
            return None
        
        if driver_code == winner_code:
            return winner_race_time
        else:
            driver_results = self.results[self.results['Abbreviation'] == driver_code]
            if not driver_results.empty:
                time_behind_str = driver_results.iloc[0]['Time']
                try:
                    time_behind = pd.to_timedelta(time_behind_str)
                    # Calculate the total race time for the driver
                    total_race_time = winner_race_time + time_behind
                    return total_race_time
                except ValueError:
                    print(f"Race time data is invalid for driver code '{driver_code}'.")
                    return None
            else:
                print(f"No race results found for driver code '{driver_code}'.")
                return None
        

    def get_winner_race_time(self):
        winner_results = self.results[self.results['Position'] == 1]
        if not winner_results.empty:
            winner_time_str = winner_results.iloc[0]['Time']
            try:
                winner_time = pd.to_timedelta(winner_time_str)
                return winner_time
            except ValueError:
                print(f"Winner's race time data is invalid.")
                return None
        else:
            print("Winner's race time not found.")
            return None