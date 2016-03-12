import queue
import threading
import os
import csv
import numpy as np

import targets
import config
from classification import _scale_axis

class ClassificationProcessor:
    """"""

    def __init__(self, classifier, target_space, send_triggers,
                 auto_start_thread=True):
        self.classifier = classifier
        self.target_space = target_space
        self.send_triggers = send_triggers

        self.queue = queue.Queue()
        self.classification_count = 0

        if auto_start_thread: self.startThread()

    def addTargetToQueue(self, target):
        """Adds a target object to the 'to be classified' queue using the
        prioritization scheme defined for the class.

        First target in list will be considered front of queue (first to be popped).
        """
        self.queue.put(target)

    def startThread(self):
        """Start thread with all classification processing tasks defined
        in `threadFunctions`.
        """
        threading.Thread(target=self.threadFunctions).start()

    def threadFunctions(self):
        """Procedure to run when thread starts."""
        self.load_targets("current_model_targets.csv",'csv')
        self.fit_classifier()
        self.fitClassificationsAndTriggerRules()

    def fit_classifier(self):
        self.classifier.fit(self.target_space.tables['classifier_features'],
                            self.target_space.tables['classifier_classifications'])

    def load_targets(self, file, format, delimiter=';'):
        """Reads targets from file, creating Target instances and appending
        features and classification to relevant numpy array.
        """
        if format == 'csv':
            if os.path.isfile(file):
                with open(file, 'r') as f:
                    for record in csv.DictReader(f, delimiter = delimiter):

                        instance = targets.Target(self.target_space,
                                          source=record['source'],
                                          date=record['date'])
                        index = len(self.target_space.tables['classifier_features'])
                        assert(len(self.target_space.tables['classifier_features'])
                                == len(self.target_space.tables['classifier_classifications']))
                        self.target_space.targets.append(index)

                        instance.indices['classifier'] = index
                        self.target_space.classifier_index_to_target[index] = instance
                        self.target_space.tables['classifier_features'].append([
                            _scale_axis(float(record['size']), 'size'),
                            _scale_axis(float(record['speed']), 'speed'),
                            _scale_axis(float(record['deltav']), 'deltav'),
                            _scale_axis(float(record['target_strength']),
                                    'target_strength'),
                            _scale_axis(float(record['time_of_day']),
                                    'time_of_day'),
                            _scale_axis(float(record['current']), 'current')])
                        self.target_space.tables['classifier_classifications'].append(
                                record['classification'])
            else:
                raise IOError("Unable to find csv file {0} to load targets.".
                        format(file))


    def fitClassificationsAndTriggerRules(self):
        """Continuously classifies any targets inside of queue."""
        while True:
            if not self.queue.empty():
                target = self.queue.get()
                X = np.array(target.get_classifier_features()).reshape(1, -1)
                print("inputs (X) for classification:", X)
                classification = np.squeeze(self.classifier.predict(X))
                target.classification = classification
                print('Classified target {0}, classification: {1}'.format(target, classification))
                self.send_triggers.check_saving_rules(target, classification)
                self.classification_count += 1
                if self.classification_count < config.refit_classifier_count:
                    self.fit_classifier()
                    self.target_space.update()
                    self.classification_count = 0
            self.send_triggers.send_triggers_if_ready()
