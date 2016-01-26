from enum import Enum
import numpy as np
from sklearn.neighbors import NearestNeighbors
from datetime import datetime
#import .utils 

# Global variables
INITIAL_RADIUS = 3.0

# Define classes
class Classes(Enum):
    Interesting = 1.1
    NotInteresting = 1.2
    
    FastLarge = 2.1
    FastSmall = 2.2
    SlowLarge = 2.3
    SlowSmall = 2.4
    
    # SchoolOfFish = 3.1
    # SingleFish = 3.2
    # Kelp = 3.3
    # DolphinOrPorpoise = 3.4

# Read in existing DetectedTargets from file
current_model_targets = []

with open('current_model_targets.csv', 'r') as f:
	for target in csv.reader(f, delimiter=";"):
		current_model_targets.append( DetectedTarget( \
			features=list(target[1]), source=target[2], date=target[3], classification=Classes(target[4])) )

# Initialize model
model = NearestNeighbors(radius=INITIAL_RADIUS)
model.fit(np.array(map(lambda x: x.features, current_model_targets)))

# Adjust weights of features for all existing points


# Call classify

	# find distances and indices

	# radius manipulation

	# obtain weights

	# voting

	# returns classification and classification strength