from datetime import datetime

import config


headers = {}
headers['adcp'] = ['timestamp', 'speed', 'heading']
headers['pamguard'] = ['timestamp', 'detection']
headers['nims'] = ['timestamp', 'id', 'pings_visible', 'first_ping',
        'target_strength', 'width', 'height', 'size_sq_m', 'speed_mps',
        'min_angle_m', 'min_range_m', 'max_angle_m', 'max_range_m',
        'last_pos_angle', 'last_pos_range', 'aggregate_indices']
headers['classifier'] = config.classifier_features

def _get_minutes_since_midnight(timestamp):
    """"""
    return min(timestamp.hour*60 + timestamp.minute,
        60*24 - (timestamp.hour*60 + timestamp.minute))

class Target:
    """"""
    def __init__(self, target_space, source="Unknown", date=datetime.utcnow(),
                 classification=None, indices={}):
        self.target_space = target_space
        self.source = source
        self.date = date
        self.classification = classification
        self.indices = indices

    def get_entry(self, table):
        """Returns dictionary of table headers and values for given table."""
        if table not in headers or table not in self.target_space.tables:
            raise ValueError("{0} is an invalid table name. Valid inputs are " \
                    "'classifier_{features,classifications} or data stream " \
                    "name.".format(table))
        elif self.indices.get(table) != None:
            return dict(zip(headers[table],
                            self.target_space.tables[table][self.indices[table]]))

    def get_entry_value(self, table, key):
        """Returns specific value from Target.get_entry() to avoid None issues."""
        entry = self.get_entry(table)
        if entry != None and key in entry:
            return entry.get(key)

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
            new_entry = self.target_space.combine_entries(table, indices)
            self.target_space.tables[table][location] = new_entry

    def get_classifier_features(self):
        """Uses Target's data stream entries to update classifier tables."""
        if self.indices.get('classifier') == None:
            index = len(self.target_space.tables['classifier_features'])
            self.indices['classifier'] = index
        else:
            index = self.indices['classifier']
        nims_entry = self.get_entry('nims')
        adcp_entry = self.get_entry('adcp')
        return [nims_entry['size_sq_m'],  # size
                nims_entry['speed_mps'],  # speed
                0,  # deltav
                nims_entry['target_strength'],  # target_strength
                _get_minutes_since_midnight(nims_entry['timestamp']),  # time_of_day
                adcp_entry['speed']]  # current

class TargetSpace:
    """"""
    def __init__(self, data_streams=config.data_streams):
        self.targets = []
        self.tables = {}
        for stream in data_streams:
            self.tables[stream] = []
        self.tables['classifier_features'] = []
        self.tables['classifier_classifications'] = []
        self.classifier_index_to_target = {}

    def get_entry_by_index(self, table, index):
        """Returns dictionary of table headers and values for given index."""
        if table not in headers or table not in self.tables:
            raise ValueError("{0} is an invalid table name. Valid inputs are " \
                    "'classifier_{features,classifications}' or data stream " \
                    "name.".format(table))
        elif index < 0 or index >= len(self.tables[table]):
            raise ValueError("Invalid table index {0}. {1} table is of length" \
                    " {2}.".format(index, table, len(self.tables[table])))
        else:
            return dict(zip(headers[table], self.tables[table][index]))

    def get_entry_value_by_index(self, table, index, key):
        """Returns value for specific key in table entry."""
        entry = self.get_entry_by_index(table, index)
        if entry != None and key in entry:
            return entry.get(key)

    def combine_entries(self, table, indices):
        """Expects indices to be in order of read. That is, last
        entry is the latest in the list.
        """
        combined_entry = []
        for column_index, column_name in enumerate(headers[table]):
            values = []
            for index in indices:
                values.append(self.tables[table][index][column_index])

            if column_name in ['first_ping', 'min_angle_m', 'min_range_m']:
                combined_entry.append(min(values))
            elif column_name in ['timestamp', 'pings_visible', 'max_angle_m', 'max_range_m']:
                combined_entry.append(max(values))
            elif column_name in ['id']:
                if len(set(values)) > 1:
                    raise ValueError("Internal errror. All ids " \
                            "in combine_entries are expected to match.")
                combined_entry.append(values[0])
            elif column_name in ['target_strength', 'width', 'height',
                                 'size_sq_m', 'speed_mps']:
                combined_entry.append(sum(values) / float(len(values)))
            elif column_name in ['last_pos_angle', 'last_pos_range']:
                combined_entry.append(values[len(values) - 1])
            elif column_name == 'aggregate_indices':
                combined_entry.append(indices)
        return combined_entry

    def update_classifier_tables(self, target):
        """Permanently store recently classified features and classifications."""
        # WARNING: get_classifier_features() recalculates the features based on
        #   the current table entries. It could (but shouldn't) be that a target
        #   is classified, more target data arrives, but the target was never
        #   reclassified before old targets are removed. This means that we'd
        #   store updated features but with an old classification.
        #   A potential solution may be to store the number of pings used to
        #   create classification features from agg_indices.
        self.tables['classifier_features'].append(target.get_classifier_features)
        self.tables['classifier_classifications'].append(target.classification)
        target.indices['classifier'] = len(self.tables['classifier_features']) - 1

    def update(self, target):
        """
        remove old targets from target space
        """
        self.remove_old_nims(target)
        self.remove_old_pamguard(target)
        self.remove_old_adcp()

    def remove_old_nims(self, target):
        """
        Remove nims data older than drop_target_time. Update minimum
        time of all targets (to avoid dropping relevant ADCP data)
        """
        # remove all targets with nims that have not been seen
        # for drop_target_time seconds
        indices = target.get_entry_value('nims', 'aggregate_indices')
        indices.append(target.indices['nims'])

        for index in sorted(indices, reverse = True):
            self.tables['nims'][index] = []
            target.indices.pop('nims')

    def remove_old_pamguard(self, target):
        """
        Remove pamguard data older than drop_target_time. Update minimum
        time of all targets (to avoid dropping relevant ADCP data)
        """
        if target.get_entry('pamguard') != None:
            if self.delta_t_in_seconds(datetime.now(),
                    target.get_entry_value('pamguard', 'timestamp') >= config.drop_target_time:
                self.tables['pamguard'][target.indices['pamguard']] = []

    def remove_old_adcp(self):
        """
        remove all adcp data except for the most recent entry
        """
        self.tables['adcp'] = [self.tables['adcp'][-1]]

    # this function is already in code...import?
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
