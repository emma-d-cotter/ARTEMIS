import .config as config


class Target:
    """"""
    def __init__(self, source="Unknown", date=datetime.now(), indices=None):
        self.source = source
        self.date = date
        if data_indices == None:
            self.indices = {}
        else:
            self.indices = indices

    # TODO: convert get functions to automated format, likely getData('nims')
    def getNIMS(self, index):
        if 'nims' in self.target_space.data_streams:
            return self.target_space.data_streams['nims'][index]

    def getPamGuard(self, index):
        if 'pamguard' in self.target_space.data_streams:
            return self.target_space.data_streams['pamguard'][index]

    def getADCP(self, index):
        if 'adcp' in self.target_space.data_streams:
            return self.target_space.data_streams['adcp'][index]

class TargetSpace:
    """"""
    def __init__(self):
        self.targets = []
        self.data_streams = {}
        for stream in config.data_streams:
            self.data_streams[stream] = []
        self.classifier_features = []
        self.classifier_classifications = []
        self.classifier_index_to_target = {}

    def load_targets(self, file, format, delimiter=';'):
        """Reads targets from file, creating Target instances and appending
        features and classification to relevant numpy array.
        """
        if format == 'csv':
            if os.path.isfile(file):
                with open(file, 'r') as f:
                    for record in csv.DictReader(f, delimiter = delimiter):

                        instance = Target(source=record['source'],
                                          date=record['date'])
                        index = len(self.targets)
                        self.targets.append(index)

                        if record['classifiable']:
                            assert(len(self.classifier_classifications) == index)
                            assert(len(self.classifier_features) == index)

                            instance.indices['classifier'] = index
                            self.classifier_index_to_target[index] = instance
                            self.classifier_features.append(
                                _scale_axis(record['size'], 'size'),
                                _scale_axis(record['speed'], 'speed'),
                                _scale_axis(record['deltav'], 'deltav'),
                                _scale_axis(record['target_strength'],
                                        'target_strength'),
                                _scale_axis(record['time_of_day'],
                                        'time_of_day'),
                                _scale_axis(record['current'], 'current')])
                            self.classifier_classifications.
                                    append(record['classification'])

            else:
                raise IOError("Unable to find csv file {0} to load targets.".
                        format(file))
