import numpy as np


# name of site of current deployment. this will be added as an attribute to
# classified targets. site_name_auto indicates that a classification was
# determined by the classifier, and site_name_manual indicates that a
# classification was either entered or verified during manual review
site_name = ['MSL']

instruments = ['adcp', 'camera', 'blueview', 'm3', 'hydrophones']

# Buffer size in seconds
instrument_buffer_sizes = {'camera': 15, 'blueview': 15, 'm3':15, 'hydrophones': 15}

# Instrument ranges
instrument_ranges = {'camera': 8, 'blueview': 10, 'm3': 50}

data_streams = ['adcp', 'camera', 'pamguard', 'nims', 'nims-simulator']
data_streams_groupby = {'nims': 'track_id', 'nims-simulator': 'track_id'}

# This supplies the order and contents for classification features
classifier_features = ['size', 'speed', 'deltav', 'target_strength', 'time_of_day',
			'current']

# current threshold below which to ignore targets
# that do not include a PAMGuard detection
ADCP_threshold = 0.25 # m/s

# Minimum and maximum expected values for each axis
classifier_axis_bounds = {
	'size': (0, 3), # m^2
	'speed': (0, 5), # m/s
	'deltav': (0, 4), # m/s
	'target_strength': (0, 150), # mean intensity
	'time_of_day': (0, 24), # hours
	'current': (-2, 2) } # m/s

# Background
background_hyperspaces = [
	{'size': (.25, 3), # m^2
	'speed': (1, 5), # m/s
	'deltav': (0.5, 4), # m/s
	'target_strength': (90, 150), # ??
	'classification': 'Marine Mammal'},

	{'size': (0,.25), # m^2
	'speed': (0,1), # m/s
	'deltav': (0,0.5), # m/s
	'target_strength': (0,90), # ??
	'classification': 'Small Fish'},

	{'size': (-np.inf, np.inf), # m^2
	'speed': (-np.inf, np.inf), # m/s
	'deltav': (-np.inf, np.inf), # m/s
	'target_strength': (-np.inf, np.inf), # ??
	'time_of_day': (-np.inf, np.inf), # hours
	'current': (-np.inf, np.inf), # m/s
	'classification': 'Outliers'} ]

# Classifications
classifications = {
	1: "Marine Mammal",
	2: "Small Fish",
	3: "Outliers"
}
