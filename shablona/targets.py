from datetime import datetime

from . import config
from .classification import _scale_axis

class Target:
    """"""
    def __init__(self, source="Unknown", date=datetime.utcnow(), indices=None):
        self.source = source
        self.date = date
        if data_indices == None:
            self.indices = {}
        else:
            self.indices = indices

    # TODO: convert get functions to automated format, likely getData('nims')
    def getNIMS(self, index):
        if 'nims' in self.target_space.input_data:
            return self.target_space.input_data['nims'][index]

    def getPamGuard(self, index):
        if 'pamguard' in self.target_space.input_data:
            return self.target_space.input_data['pamguard'][index]

    def getADCP(self, index):
        if 'adcp' in self.target_space.input_data:
            return self.target_space.input_data['adcp'][index]

class TargetSpace:
    """"""

    headers = {}
    headers['adcp'] = ['timestamp', 'speed', 'heading']
    headers['pamguard'] = ['timestamp']
    headers['nims'] = ['timestamp', 'id', 'pings_visible', 'first_ping',
            'target_strength', 'width', 'height', 'size_sq_m', 'speed_mps',
            'min_angle_m', 'min_range_m', 'max_angle_m', 'max_range_m',
            'last_pos_angle', 'last_pos_range']
    headers['classifier'] = []  # Should these be relative to input headers?

    def __init__(self):
        self.targets = []
        self.input_data = {}
        for stream in config.data_streams:
            self.input_data[stream] = []
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
                                _scale_axis(record['current'], 'current'))
                            self.classifier_classifications.append(record['classification'])

            else:
                raise IOError("Unable to find csv file {0} to load targets.".
                        format(file))
