import targets
import classification as cl
import stage
import rules
import comms
import processor

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

    # initialize classification processor
    classification_processor = processor.ClassificationProcessor(rad_neigh_classifier,
                                                                 target_space,
                                                                 send_triggers,
                                                                 True)

    # initialize stage for data handling
    stage_instance = stage.Stage(classification_processor, target_space, send_triggers)

    # start instrument communications
    comms_instance = comms.InstrumentComms(stage_instance, True)
