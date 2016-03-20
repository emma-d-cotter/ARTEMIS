from datetime import datetime
import math
import config
        {
            "first_detect",
            "height",
            "id",
            "last_pos_bearing",
            "last_pos_elevation": 0.0,
            "last_pos_range": 5.508647918701172,
            "last_vel_bearing": Infinity,
            "last_vel_elevation": NaN,
            "last_vel_range": -Infinity,
            "length": 0.1428571492433548,
            "max_bearing_deg": 1338.540771484375,
            "max_elevation_deg": 0.0,
            "max_range_m": 5.538654327392578,
            "min_bearing_deg": 1000.0,
            "min_elevation_deg": 0.0,
            "min_range_m": 2.09869122505188,
            "pings_visible": 10,
            "size_sq_m": 0.8089292645454407,
            "speed_mps": 0.0,
            "target_strength": 0.0,
            "width": 4.687503814697266
        }

headers = {}
headers['adcp'] = ['timestamp', 'speed', 'heading']
headers['pamguard'] = ['timestamp', 'detection']
# TODO: need to update nims headers to match real nims (and update simulator)
headers['nims'] = ['timestamp', 'id', 'pings_visible', 'first_ping',
        'target_strength', 'width', 'height', 'size_sq_m', 'speed_mps',
        'min_angle_m', 'min_range_m', 'max_angle_m', 'max_range_m',
        'last_pos_bearing', 'last_pos_range', 'aggregate_indices']
headers['classifier'] = config.classifier_features

def _get_minutes_since_midnight(timestamp):
    """"""
    return min(timestamp.hour*60 + timestamp.minute,
        60*24 - (timestamp.hour*60 + timestamp.minute))

class Target:
    """"""
    def __init__(self, target_space, source="Unknown", firstseen=datetime.utcnow(),
                 lastseen=datetime.utcnow(), classification=None, indices={}):
        self.target_space = target_space
        self.source = source
        self.firstseen = firstseen
        self.lastseen = lastseen
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
            old_entry_index = self.indices[table]
            old_aggs = self.target_space.tables[table][old_entry_index][-1]
            assert(old_aggs != None)
            indices.extend(old_aggs)
            new_entry = self.target_space.combine_entries(table, indices)
            self.target_space.tables[table][old_entry_index] = new_entry

    def get_classifier_features(self):
        """Uses Target's data stream entries to update classifier tables."""
        return [self.get_entry_value('nims', 'size_sq_m'),  # size
                self.get_entry_value('nims', 'speed_mps'),  # speed
                self.calculate_deltav(),  # deltav
                self.get_entry_value('nims','target_strength'),  # target_strength
                _get_minutes_since_midnight(self.get_entry_value('nims','timestamp')),  # time_of_day
                self.get_entry_value('adcp', 'speed')]  # current

    def calculate_deltav(self):
        """
        Calculates "delta_v" for classification given a target.

        Delta_v is the norm of the difference between the current velocity
        and the target velocity. This function returns the maximum delta_v
        calculated for the target. Target velocity is calculated at intervals
        of M3_averaging_time

        i.e. if M3_averaging_time is 1 second, and a target was detected every
        ping at 10 Hz for 5 seconds, the velocity would be calculated 5 times.

        The most recent ADCP data at the time of target detection is used to
        calculate delta_v.
        """
        # extract target data
        nims_indices = self.get_entry('nims')['aggregate_indices']
        if len(nims_indices) > 1:
            print("calculating deltav for: ", nims_indices)
            adcp = self.get_entry('adcp')

            # sort nims data by timestamp
            #nims_indices = sorted(nims_indices,
            #       key = lambda x: self.target_space.get_entry_by_index('nims', x)['timestamp'])

            # extract all targets from nims data
            targets = self.extract_targets(nims_indices)

            points_to_avg = [targets[0]]
            index = 0
            # determine points between which to calculate velocity (must have at least
            # M3_averaging_time between the timestamps)
            start_time = targets[index]['timestamp']
            for i, target in enumerate(targets):
                # add to points_to_avg if the difference in time between
                # target sightings is greater than the M3_averaging_time
                diff = self.delta_t_in_seconds(target['timestamp'], start_time)

                if diff >= config.M3_avgeraging_time:
                    points_to_avg.append(targets[i])
                    index = i
                    start_time = targets[index]['timestamp']

                if i >= (len(targets)-1):
                    points_to_avg.append(targets[i])
                    index = i

            delta_v = self.calc_delta_v(points_to_avg, adcp)
            return max(delta_v)
        else:
            # should calculate first ping using NIMS velocity
            return 0

    def velocity_between_two_points(self, point1, point2):
        """
        Determines magnitude and direction of target trajectory (from point 1 to point 2)

        Inputs:
        point 1, point 2 = points where target was detected, in list format [range, bearing in degrees]
        AMP_heading = heading of AMP, in radians from due north
        M3_swath = list containing minimum and maximum angle ( in degrees) for M3 target
                   detection. Default is 0 --> 120 degrees

        Outputs:
        vel = [velocity magnitude, velocity direction]
        """

        point1_cartesian = self.transform_NIMS_to_vector(point1)
        point2_cartesian = self.transform_NIMS_to_vector(point2)
        dt = self.delta_t_in_seconds(point1['timestamp'], point2['timestamp'])
        # subtract 2-1 to get velocity
        vel = [(point2_cartesian[0] - point1_cartesian[0])/dt,
               (point2_cartesian[1] - point1_cartesian[1])/dt]

        return(vel)


    def transform_NIMS_to_vector(self, point):
        """
        Transform NIMS detection (in format [range, bearing in degrees]) to earth coordinates (East-North)

        Returns X-Y coordinates of point after transformation.
        """
        # convert target heading to radians, and shift such that zero degrees is center of swath
        point_heading = (point['last_pos_bearing'] - (config.M3_swath[1] - config.M3_swath[0])/2) * math.pi/180

        # convert bearing to angle from due N by subtracting AMP angle
        point_heading = point_heading - config.AMP_heading

        # get vector components for point 1 and 2
        point_cartesian = [point['last_pos_range'] * math.cos(point_heading),
                           point['last_pos_range'] * math.sin(point_heading)]

        return(point_cartesian)


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


    def extract_targets(self, nims_indices):
        """
        Extract all targets from nims data
        """

        targets = []
        for index in nims_indices:
            targets.append(self.target_space.get_entry_by_index('nims', index))

        return targets

    def calc_delta_v(self, points_to_avg, adcp):
        """
        returns delta v between all selected points and ADCP
        """
        # convert ADCP to cartesian coordinates
        velocity_adcp = [adcp['speed'] * math.cos(adcp['heading']),
                         adcp['speed'] * math.sin(adcp['heading'])]

        delta_v = []
        for i, target in enumerate(points_to_avg):

            # calculate delta_v between two consecutive points
            point1 = points_to_avg[i]

            try:
                point2 = points_to_avg[i+1]
            except:
                break

            # velocity of target between point 1 and point 2
            velocity_target = self.velocity_between_two_points(point1, point2)
            # difference between target and adcp velocity
            velocity_diff = [velocity_target[0]-velocity_adcp[0],
                             velocity_target[1]-velocity_adcp[1]]
            # "delta_v" is magnitude of velocity difference
            delta_v.append((velocity_diff[0]**2 + velocity_diff[1]**2)**0.5)

            return(delta_v)


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

    def append_entry(self, table, data):
        for i, entry in enumerate(self.tables[table]):
            if entry == []:
                self.tables[table][i] = data
                return i
        else:
            self.tables[table].append(data)
            return len(self.tables[table]) - 1

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
            elif column_name in ['last_pos_bearing', 'last_pos_range']:
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
        self.tables['classifier_features'].append(target.get_classifier_features())
        self.tables['classifier_classifications'].append(target.classification)
        index = len(self.tables['classifier_features']) - 1
        target.indices['classifier'] = index
        self.classifier_index_to_target[index] = target

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
            if self.delta_t_in_seconds(datetime.now(), target.get_entry_value('pamguard', 'timestamp')) >= config.drop_target_time:
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
