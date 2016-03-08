import random

from datetime import datetime
from .rules import SendTriggers
from . import config


class Stage:
    """"""

    def __init__(self, classifier, target_space, send_triggers):
        self.classifier_queue = StageClassifierQueue(classifier, target_space, self)
        self.target_space = target_space
        self.data_queues = {}
        for stream in config.data_streams:
            self.data_queues[stream] = []
        # NIMS grouped by target_id, so change to dict {target_id: [indices]}
        self.data_queues['nims'] = {}
        self.data_queues['nims-simulator'] = {}

    def processDataBeforeStage(self, stream, data):
        """Performs whatever preprocessing necessitated for data from a
        particular stream, adds data to appropriate target list, then returns
        index for added data in TargetSpace.

        Assumes 'nims-simulator' passes a list inside a list with different tracks.
        """
        if stream == 'adcp':
            data = [datetime.fromtimestamp(data[0]), data[1], data[2]]
            self.target_space.input_data[stream].append(data)
            return len(self.target_space.input_data[stream]) - 1
        elif stream == 'pamguard':
            # comm format matches desired, no need to change
            self.target_space.input_data[stream].append(data)
            return len(self.target_space.input_data[stream]) - 1
        elif stream == 'nims' or stream == 'nims-simulator':
            indices = {}
            timestamp = data[0]
            for track in data[1]:
                new_data = [timestamp, track['id'], track['pings_visible'],
                        track['first_ping'], track['target_strength'], track['width'],
                        track['height'], track['size_sq_m'], track['speed_mps'],
                        track['min_angle_m'], track['min_range_m'], track['max_angle_m'],
                        track['max_range_m'], track['last_pos_angle'], track['last_pos_range']]
                self.target_space.input_data[stream].append(new_data)
                indices[track['id']] = len(self.target_space.input_data[stream]) - 1

        elif stream in config.data_streams:
            raise ValueError("No stage processing functionality exists for" \
                             " data stream {0}.".format(stream))
        else:
            raise ValueError("Error processing data for stage. Stream {0} not" \
                              " defined in config file.".format(stream))

        return indices

    def addDataToStage(self, stream, data):
        """Calls processing function for data based on stream then adds data to
        stream-specific queue.
        """
        if stream not in config.data_streams:
            raise ValueError("Error adding data to stage. Stream {0} not \
                              defined in config file.".format(stream))
        stageIndices = self.processDataBeforeStage(stream, data)
        if stream == 'nims' or stream == 'nims-simulator':
            for track_id in stageIndices:
                if track_id not in self.data_queues[stream]:
                    self.data_queues[stream][track_id] = []
                self.data_queues[stream][track_id].append(stageIndices[track_id])
        else:
            self.data_queues[stream].append(stageIndices)

    def createOrUpdateTarget(self, stream, key):
        """Appends or creates a Target instance based on current staged data."""
        self.data_queues[stream]

    # Should be looping. That way, we can check time-based conditions.
    def processEligibleStagedData(self):
        """Deletes, classifies, or sends data to rules if eligible."""
        for track_id in self.data_queues['nims-simulator']:
            if len(self.data_queues['nims-simulator'][track_id]) >=
                    config.data_streams_classifier_triggers['nims-simulator_max_pings']:
                # create/update Target
                target = createOrUpdateTarget()
                # remove from stage
                self.data_queues['nims-simulator'][track_id] = []
                # trigger classification
                self.classifier_queue.addTargetToQueue(target)


class StageClassifierQueue:
    """"""

    def __init__(classifier, target_space, stage, send_triggers, prioritization='lifo'):
        self.classifier = classifier
        self.stage = stage
        self.target_space = target_space
        self.prioritization = prioritization
        self.queue = []
        self.send_triggers = send_triggers

    def addTargetToQueue(target):
        """Adds a target object to the 'to be classified' queue using the
        prioritization scheme defined for the class.

        Last target in list will be considered front of queue (first to be popped).
        """
        if self.prioritization == 'lifo':
            self.queue.append(target)
        else:
            raise ValueError("Prioritization scheme {0} undefined for " \
                    "StageClassifierQueue.".format(self.prioritization))

    def fitClassificationsAndTriggerRules():
        """Continuously classifies any targets inside of queue."""
        while True:
            if len(self.queue) >= 1:
                target = self.queue.pop()
                X = target_space.classifier_features[target.data_indices['classifier']]
                classification = self.classifier.fit(X) #random.choice()
                target.indices['classification'] = classification
                self.send_triggers.check_saving_rules(target, classification)
            self.send_triggers.send_triggers_if_ready()
