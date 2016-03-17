import socket
from datetime import datetime
from config import instrument_ranges
from config import ADCP_threshold
from config import instruments
from config import instrument_buffer_sizes
from config import saving_parameters

# TODO: add function to deal with strobes. If it's night...we don't want to
# offload immediately
class SendTriggers:

    def __init__(self):
        self.trigger_status = self.init_trigger_status()
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.udp_IP = "localhost"
        self.udp_port = 61500


    def check_saving_rules(self, target, classification):
        """
        Rules to determine what, if any, instruments should save a recorded
        target. This script is intended to be modified to match data collection
        priorities/goals.

        Current rule hierarchy:

                       PAMGuard detection?
                    /                      \
                   /                        \
                Yes:                          No:
            Any detecion                Current above
            from NIMS?                  threshold?
            /       \                     /       \
           /         \                   /         \
        Yes:          No:              Yes:         No:
        save         save           is the          save none
        all        hydrophones      classification
                                    interesting?
                                    (defined with
                                    classes_to_save)
                                    /           \
                                   /             \
                                Yes:            No:
                                Save            save none
                                instruments
                                in range + PAM
        """

        classes_to_save = ['1','2','3']
        PAMGuard = target.get_entry('pamguard')
        ADCP = target.get_entry('adcp')
        NIMS = target.get_entry('nims')

        # if there is a marine mammal detection from  PAMGuard
        if PAMGuard:
            # if there is no detection from NIMS, only save hydrophones
            if not NIMS:
                new_trigs = ['hydrophones']
            # if there is any detection from NIMS, save all instruments
            else:
                new_trigs = ['hydrophones', 'm3', 'blueview', 'cameras']

        else:
            # if the current speed is greater than the threshold
            if ADCP['speed'] > ADCP_threshold:
                if classification in classes_to_save:
                    new_trigs = self.evaluate_target_range(target)
                else:
                    new_trigs = []
            else:
                new_trigs = []

        # add any new triggers to trigger_status list
        for inst in new_trigs:
            self.trigger_status['unsent_trigs'][inst].append(target.date)

    def evaluate_target_range(self, target):
        """
        Determine which instruments may be able to detect a target based on
        the minimum range at which the target was detected.

        M3 and hydrophones are always saved if there is an "interesting" NIMS
        detection, and cameras and BlueView are added if the target passes within
        their range
        """
        NIMS = target.get_entry('nims')
        target_min_range = NIMS['min_range_m']

        new_trigs = ['hydrophones', 'm3']

        if target_min_range > instrument_ranges['camera']:
            new_trigs += 'camera'

        if target_min_range > instrument_ranges['blueview']:
            new_trigs += 'blueview'

        return new_trigs


    def send_triggers_if_ready(self):
        """
        Determine what, if any save triggers to send to LabView, and send over UDP.
        """
        trigs_to_send = []

        timestamp = datetime.utcnow()
        unsent_trigs = self.trigger_status['unsent_trigs']
        last_trigger = self.trigger_status['last_trigger']
        buffer_overlap = saving_parameters['buffer_overlap']
        min_time_between_targets = saving_parameters['min_time_between_targets']
        time_before_target = saving_parameters['time_before_target']

        # for all triggers that have not been sent yet (unsent_trigs)
        for inst in unsent_trigs:
            if unsent_trigs[inst]:
                # calculate elapsed time since the target was detected
                time_since_detection = self.delta_t_in_seconds(
                    timestamp, unsent_trigs[inst][0])

                # calculate elapsed time since the last trigger for this instrument
                time_since_last_trigger = self.delta_t_in_seconds(
                    timestamp, last_trigger[inst])

                # Determine if more time than "wait_before_send" (from config)
                # has elapsed since detection.
                if time_since_detection >= instrument_buffer_sizes[inst] - time_before_target:
                    # Determine if sufficient time has passed since last trigger
                    # was sent to inst to create an overlap of "buffer_overlap"
                    # (from config) in the saved data
                    #print('time_since_last_trigger:', time_since_last_trigger)
                    #print('inst_buffer_sizes[inst]-buffer_overlap', (instrument_buffer_sizes[inst] - buffer_overlap))
                    if time_since_last_trigger >= (instrument_buffer_sizes[inst] - buffer_overlap):
                    #    print('time_since_last_trigger >= (instrument_buffer_sizes[inst] - buffer_overlap)')
                        unsent_trigs[inst].pop(0)
                        trigs_to_send.append(inst)
                        last_trigger[inst] = timestamp

                        # remove triggers that are within min_time_between_targets
                        # (i.e. already saved by this buffer)
                        for index, unsent_trig in enumerate(unsent_trigs[inst]):
                            time_since_detection = self.delta_t_in_seconds(
                                last_trigger[inst], unsent_trigs[inst][index])
                            if time_since_detection < min_time_between_targets:
                                unsent_trigs[inst].pop(index)

        # send triggers over socket!
        if trigs_to_send:
            print('sending triggers for ', trigs_to_send)
            self.send_triggers(trigs_to_send)

        self.trigger_status = {
                               'unsent_trigs': unsent_trigs,
                               'last_trigger': last_trigger
                               }


    def delta_t_in_seconds(self, datetime1, datetime2):
        """
        calculate delta t in seconds between two datetime objects
        (returns absolute value, so order of dates is insignifigant)
        """
        delta_t = datetime1 - datetime2
        days_s = delta_t.days*(86400)
        microseconds_s = delta_t.microseconds/1000000
        delta_t_s = days_s + delta_t.seconds + microseconds_s

        return abs(delta_t_s)


    def send_triggers(self, trigs_to_send):
        """
        send triggers to save data to AMP interface.

        Inputs:
        sock - socket over which to send data (create with
               socket.socket(socket.AF_INET, socket.SOCK_DGRAM))
        udp_IP - IP address to send data over (typically "localhost")
        udp_port - port to send data over (typically 61500)
        new_trigs - list of instruments to send trigger

        Outputs:
        bytes_sent = number of bytes sent, should be 17 for 4 instruments.

        Data is sent in the following format:
            "AAAA 1 1 1 1 1 ZZZZ" where "AAAA" and "ZZZZZ" are always the header
            and footer, and the "1" values are zero or 1 if that instrument
            should offload data (in the order of the instruments list from
            config)
        """


        msg = "AAAA "

        for instrument in instruments:
            if instrument in trigs_to_send:
                msg += '1 '
            else:
                msg += '0 '

        msg += 'ZZZZ'

        print('sent message:', msg)
        msg = bytes(msg, 'utf-8')

        bytes_sent = self.sock.sendto(msg, (self.udp_IP, self.udp_port))

        return bytes_sent


    def init_trigger_status(self):

        zero_time = datetime(2000,1,1,0,0,0)

        last_trigger = {}
        unsent_trigs = {}
        for inst in instruments:
            last_trigger[inst] = zero_time
            unsent_trigs[inst] = []

        trigger_status = {
                          'last_trigger': last_trigger,
                          'unsent_trigs': unsent_trigs
                          }

        return trigger_status
