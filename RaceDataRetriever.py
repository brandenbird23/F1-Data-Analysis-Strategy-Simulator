"""
    This class fetches and processes the raw race data from FastF1.
    Fetch detailed information such as lap times, pit stop times,
    and tire choices.
    It returns the data in a generic format so RaceAnalysis.py can
    understand the inputs without using FastF1
"""
import fastf1 as ff1
from fastf1.core import Session
import os


class RaceDataRetriever:
    def __init__(self, year, race):
        self.cache_dir = './fastf1_cache'
        self.year = year
        self.race = race
        self.session = None
        self.num_to_abbreviation = None
        self.abbreviation_to_num = None
        self._setup_cache()
        
        
    def _setup_cache(self):
        if not os.path.exists(self.cache_dir):
            os.makedirs(self.cache_dir)
        ff1.Cache.enable_cache(self.cache_dir) # Enable cache

         
    def load_session(self):
        try:
            self.session = ff1.get_session(self.year, self.race, 'R')
            self.session.load()
            return self.session
        except Exception as e:
            print(f"An error occurred while loading the session: {e}")
        return None


    def get_race_data(self):
        if self.session:
            try:
                return self.session.results
            except ff1.core.DataNotLoadedError as e:
                print(f"The data you are trying to access has not been loaded yet. Error: {e}")
                return None
            except Exception as e:
                print(f"An error occurred while loading lap data: {e}")
                return None
        else:
            print("Session is not initialized.")
            return None


    def get_lap_data(self):
        if self.session:
            try:
                return self.session.laps
            except ff1.core.DataNotLoadedError as e:
                print(f"The data you are trying to access has not been loaded yet. Error: {e}")
                return None
            except Exception as e:
                print(f"An error occurred while loading lap data: {e}")
                return None
        else:
            print("Session is not initialized.")
            return None
        
    
    def get_race_calendar(self):
        try:
            calendar = ff1.get_event_schedule(self.year)
            return calendar[['RoundNumber', 'EventName', 'Country', 'Location']]
        except Exception as e:
            print(f"An error occurred while fetching the race calendar: {e}")
            return None
        
    
    def get_fastest_lap_data(self, driver_code):
        if self.session:
            try:
                fastest_lap = self.session.laps.pick_driver(driver_code).pick_fastest()
                if not fastest_lap.empty:     
                    fastest_lap_time = fastest_lap['LapTime']
                    telemetry = fastest_lap.get_telemetry()
                    if telemetry is not None:
                        top_speed = telemetry['Speed'].max()
                        return fastest_lap_time, top_speed
                else:
                    return fastest_lap_time, None
            except ff1.core.DataNotLoadedError as e:
                print(f"Fastest lap data cannot be loaded. Error: {e}")
                return None, None
            except Exception as e:
                print(f"An error occurred while fetching fastest lap data: {e}")
                return None, None
        else:
            print("Session is not initialized.")
            return None, None
        

    
    def create_driver_mappings(self, results):
        if self.session and hasattr(self.session, 'results'):
            #results = self.session.results
            self.num_to_abbreviation = {str(row['DriverNumber']): row['Abbreviation'] for _, row in results.iterrows()}
            self.abbreviation_to_num = {row['Abbreviation']: str(row['DriverNumber']) for _, row in results.iterrows()}
            return self.num_to_abbreviation, self.abbreviation_to_num
        else:
            self.num_to_abbreviation = {}
            self.abbreviation_to_num = {}



    def display_driver_mappings(self, num_to_abbreviation):
        self.num_to_abbreviation = num_to_abbreviation
        print("\nDriver Number and Abbreviations:")
        print(f"{'Number':<10} | {'Abbreviation'}")
        print("-" * 25)
        for number, abbreviation in self.num_to_abbreviation.items():
            print(f"{number:<10} | {abbreviation}")