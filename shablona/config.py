instruments = ['adcp', 'camera', 'blueview', 'm3', 'hydrophone']

# Buffer size in seconds
instrument_buffer_sizes = {'camera': 15, 'blueview': 15, 'm3':15, 'pamguard': 15}

# This supplies the order and contents for classification features
classifier_features = ['size', 'speed', 'deltav', 'target_strength', 'time_of_day',
			'current']

# Minimum and maximum expected values for each axis
classifier_axis_bounds = {
	'size': (5.0,100.0),
	'speed': (5.0, 100.0),
	'deltav': (5.0, 100.0),
	'target_strength': (5.0, 100.0),
	'time_of_day': (5.0, 100.0),
	'current': (5.0, 100.0) }

# Background
background_hyperspaces = [
	{'size': (1,5),
	'speed': (4,6),
	'deltav': (-0.5,0.5),
	'target_strength': (0.7,1.0),
	'classification': 'Class1'},

	{'size': (-np.inf, np.inf),
	'speed': (-np.inf, np.inf),
	'deltav': (-np.inf, np.inf),
	'target_strength': (-np.inf, np.inf),
	'time_of_day': (-np.inf, np.inf),
	'current': (-np.inf, np.inf),
	'classification': 'Class2'} ]

# Classifications
classifications = {
	1: "Some class",
	2: "Some other class"
}
