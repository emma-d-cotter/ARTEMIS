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

class TargetSpace:
    """"""
    def __init__(self):
        self.targets = []
        self.instrument_data = {}
        for instrument in config.instrument_data:
            self.instrument_data[instrument] = []
        self.classifier_features = []
        self.classifier_classifications = []

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

                        if record['classifiable']:
                            instance.classifiable = True
                            assert(len(self.classy_classifications) ==
                                    len(self.classy_features))
                            assert(len(self.classy_classifications) ==
                                    len(self.classy_targets))
                            instance.index = len(self.classy_targets)
                            self.classy_targets.append(instance)
                            self.classy_features.append(
                                _scale_axis(record['size'], 'size'),
                                _scale_axis(record['speed'], 'speed'),
                                _scale_axis(record['deltav'], 'deltav'),
                                _scale_axis(record['target_strength'],
                                        'target_strength'),
                                _scale_axis(record['time_of_day'],
                                        'time_of_day'),
                                _scale_axis(record['current'], 'current')])
                            self.classy_classifications.
                                    append(record['classification'])
                        else:
                            instance.classifiable = False
                            instance.index = len(self.classless_targets)

            else:
                raise IOError("Unable to find csv file {0} to load targets.".
                        format(file))
