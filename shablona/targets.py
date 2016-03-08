from datetime import datetime

from . import config
from .classification import _scale_axis


headers = {}
headers['adcp'] = ['timestamp', 'speed', 'heading']
headers['pamguard'] = ['timestamp']
headers['nims'] = ['timestamp', 'id', 'pings_visible', 'first_ping',
        'target_strength', 'width', 'height', 'size_sq_m', 'speed_mps',
        'min_angle_m', 'min_range_m', 'max_angle_m', 'max_range_m',
        'last_pos_angle', 'last_pos_range', 'aggregate_indices']
headers['classifier'] = []  # Should these be relative to input headers?

class Target:
    """"""
    def __init__(self, target_space, source="Unknown", date=datetime.utcnow(), indices={}):
        self.target_space = target_space
        self.source = source
        self.date = date
        self.indices = indices

    def get_entry(self, table):
        """Returns dictionary of table headers and values for given table."""
        if table not in headers:
            raise ValueError("{0} is an invalid data stream or table name. Valid inputs are " \
                    "'classifier_{features,classifications}' or data stream name.".format(table))
        elif table not in self.tables:
            raise ValueError("Table {0} not found in target space. Following tables available:  " \
                    ' '.join(list(self.tables.keys()))
        else:
            return dict(zip(headers[table], self.tables[table][self.indices[table]]))

    def combine_entries(self, table, indices):
        """Expects indices to be in order of read. That is, last
        entry is the latest in the list.
        """
        combined_entry = []
        for column_name in headers[table]:
            values = []
            for index in indices:
                values.append(target_space.tables[table][index][column_name])

            if column_name in ['timestamp', 'first_ping', 'min_angle_m', 'min_range_m']:
                combined_entry.append(min(values))
            elif column_name in ['pings_visible', 'max_angle_m', 'max_range_m']:
                combined_entry.append(max(values))
            elif column_name in ['id']:
                if len(set(values)) > 1:
                    raise ValueError("Internal errror. All ids " \
                            "in combine_entries are expected to match.")
                combined_entry.append(values[0])
            elif column_name in ['target_strength', 'width', 'height',
                                 'size_sq_m', 'speed_mps']:
                combined_entry.append(sum(values) / float(values))
            elif column_name in ['last_pos_angle', 'last_pos_range']:
                combined_entry.append(values[len(values) - 1])
            elif column_name == 'aggregate_indices':
                combined_entry.append(indices)
        return combined_entry

    def update_entry(self, table, indices):
        """Rules to update an existing target entry with
        additional data. Throws error if unable to update,
        returns nothing otherwise.

        NIMS records list of indices from which it is derived
        in 'aggregate_indices' field.
        """
        if table == 'nims':
            old_index = self.indices[table]
            indices.insert(0,old_index)
            old_entry = self.get_entry(table)
            if old_entry['aggregate_indices'] == None:
                location = len(self.target_space.tables[table])
            else:
                location = old_index
            new_entry = self.combine_entries(table, indices)
            self.target_space.tables[table][location] = new_entry

    # TODO: Remove all getX() when all calls gone
    def getNIMS(self):
        if 'nims' in self.target_space.input_data and self.indices['nims'] != None:
            return dict(zip(headers['nims'],
                            self.target_space.input_data['nims'][self.indices['nims']]))

    def getPamGuard(self):
        if 'pamguard' in self.target_space.input_data and self.indices['pamguard'] != None:
            return dict(zip(headers['pamguard'],
                            self.target_space.input_data['pamguard'][self.indices['pamguard']]))

    def getADCP(self):
        if 'adcp' in self.target_space.input_data and self.indices['adcp'] != None:
            return dict(zip(headers['adcp'],
                            self.target_space.input_data['adcp'][self.indices['adcp']]))

class TargetSpace:
    """"""

    def __init__(self):
        self.targets = []
        self.tables = {}
        for stream in config.data_streams:
            self.tables[stream] = []
        self.classifier_features = []
        self.classifier_classifications = []
        self.classifier_index_to_target = {}

    def get_entry_by_index(self, table, index):
        """Returns dictionary of table headers and values for given index for table."""
        if table not in headers:
            raise ValueError("{0} is an invalid data stream or table name. Valid inputs are " \
                    "'classifier_{features,classifications}' or data stream name.".format(table))
        elif table not in self.tables:
            raise ValueError("Table {0} not found in target space. Following tables available: " \
                    "{1}".format(' '.join(list(self.tables.keys()))))
        elif index < 0 or index >= len(self.tables[table]):
            raise ValueError("Invalid index {0}. {1} table is of length {2}.".format(index, table,
                    len(self.tables[table])))
        else:
            return dict(zip(headers[table], self.tables[table][index]))

    def load_targets(self, file, format, delimiter=';'):
        """Reads targets from file, creating Target instances and appending
        features and classification to relevant numpy array.
        """
        if format == 'csv':
            if os.path.isfile(file):
                with open(file, 'r') as f:
                    for record in csv.DictReader(f, delimiter = delimiter):

                        instance = Target(self.target_space,
                                          source=record['source'],
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
