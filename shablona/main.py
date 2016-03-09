import .targets as targets
import .classification as cl
import .stage as stage
import .rules as rules
import .comms as comms
import datetime

if __name__ == "__main__":
    # intitialize target space
    target_space = targets.TargetSpace()

    # intialize classifier
    background_classifier = cl.BackgroundClassifier()
    rad_neigh_classifier = cl.RadiusNeighborsClassifier(cl.classification_weights,
                                                        target_space,
                                                        outliers=background_classifier)

    # initialize socket to send triggers to LabView
    send_triggers = rules.SendTriggers()

    # initialize stage for data handling
    stage_instance = stage.Stage(rad_neigh_classifier, target_space, send_triggers)

    # start instrument communications
    comms_instance = comms.InstrumentComms(stage_instance, True)
