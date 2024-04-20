# Pandas is updating soon and posts lots of warnings about it
import warnings
warnings.simplefilter("ignore")

import numpy as np
import matplotlib as mpl
from matplotlib import pyplot as plt

import fastf1 as ff1
from fastf1 import plotting
from RaceDataRetriever import RaceDataRetriever
from RaceAnalysis import RaceAnalysis


class Plotting:
    def __init__(self, year, race):
        self.year = year
        self.race = race
        self.data_retriever = RaceDataRetriever(year, race)
        self.analysis = None
        self.drivers = None
        self.driver_laps = None
        self.lap_data = None
        self.total_laps = 0

    
    def load_and_initialize_data(self):
        session = self.data_retriever.load_session()
        if session and hasattr(session, 'laps'):
            self.analysis = RaceAnalysis(session.results)
            self.drivers = session.drivers
            self.drivers = [session.get_driver(driver)["Abbreviation"] for driver in self.drivers]
            self.total_laps = session.laps['LapNumber'].max()

            self.stint_and_compound()
        else:
            print("Race data could not be initialized.")



    def stint_and_compound(self):
        self.lap_data = self.analysis.analyze_stint_and_compound_data(self.data_retriever.get_lap_data())
        return self.lap_data

    
    def plot_tyre_strategies(self, driver_code=None, simulated_strategy=None):
        fig, ax = plt.subplots(figsize=(7, 10))

        if self.lap_data is not None and self.drivers is not None:
            legend_entries = []  # Stores the legend handles
            existing_labels = [] # Keeps track of compounds already stored

            for driver in self.drivers:
                driver_stints = self.lap_data.loc[self.lap_data["Driver"] == driver]
                previous_stint_end = 0
                for _, row in driver_stints.iterrows():
                    stint_length = row['StintLength']
                    compound = row['Compound']
                    color = plotting.COMPOUND_COLORS.get(row["Compound"], "grey")
                    # Bars
                    ax.barh(
                        y = driver,
                        width = stint_length,
                        left = previous_stint_end,
                        color = color,
                        edgecolor = "black",
                        fill = True
                    )
                    previous_stint_end += stint_length

                    # Key/Legend for tyre compound color
                    # Create a legend entry if compound is not already in the legend
                    if compound not in existing_labels:
                        legend_entry = mpl.patches.Patch(color=color, label=compound)
                        legend_entries.append(legend_entry)
                        existing_labels.append(compound)
            
            if simulated_strategy and driver_code:
                sim_driver = f"SIM {driver_code}"  # Use the driver abbreviation for the simulated strategy
                previous_stint_end = 0
                for stint in simulated_strategy:
                    compound, stint_length = stint
                    color = plotting.COMPOUND_COLORS.get(compound.upper(), "grey")
                    # Simulated Bars
                    ax.barh(
                        y = sim_driver,
                        width = stint_length,
                        left = previous_stint_end,
                        color = color,
                        edgecolor = "black",
                        hatch = '//',
                        fill = True
                    )
                    previous_stint_end += stint_length

                    if compound.upper() not in existing_labels:
                        legend_entry = mpl.patches.Patch(color=color, label=compound.upper(), hatch='//')
                        legend_entries.append(legend_entry)
                        existing_labels.append(compound.upper())
                        

            # invert the y-axis so drivers that finish higher are closer to the top
            ax.invert_yaxis()
            ax.set_title(f"{self.race.capitalize()} Grand Prix {self.year} Strategies")
            ax.set_xlabel("Lap Number")
            ax.spines['top'].set_visible(False)
            ax.spines['right'].set_visible(False)
            ax.spines['left'].set_visible(False)

            # Create the legend outside the plots
            ax.legend(handles=legend_entries, loc='upper left', bbox_to_anchor=(0.96, 0.98), title="Tyre Compounds")
            
            plt.tight_layout()
            plt.show(block=False)
        else:
            print("Data not initialized or loaded.")


    
    def draw_map_visual(self):
        #self.load_and_initialize_data()
        session = self.data_retriever.load_session()
        lap = session.laps.pick_fastest()
        pos = lap.get_pos_data()
        circuit_info = session.get_circuit_info()

        # Get array of shape [n,2] where n is the number of points
        # and the second axis is x and y
        track = pos.loc[:, ('X', 'Y')].to_numpy()

        # Convert rotation angle from degrees to radian
        track_angle = circuit_info.rotation / 180 * np.pi

        # Rotate and plot the track map
        rotated_track = self.rotate(track, angle=track_angle)
        plt.plot(rotated_track[:, 0], rotated_track[:, 1])

        offset_vector = [500, 0]

        # Iterate over all corners
        for _, corner in circuit_info.corners.iterrows():
            # Create string from corner number and letter
            txt = f"{corner['Number']}{corner['Letter']}"

            # Convert angle from degrees to radian
            offset_angle = corner['Angle'] / 180 * np.pi

            # Rotate offset vector so it points sideways from track
            offset_x, offset_y = self.rotate(offset_vector, angle=offset_angle)

            # Add offset to the position of the corner
            text_x = corner['X'] + offset_x
            text_y = corner['Y'] + offset_y

            # Rotate text position equivalently to the rest of the track map
            text_x, text_y = self.rotate([text_x, text_y], angle=track_angle)

            # Rotate center of corner equivalently to rest of the track map
            track_x, track_y = self.rotate([corner['X'], corner['Y']], angle=track_angle)

            # Draw a circle next to the track
            plt.scatter(text_x, text_y, color='grey', s=140)

            # Draw a line from the track to the circle
            plt.plot([track_x, text_x], [track_y, text_y], color='grey')

            # Print the corner number inside the circle
            plt.text(text_x, text_y, txt,
                     va='center_baseline', ha='center', size='small', color='white')
            
        plt.title(f"{session.event['EventName']} {self.year}")
        plt.xticks([])
        plt.yticks([])
        plt.axis('equal')
        plt.show(block=False)



    # Helper function for rotating points around origin of coordinate system
    def rotate(self, xy, *, angle):
        rot_mat = np.array([[np.cos(angle), np.sin(angle)],
                        [-np.sin(angle), np.cos(angle)]])
        return np.matmul(xy, rot_mat)




if __name__ == "__main__":
    year = int(input("Enter the year of the race: "))
    race = input("Enter the name or location of the race: ")
    simulator = Plotting(year, race)
    simulator.load_and_initialize_data()
    #simulator.stint_and_compound()
    simulator.plot_tyre_strategies()
    simulator.draw_map_visual()