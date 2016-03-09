import random
import threading

import datetime
from .rules import SendTriggers
from . import config


class Stage:
    """"""

    def __init__(self, classifier, target_space, send_triggers, source=config.site_name):
        self.classifier_queue = StageClassifierQueue(classifier, target_space, self, send_triggers)
        self.target_space = target_space
        self.send_triggers = send_triggers
        self.data_queues = {}
        for stream in config.data_streams:
            self.data_queues[stream] = []
        # NIMS grouped by target_id, so change to dict {target_id: [indices]}
        self.data_queues['nims'] = {}
        self.recent_targets = []

        #self.startStageProcessing()

    def processDataBeforeStage(self, stream, data):
        """Performs whatever preprocessing necessitated for data from a
        particular stream, adds data to appropriate target list, then returns
        index for added data in TargetSpace.

        Assumes 'nims' passes a list inside a dict with different tracks.
        """
        if stream == 'adcp':
            data = [datetime.datetime.fromtimestamp(data[0]), data[1], data[2]]
            self.target_space.tables[stream].append(data)
            return len(self.target_space.tables[stream]) - 1
        elif stream == 'pamguard':
            # comm format matches desired, no need to change
            self.target_space.tables[stream].append(data)
            return len(self.target_space.tables[stream]) - 1
        elif stream == 'nims':
            indices = {}
            timestamp = data[0]
            for track in data[1]:
                new_data = [timestamp, track['id'], track['pings_visible'],
                        track['first_ping'], track['target_strength'], track['width'],
                        track['height'], track['size_sq_m'], track['speed_mps'],
                        track['min_angle_m'], track['min_range_m'], track['max_angle_m'],
                        track['max_range_m'], track['last_pos_angle'],
                        track['last_pos_range'], None]
                self.target_space.tables[stream].append(new_data)
                indices[track['id']] = len(self.target_space.tables[stream]) - 1
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
        stage_indices = self.processDataBeforeStage(stream, data)
        if stream == 'nims':  # indexed
            for track_id in stage_indices:
                if track_id not in self.data_queues[stream]:
                    self.data_queues[stream][track_id] = []
                self.data_queues[stream][track_id].append(stage_indices[track_id])
        elif stream == 'pamguard' or stream == 'adcp':  # one at any time
            self.data_queues[stream] = stage_indices
        else:
            self.data_queues[stream].append(stage_indices)  # can have multiple

    def createOrUpdateTarget(self, nims=[], pamguard=[], adcp=[]):
        """Appends or creates a Target instance based on current staged data."""
        if pamguard != [] and nims == []:
            print("pamguard != [] and nims == []")
            for target in self.recent_targets:
                # Data is captured in a nims+pamguard Target that will be saved, ignore
                if target.indices.get('pamguard') == pamguard:
                    print("target.indices.get('pamguard') == pamguard")
                    break
            else:
                print("target.indices.get('pamguard') != pamguard for all")
                # Data not captured in any other Targets, create a new one
                target_out = Target(target_space=self.target_space,
                              source=self.source,
                              date=self.target_space.get_entry_by_index('pamguard', pamguard)['timestamp'],
                              indices={'pamguard': pamguard, 'adcp': adcp})
                target_out.update_classifier_table
                self.recent_targets.append(target_out)
                print("target_out: ", target_out)
                return target_out
        elif nims != [] and nims[1] != []:
            print("nims != [] and nims[1] != []")
            print('recent_targets: ', self.recent_targets)
            for target in self.recent_targets:
                if target.get_entry('nims')['id'] == nims[0]:
                    print("target.get_entry('nims')['id'] == nims[0]")
                    # There's an existing target with that id, update that Target object
                    target.update_entry('nims', nims[1])
                    print("target_out: ", target)
                    return target
            else:
                    print("target.get_entry('nims')['id'] != nims[0] for all")
                    latest_timestamp = max(self.target_space.get_entry_by_index('pamguard', pamguard),
                                           self.target_space.get_entry_by_index('nims', nims[1][len(nims[1])-1]))
                    if len(nims[1]) == 1:
                        print("len(nims[1]) == 1")
                        # We don't have existing targets and only one index in queue
                        target_out = Target(target_space=self.target_space,
                                      source=self.source,
                                      date=latest_timestamp,
                                      indices={'nims': nims[1][0], 'pamguard': pamguard, 'adcp': adcp})
                        self.recent_targets.append(target_out)
                        print("target_out: ", target_out)
                        return target_out
                    elif len(nims[1]) > 1:
                        print("len(nims[1]) > 1")
                        # We don't have existing targets, but multiple indices in queue
                        combined_entry = self.target_space.combine_entries('nims', nims[1])
                        self.target_space.tables['nims'].append(combined_entry)
                        index = len(self.target_space.tables['nims']) - 1
                        target_out = Target(target_space=self.target_space,
                                      source=self.source,
                                      date=latest_timestamp,
                                      indices={'nims': index, 'pamguard': pamguard, 'adcp': adcp})
                        self.recent_targets.append(target_out)
                        print("target_out: ", target_out)
                        return target_out

    def startStageProcessing(self):
        """Creates thread, starts loop that processes stage data."""
        threading.Thread(target=self.processEligibleStagedData).start()

    # Should be looping. That way, we can check time-based conditions.
    def processEligibleStagedData(self):
        """Deletes, classifies, or sends data to rules if eligible."""
        # Only try to create new target in potential pamguard only case
        #while True:
        if self.data_queues['pamguard'] != []:
            pamguard_exceeds_max_time = (datetime.datetime.utcnow() -
                    self.target_space.get_entry_by_index('pamguard',
                    self.data_queues['pamguard']).get('timestamp') >= datetime.timedelta(
                    seconds=config.data_streams_classifier_triggers['pamguard_max_time']))
            if pamguard_exceeds_max_time:
                target = createOrUpdateTarget(pamguard=self.data_queues['pamguard'],
                                              adcp=self.data_queues['adcp'])
                self.data_queues['pamguard'] = []
                self.recent_targets.append(target)
                self.send_triggers.check_saving_rules(target, None)
                self.send_triggers.send_triggers_if_ready()

        for track_id in self.data_queues['nims']:
            # If max_pings or max_time, create/update Target
            ping_count = len(self.data_queues['nims'][track_id])
            exceeds_max_pings = (ping_count >=
                    config.data_streams_classifier_triggers['nims_max_pings'])
            exceeds_max_time = (datetime.datetime.utcnow() -
                    self.target_space.get_entry_by_index('nims',
                    self.data_queues['nims'][track_id][-1]).get('timestamp')
                    >= datetime.timedelta(seconds=config.data_streams_classifier_triggers['nims_max_time']))
            if exceeds_max_pings or exceeds_max_time:
                print('nims=(',track_id,",",self.data_queues['nims'][track_id],")")
                print('pamguard=',self.data_queues['pamguard'])
                print('adcp=',self.data_queues['adcp'])
                target = self.createOrUpdateTarget(nims=(track_id, self.data_queues['nims'][track_id]),
                                              pamguard=self.data_queues['pamguard'],
                                              adcp=self.data_queues['adcp'])
                print("target after createOrUpdateTarget(): ", target)
                self.data_queues['nims'][track_id] = []
                self.classifier_queue.addTargetToQueue(target)

        max_max_time = max(config.data_streams_classifier_triggers['pamguard_max_time'],
                       config.data_streams_classifier_triggers['nims_max_time'])
        for recent_target in self.recent_targets:
            if datetime.datetime.utcnow() - recent_target.date >= max_max_time:
                # Remove recent target from list
                print("recent_targets.remove(",recent_target,")")
                #self.recent_targets.remove(x)

class StageClassifierQueue:
    """"""

    def __init__(self, classifier, target_space, stage, send_triggers, prioritization='lifo'):
        self.classifier = classifier
        self.stage = stage
        self.target_space = target_space
        self.prioritization = prioritization
        self.queue = []
        self.send_triggers = send_triggers
        self.startClassifierQueueProcessing()

    def addTargetToQueue(self, target):
        """Adds a target object to the 'to be classified' queue using the
        prioritization scheme defined for the class.

        Last target in list will be considered front of queue (first to be popped).
        """
        if self.prioritization == 'lifo':
            self.queue.append(target)
        else:
            raise ValueError("Prioritization scheme {0} undefined for " \
                    "StageClassifierQueue.".format(self.prioritization))

    def startClassifierQueueProcessing(self):
        """Creates thread, starts loop that processes stage data."""
        threading.Thread(target=self.fitClassificationsAndTriggerRules).start()

    def fitClassificationsAndTriggerRules(self):
        """Continuously classifies any targets inside of queue."""
        while True:
            if len(self.queue) >= 1:
                target = self.queue.pop()
                print('queue: ', self.queue)
                print('target: ', target)
                print("Finally, going to classify! Check out target_space classifier index {0}.".format(target.indices['classifier']))
                X = self.target_space.tables['classifier_features'][target.indices['classifier']]
                classification = self.classifier.predict(X) #random.choice()
                target.indices['classification'] = classification
                print('Classified target {0}, classification: {1}'.format(target, classification))
                self.send_triggers.check_saving_rules(target, classification)
            self.send_triggers.send_triggers_if_ready()
