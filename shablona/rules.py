import socket
from datetime import datetime
from .config import instrument_ranges
from .config import ADCP_threshold
from .config import instruments


def send_save_triggers(socket, target, classification, trigger_status):

    """
    Rules to determine what, if any, instruments should save a recorded target.
    This script is intended to be modified to match data collection
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
                            in range
    """

    classes_to_save = [1,2,3]
    PAMGuard = target.getPamGuard()
    ADCP = target.getADCP()
    NIMS = target.getNIMS()

    # if there is a marine mammal detection from  PAMGuard
    if PAMGuard != None:
        # if there is no detection from NIMS, only save hydrophones
        if not NIMS:
            new_trigs = ['hydrophones']
        # if there is any detection from NIMS, save all instruments
        else:
            new_trigs = ['hydrophones', 'M3', 'blueview', 'cameras']
    else:
        # if the current speed is greater than the threshold
        if ADCP.speed > ADCP_threshold:
            # if the class is interesting
            if classification in classes_to_save:
                new_trigs = evaluate_target_range(target, NIMS)
            else:
                new_trigs = []
        else:
            new_trigs = []

    if new_trigs

    trigger_status = is_time_to_send(socket, new_trigs, trigger_status)

    return trigger_status


def evaluate_target_range(target):
    """
    Determine which instruments may be able to detect a target based on
    the minimum range at which the target was detected.

    M3 and hydrophones are always saved if there is an "interesting" NIMS
    detection, and cameras and BlueView are added if the target passes within
    their range
    """

    target_min_range = NIMS.min_range_m

    new_trigs = ['hydrophones', 'M3']

    if target_min_range > instrument_ranges['camera']:
        new_trigs += 'camera'

    if target_min_range > instrument_ranges['blueview']:
        new_trigs += 'blueview'

    return new_trigs


def is_time_to_send(socket, udp_IP, udp_port, new_trigs, trigger_status):
    """
    Add any new triggers to trigger_status, and determine what, if any save
    triggers to send to LabView.

    inputs:
    socket - socket over which to send triggers to LabView
    udp_IP - IP address over which to send triggers to LabView ("localhost")
    udp_port - port over which to send triggers to LabView (61500)
    new_triggs - new triggers to send (or wait to send)
    trigger_status - dictionary containing unsent triggers and timestamp that
                    last trigger was sent to each instrument

    """
    trigs_to_send = []

    # current timestamp
    timestamp = datetime.utcnow()

    # extract information from trigger_status
    unsent_trigs = trigger_status['unsent_trigs']
    last_trigger = trigger_status['last_trigger']

    # extract saving parameters
    buffer_overlap = saving_parameters['buffer_overlap']
    min_time_between_targets = saving_parameters['min_time_between_targets']
    wait_before_send = saving_parameters['wait_before_send']

    # add any new triggers to trigger_status list
    for inst in new_trigs:
        unsent_trigs[inst].append(timestamp)


    # for all triggers that have not been sent yet (unsent_trigs)
    for inst in unsent_trigs:
        if unsent_trigs[inst]:
            # calculate elapsed time since the target was detected
            time_since_detection = delta_t_in_seconds(timestamp, unsent_trigs[inst][0])
            print(time_since_detection, ' seconds since last ', inst, ' detection')

            # calculate elapsed time since the last trigger for this instrument
            time_since_last_trigger = delta_t_in_seconds(timestamp, last_trigger[inst])
            print(time_since_last_trigger, ' seconds since last ', inst, ' trigger sent')

            # Determine if more time than "wait_before_send" (from config) has elapsed
            # since detection.
            if time_since_detection >= wait_before_send:

                # Determine if sufficient time has passed since last trigger was sent to inst to
                # create an overlap of "buffer_overlap" (from config) in the saved data
                if time_since_last_trigger >= (instrument_buffer_sizes[inst] - buffer_overlap):

                    # remove from unsent_trigs
                    del unsent_trigs[inst][0]

                    trigs_to_send.append(inst)
                    last_trigger[inst] = timestamp

                    # remove triggers that are within min_time_between_targets (i.e.
                    # already saved by this buffer)
                    for index, unsent_trig in enumerate(unsent_trigs[inst]):
                        time_since_detection = delta_t_in_seconds(last_trigger[inst], unsent_trigs[inst][index])

                        if time_since_detection < min_time_between_targets:
                            del unsent_trigs[inst][index]

    # send triggers over socket!
    if trigs_to_send:
        print('sending triggers for ', trigs_to_send)
        send_triggers(sock, udp_IP, udp_port, trigs_to_send)

    trigger_status = {'unsent_trigs': unsent_trigs, 'last_trigger': last_trigger}

    return trigs_to_send, trigger_status


def delta_t_in_seconds(datetime1, datetime2):
    """
    calculate delta t in seconds between two datetime objects
    """
    delta_t = datetime1 - datetime2
    return delta_t.days*(60*60*24) + delta_t.seconds + delta_t.microseconds/1000



def send_triggers(sock, udp_IP, udp_port, trigs_to_send):
    """
    send triggers to save data to AMP interface.

    Inputs:
    sock - socket over which to send data (create with socket.socket(socket.AF_INET, socket.SOCK_DGRAM))
    udp_IP - IP address to send data over (typically "localhost")
    udp_port - port to send data over (typically 61500)
    new_trigs - list of instruments to send trigger

    Outputs:
    bytes_sent = number of bytes sent, should be 17 for 4 instruments.

    Data is sent in the following format:
        "AAAA 1 1 1 1 1 ZZZZ" where "AAAA" and "ZZZZZ" are always the header and
        footer, and the "1" values are zero or 1 if that instrument should
        offload data (in the order of the instruments list from config)
    """


    msg = "AAAA "

    for instrument in instruments:
        if instrument in trigs_to_send:
            msg += '1 '
        else:
            msg += '0 '

    msg += 'ZZZZ'
    msg = bytes(msg, 'utf-8')

    bytes_sent = sock.sendto(msg, (udp_IP, udp_port))

    return bytes_sent
