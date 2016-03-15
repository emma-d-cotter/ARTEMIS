import random
import threading
import numpy as np

import datetime
from rules import SendTriggers
from targets import Target
import config


class Stage:
    """"""

    def __init__(self, processor, target_space, send_triggers, source=config.site_name):
        self.processor = processor
        self.target_space = target_space
        self.send_triggers = send_triggers
        self.data_queues = {}
        for stream in config.data_streams:
            self.data_queues[stream] = []
        # NIMS grouped by target_id, so change to dict {target_id: [indices]}
        self.data_queues['nims'] = {}
        self.recent_targets = []
        # Adds ADCP (necessary for testing when not connected to ADCP)
        unixtime = (datetime.datetime.utcnow() - datetime.datetime(1970,1,1))
        self.addDataToStage('adcp', [unixtime.days*24*60*60 + unixtime.seconds, 1.2, 4.5])
        #self.startStageProcessing()

    def processDataBeforeStage(self, stream, data):
        """Performs whatever preprocessing necessitated for data from a
        particular stream, adds data to appropriate target list, then returns
        index for added data in TargetSpace.

        Assumes 'nims' passes a list inside a dict with different tracks.
        """
        if stream == 'adcp':
            data = [datetime.datetime.fromtimestamp(data[0]), data[1], data[2]]
            indices = self.target_space.append_entry(stream, data)
        elif stream == 'pamguard':
            # comm format matches desired, no need to change
            indices = self.target_space.append_entry(stream, data)
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
                indices[track['id']] = self.target_space.append_entry(stream, new_data)
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
            raise ValueError("Error adding data to stage. Data stream {0} not" \
                             " defined in config file.".format(stream))
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
            for target in self.recent_targets:
                # Data is captured in a nims+pamguard Target that will be saved, ignore
                if target.indices.get('pamguard') == pamguard:
                    break
            else:
                # Data not captured in any other Targets, create a new one
                target_out = Target(target_space=self.target_space,
                              source=config.site_name + "_auto",
                              date=self.target_space.get_entry_value_by_index('pamguard', pamguard, 'timestamp'),
                              indices={'pamguard': pamguard, 'adcp': adcp})
                target_out.update_classifier_table
                self.recent_targets.append(target_out)
                return target_out
        elif nims != [] and nims[1] != []:
            print("nims[0]:", nims[0], "nims[1]:", nims[1])
            for target in self.recent_targets:
                if target.get_entry_value('nims', 'id') == nims[0]:
                    # There's an existing target with that id, update that Target object
                    target.update_entry('nims', nims[1])
                    return target
            else:
                    if pamguard:
                        latest_timestamp = max(self.target_space.get_entry_value_by_index('pamguard', pamguard[-1], 'timestamp'),
                                           self.target_space.get_entry_value_by_index('nims', nims[1][-1],'timestamp'))
                    else:
                        latest_timestamp = self.target_space.get_entry_value_by_index('nims', nims[1][-1],'timestamp')
                        pamguard = None

                    if len(nims[1]) == 1:
                        # We don't have existing targets and only one index in queue
                        self.target_space.tables['nims'][nims[1][0]][-1] = []  # changes agg_indices to []
                        target_out = Target(target_space=self.target_space,
                                      source=config.site_name + "_auto",
                                      date=latest_timestamp,
                                      indices={'nims': nims[1][0], 'pamguard': pamguard, 'adcp': adcp})
                        self.recent_targets.append(target_out)
                        return target_out
                    elif len(nims[1]) > 1:
                        # We don't have existing targets, but multiple indices in queue
                        combined_entry = self.target_space.combine_entries('nims', nims[1])
                        self.target_space.tables['nims'].append(combined_entry)
                        index = len(self.target_space.tables['nims']) - 1
                        target_out = Target(target_space=self.target_space,
                                      source=config.site_name + "_auto",
                                      date=latest_timestamp,
                                      indices={'nims': index, 'pamguard': pamguard, 'adcp': adcp})
                        self.recent_targets.append(target_out)
                        return target_out

    def startStageProcessing(self):
        """Creates thread, starts loop that processes stage data."""
        threading.Thread(target=self.processEligibleStagedData).start()

    # Should be looping. That way, we can check time-based conditions.
    def processEligibleStagedData(self):
        """Deletes, classifies, or sends data to rules if eligible."""
        # Only try to create new target in potential pamguard only case
        #while True:
        # determine if ADCP is active
        adcp_index = self.data_queues['adcp']
        adcp_last_seen = self.target_space.get_entry_value_by_index('adcp', adcp_index, 'timestamp')
        adcp_flag = abs(datetime.datetime.now() - adcp_last_seen) > datetime.timedelta(0,60*config.adcp_last_seen_threshold,0)

        if adcp_flag:
            raise Exception('ADCP has is no longer updating, cannot classify features.')

        if self.data_queues['pamguard'] != []:
            pamguard_exceeds_max_time = (datetime.datetime.utcnow() -
                    self.target_space.get_entry_value_by_index('pamguard',
                    self.data_queues['pamguard'],'timestamp') >= datetime.timedelta(
                    seconds=config.data_streams_classifier_triggers['pamguard_max_time']))
            if pamguard_exceeds_max_time:
                target = createOrUpdateTarget(pamguard=self.data_queues['pamguard'],
                                              adcp=self.data_queues['adcp'])
                self.data_queues['pamguard'] = []
                self.recent_targets.append(target)
                self.send_triggers.check_saving_rules(target, None)
                self.send_triggers.send_triggers_if_ready()

        track_ids_to_remove = []
        for track_id in self.data_queues['nims']:
            # If max_pings or max_time, create/update Target
            ping_count = len(self.data_queues['nims'][track_id])
            exceeds_max_pings = (ping_count >=
                    config.data_streams_classifier_triggers['nims_max_pings'])
            exceeds_max_time = (datetime.datetime.utcnow() -
                    self.target_space.get_entry_value_by_index('nims',
                    self.data_queues['nims'][track_id][-1], 'timestamp')
                    >= datetime.timedelta(seconds=config.data_streams_classifier_triggers['nims_max_time']))
            if exceeds_max_pings or exceeds_max_time:
                target = self.createOrUpdateTarget(nims=(track_id, self.data_queues['nims'][track_id]),
                                              pamguard=self.data_queues['pamguard'],
                                              adcp=self.data_queues['adcp'])
                track_ids_to_remove.append(track_id)
                self.processor.addTargetToQueue(target)

        for track_id in track_ids_to_remove: self.data_queues['nims'].pop(track_id)

        for recent_target in self.recent_targets:
            if (datetime.datetime.utcnow() - recent_target.date).seconds >= config.drop_target_time:
                print('Start removal process for Target:', recent_target.indices)
                # Remove recent target from list
                self.recent_targets.remove(recent_target)
                # Processes any stage data remaining
                rt_nims_id = recent_target.get_entry_value('nims','id')
                #if self.data_queues['nims'].get(rt_nims_id):
                #    new_target = self.createOrUpdateTarget(adcp=self.data_queues['adcp'],
                #            pamguard=self.data_queues['pamguard'],
                #            nims=self.data_queues['nims'].get(rt_nims_id))
                #else:
                #    new_target = self.createOrUpdateTarget(adcp=self.data_queues['adcp'],
                #            pamguard=self.data_queues['pamguard'])
                #if self.data_queues['nims'].get(rt_nims_id):
                #    self.processor.addTargetToQueue(new_target)
                # Update classifier features list
                self.target_space.update_classifier_tables(recent_target)
                # Clear nims and pamguard
                self.target_space.update(recent_target)
