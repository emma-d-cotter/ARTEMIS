import .config as config


class Stage:
    """"""

    def __init__(self):
        self.data_queues = {}
        for stream in config.data_streams:
            self.data_queues[stream] = []

    def processDataBeforeStage(stream, data):
        """Performs whatever preprocessing necessitated for data from a
        particular stream, adds data to appropriate target list, then returns
        index to post-processing data.
        """
        if stream is 'adcp':
            pass
        elif stream is 'camera':
            pass
        elif stream is 'pamguard':
            pass
        elif stream is 'nims':
            pass
        elif stream in config.data_streams:
            pass
        else:
            # TODO: Failing when data stream mismatches may be too extreme. We
            # want to keep the data and potentially fail more softly.
            raise ValueError("Error processing data for stage. Stream {0} not \
                              defined in config file.".format(stream))

    def addDataToStage(self, stream, data):
        """Calls processing function for data based on stream then adds data to
        stream-specific queue.
        """
        if stream not in config.data_streams:
            raise ValueError("Error adding data to stage. Stream {0} not \
                              defined in config file.".format(stream))
        index = processDataBeforeStage(stream, data)
        self.data_queues[stream].append(index)
        target = streamDataToTarget(stream, data)
        initiateClassificationIfEligible(stream)

    def streamDataToTarget(self, stream, data):
        """Appends or creates a Target instance based on current staged data."""
        # TODO: Ask Emma "how to tell that repeating data is attached to same target?"
        # For NIMS, we know target_id is the same. PAMGuard? Start and end time?
        if stream is 'adcp':

    def initiateClassificationIfEligible(self, stream):
        """Calls classifier.fit() if eligible given specified rules."""
        # TODO: Vague documentation, any way to be more specific?
        # TODO: Ask Emma about what things should trigger a classification.
        if stream is 'adcp':
            pass
        elif stream is 'camera':
            pass
        elif stream is 'pamguard':
            pass
        elif stream is 'nims':
            pass
        elif stream in config.data_streams:
            pass
        else:
            # TODO: Failing when data stream mismatches may be too extreme. We
            # want to keep the data and potentially fail more softly.
            raise ValueError("Error processing data for stage. Stream {0} not \
                              defined in config file.".format(stream))
