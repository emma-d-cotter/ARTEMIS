from .config import instrument_ranges
from .config import ADCP_threshold

def save_triggers(socket, target, classification):
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
            save_trig = ['hydrophones']
        # if there is any detection from NIMS, save all instruments
        else:
            save_trig = ['hydrophones', 'M3', 'blueview', 'cameras']
    else:
        # if the current speed is greater than the threshold
        if ADCP.speed > ADCP_threshold:
            # if the class is interesting
            if classification in classes_to_save:
                save_trig = evaluate_target_range(target, NIMS)
            else:
                save_trig = []
        else:
            save_trig = []

    if save_trig
        send_triggers(socket,save_trig)

    return save_trig


def evaluate_target_range(target):
    """
    Determine which instruments may be able to detect a target based on
    the minimum range at which the target was detected.

    M3 and hydrophones are always saved if there is an "interesting" NIMS
    detection, and cameras and BlueView are added if the target passes within
    their range
    """
    target_min_range = NIMS.min_range_m

    save_trig = ['hydrophones', 'M3']

    if target_min_range > instrument_ranges['camera']:
        save_trig += 'cameras'

    if target_min_range > instrument_ranges['blueview']:
        save_trig += 'blueview'

    return save_trig

def send_triggers(socket, save_trig):
    pass
