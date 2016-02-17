instruments = ['adcp', 'camera', 'blueview', 'm3', 'hydrophones']

# Buffer size in seconds
instrument_buffer_sizes = {'camera': 15, 'blueview': 15, 'm3':15, 'hydrophones': 15}

# This supplies the order and contents for classification features
classifier_features = ['size', 'speed', 'deltav', 'target_strength', 'time_of_day',
			'current']

# Minimum and maximum expected values for each axis
classifier_axis_bounds = {
	'size': (0, 5), # m^2
	'speed': (0, 5), # m/s
	'deltav': (5.0, 100.0), # m/s
	'target_strength': (0, 1), # ??
	'time_of_day': (0, 24), # hours
	'current': (-2, 2) } # m/s

# Background
background_hyperspaces = [
	{'size': (1,5), # m^2
	'speed': (1,6), # m/s
	'deltav': (-0.5,0.5), # m/s
	'target_strength': (0.7,1.0), # ??
	'classification': 'Class1'},

	{'size': (-np.inf, np.inf), # m^2
	'speed': (-np.inf, np.inf), # m/s
	'deltav': (-np.inf, np.inf), # m/s
	'target_strength': (-np.inf, np.inf), # ??
	'time_of_day': (-np.inf, np.inf), # hours
	'current': (-np.inf, np.inf), # m/s
	'classification': 'Outliers'} ]

# Classifications
classifications = {
	1: "Some class",
	2: "Some other class"
}
