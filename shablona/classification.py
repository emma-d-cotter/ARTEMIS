from enum import Enum
import numpy as np
from sklearn.neighbors import NearestNeighbors
from datetime import datetime
import os.path
import csv

#class Classes(Enum):
 #   Interesting = 1.1
#  NotInteresting = 1.2

   # FastLarge = 2.1
    #FastSmall = 2.2
    #SlowLarge = 2.3
    #SlowSmall = 2.4

    # SchoolOfFish = 3.1
    # SingleFish = 3.2
    # Kelp = 3.3
    # DolphinOrPorpoise = 3.4

class DetectedTarget:

    features_label = ["","","","","","","",""]

    def __init__(self, features=[], source="Unknown", date=datetime.now(), classification=None):
        self.features = features
        self.source = source
        self.date = date
        self.classification = classification

class weightedNeighbors:

    def __init__(self,radius=4.0):

        # Global variables
        self.INITIAL_RADIUS = radius
        self.SIZE_FEATURE_WEIGHT = 1.0
        self.SPEED_FEATURE_WEIGHT = 1.0
        self.SPEED_RELATIVE_TO_CURRENT_FEATURE_WEIGHT = 1.0
        self.TARGET_STRENGTH_FEATURE_WEIGHT = 1.0
        self.CURRENT_SPEED_FEATURE_WEIGHT = 1.0
        self.TIME_OF_DAY_FEATURE_WEIGHT = 1.0
        self.PASSIVE_ACOUSTICS_FEATURE_WEIGHT = 1.0
        self.RADIUS_INCREMENT = 0.1 # increment for expanding radius
        self.DISTANCE_THRESHOLD = 0.01 # distance threshold for determing if two points near equidistant

        # load current model and initialize NearestNeighbors model
        self.current_model_targets = self.load_detectedTargets()
        self.model =  NearestNeighbors(radius=self.INITIAL_RADIUS)


    def load_detectedTargets(self):
        '''
        Load existing targets from current_model_targets.csv
        '''

        current_model_targets = []

        if os.path.isfile('current_model_targets.csv'):
            current_model_targets = []
            with open('current_model_targets.csv', 'r') as f:
                reader = csv.reader(f,delimiter = ";")
                next(reader,None)
                for target in reader:
                    current_model_targets.append( DetectedTarget(
                            features=list(map(float,list(target[1:8]))), source=target[8], date=target[10],
                            classification=str(target[-1])))

        return current_model_targets

    def fitModel(self):
        '''
        Fit current model targets to model
        '''
        self.model.fit(np.array(list(map(lambda x: x.features, self.current_model_targets))))

    def determine_weights(self,indices):
        '''
        This function will return the weights of points with the desired indices
        '''
        pass
        return np.ones(indices[0].shape)


    def classify(self,newPoint):
        '''
        Predict class of new target detection(s)
        '''
        x = self.RADIUS_INCREMENT
        d = self.DISTANCE_THRESHOLD
        r = self.INITIAL_RADIUS

        existingClasses = np.array(list(map(lambda x: x.classification, self.current_model_targets)))

        distances,indices = self.model.radius_neighbors(newPoint)

        # if there are no points in the radius, expand radius by x and check again before classifying point.
        if indices[0].shape==0 or indices[0].shape==1:
            self.model.radius = r+x
            distances,indices = self.model.radius_neighbors(newPoint)

        # else if there are two points from different classes that are close to the same distance
        # (within distance threshold), expand radius to see if there is another very close point
        elif indices[0].shape ==2 and existingClasses[list(indices[0])[0]]!=existingClasses[list(indices[0])[1]]:
            if abs(distances[0]-distances[1]) <= d & existingClasses[0]!=existingClasses[1]:
                self.model.radius = r+x
                distances,indices = self.model.radius_neighbors(newPoint)


        # predict class of new data
        if len(indices)!=0:
            # calculate weights (arbitrary weights for now)
            weights = self.determine_weights(indices)

            # sum weights for each class
            classes = existingClasses[list(indices)]
            classes = np.unique(classes[np.where(classes!='0')])  # ignore zero class (outliers)

            classWeight = np.array([]) # initialize weight array

            for i,cl in enumerate(classes):

                classWeight = np.append(classWeight,sum(weights[np.where(classes==cl)]))

            newClass = classes[np.argmax(classWeight)]

        else:
            newClass = '0'

        return(newClass,indices)
