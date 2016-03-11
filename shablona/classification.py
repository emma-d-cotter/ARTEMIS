import numpy as np
from scipy import stats
import os.path
import csv
from datetime import datetime
import pprint

from sklearn.base import ClassifierMixin
from sklearn.neighbors.base import NeighborsBase, RadiusNeighborsMixin, \
        SupervisedIntegerMixin
from sklearn.utils import check_array
from sklearn.utils.extmath import weighted_mode

import config


def _within_interval(x, interval):
    """Utility function returns boolean if in interval (inclusive, both sides)."""
    if len(interval) == 2:
        return interval[0] <= x and x <= interval[1]
    else:
        raise ValueError("Invalid interval parameter '{0}'. Expected to be tuple "
                "or list of length 2.".format(interval))

def _scale_axis(value, axis_name, axis_bounds=config.classifier_axis_bounds):
    """Retrieves classifier axis bounds and scales value accordingly."""
    try:
        min_bound = axis_bounds[axis_name][0]
        max_bound = axis_bounds[axis_name][1]
    except KeyError:
        raise ValueError("Unable to scale axis {0}.".format(axis_name))
    return (value - min_bound) / (max_bound - min_bound)

def classification_weights(neigh_dist, neigh_ind, target_space):
    """
    Returns desired weights for targets in a given target space.

    For each neighbor, the weight is a function of distance and data source:
    weight = 1/distance * source_weight

    source_weight is determined based on the physical site of a target (current
    site, or a previous deployment) and whether the target has been manually
    reviewed.
    """

    weights = []
    # determine weight for each neighbor
    for i, ind in enumerate(neigh_ind):
        target = target_space.classifier_index_to_target[ind]
        source = target.source

        # using source, determine source_weight. If source is not formatted
        # correctly, assign weight of 1
        if source.startswith(config.site_name):
            if source.endswith('manual'):
                source_weight = 1
            elif source.endswith('auto'):
                source_weight = 0.9
        else:
            if source.endswith('manual'):
                source_weight = 0.9
            elif source.endswith('auto'):
                source_weight = 0.8
            else:
                source_weight = 1

        distance = neigh_dist[i]

        weights += (1/distance) * source_weight

    return np.array(weights)

class BackgroundClassifier():
    """Classifier implementing priority-based background hyperspace rules to be
    used when the radius neighbors classifier finds no neighbors in loaded data.

    Parameters
    ----------
    hyperspaces : list of dicts, optional
        Defines hyperspaces (rules) for which a classification is assumed, list
          in order of descending priority. Each feature defined in hyperspaces
          must be defined everywhere between negative infinity and infinity.
          Must also be defined for at least one feature and have valid
          classification for each rule/hyperspace. Pulled from
          config.background_hyperspaces object if blank.
    features : list, optional
        list of features to be used in classifier. Pulled from
          config.classifier_features if blank.
    classifications : dict, optional
        dict of classifications, with keys integer and values string. Pulled from
          config.classifications if blank.
    """
    def __init__(self,
                 hyperspaces=config.background_hyperspaces,
                 features=config.classifier_features,
                 classifications=config.classifications):
        self.hyperspaces = hyperspaces
        self.features = features
        self.classifications = classifications

    def _check_background_coverage(self, hyperspaces, features, classifications):
        """Checks that every feature defined in the background hyperspace
        used for outliers are defined everywhere between negative infinity
        and infinity. Also checks that background defined on at least one
        feature, classification is defined for each rule, and each classification
        is a valid classification.

        Throws ValueError if hyperspace fails, returns hyperspace otherwise.

        Parameters
        ----------
        hyperspaces : list of dicts
            List of rules, where each rule is a dictionary with classifier
            features as keys and a tuple (min, max) as the value.
        """
        for rule in hyperspaces:
            if 'classification' not in rule:
                raise ValueError("Invalid background hyperspace. There exists a " \
                        "rule without a classification key.")
            if (rule['classification'] not in classifications or
                    rule['classification'] not in classifications.values()):
                raise ValueError("Invalid classification {0} in background " \
                        "hyperspace. Valid classifications are: {1} or {2}".format(
                        rule['classification'], list(classifications.keys()),
                        list(classifications.values())))

        num_features_with_full_background = 0
        for feature in features:
            ranges = set()
            for rule in hyperspaces:
                if rule.get(feature) == None: continue  # skips features undefined in rule
                rule_min = rule[feature][0]
                rule_max = rule[feature][1]
                for rng in ranges:
                    #    *----*         original range (rng)
                    #  |--------|       rule engulfs orig range
                    if rule_min <= rng[0] and rng[1] <= rule_max:
                        rng[0] = rule_min
                        rng[1] = rule_max
                    #    *----*         original range (rng)
                    #  |---|            rule overlaps, but to minimum side
                    elif rule_min <= rng[0]:
                        rng[0] = rule_min
                    #    *----*         original range (rng)
                    #        |---|      rule overlaps, but to maximum side
                    elif rng[1] <= rule_max:
                        rng[1] = rule_max
                    #    *----*         original range (rng)
                    #      |-|          original range engulfs rule
                    elif rng[0] <= rule_min and rule_max <= rng[1]:
                        pass
                    #    *----*         original range (rng)
                    # |-|               rule completely outside of orig range
                    else:
                        ranges.add( (rule_min,rule_max) )
            if len(ranges) > 1:
                raise ValueError("Defined background hyperspaces fail to span all \
                    of {0} feature. Ranges covered: {1}".format(feature, ranges))
            num_features_with_full_background += 1
        if num_features_with_full_background == 0:
            raise ValueError("Defined background hyperspaces fail to cover any of \
                    the classifier features, meaning outliers could go unclassified.")

        return hyperspaces

    def fit(self, hyperspaces):
        """Fits background classifier after checking validity of defined hyperspace."""
        self.hyperspaces = self._check_background_coverage(hyperspaces, self.features,
                self.classifications)

    def predict(self, X):
        """Predict the class labels for the provided data
        Parameters
        ----------
        X : array-like, shape (n_query, n_features)
            Test samples.
        Returns
        -------
        y : array of shape [n_samples]
            Class labels for each data sample, along with classification info
        """
        for rule in self.hyperspaces:
            for i, feature in enumerate(self.classifier_features):
                if feature in rule and not _within_interval(X[i], rule[feature]):
                    break
            else:
                # Success, none of the features in rule fail
                return rule.get('classification')
        # Failure for all rules, should be caught by _check_background_coverage
        raise ValueError("No background classification could be found for \
                {0}.".format(X))

class RadiusNeighborsClassifier(NeighborsBase, RadiusNeighborsMixin,
                                SupervisedIntegerMixin, ClassifierMixin):
    """Classifier implementing a vote among neighbors within a given radius

    Extension of scikit-learn's RadiusNeighborsClassifier that
    predicts using a weight function based on index in addition to distance.
    This allows more general weighting schemes. Remaining parameters
    identical to that of scikit-learn.

    Parameters
    ----------
    weights : callable
        a user-defined function that returns an array of the same shape
          containing the weights to use. Should accept three parameters:
        - dist, an array containing distances of neighbors
        - ind, an array containing indices of neighbors
        - target_space, TargetSpace instance that maps ind to other target info
    target_space : TargetSpace object, optional (default = None)
        a TargetSpace instance that contains map from index to other
          characteristics (source, datetime of collection) to be used in weight.
    radius : float, optional (default = 1.0)
        Range of parameter space to use by default for :meth`radius_neighbors`
        queries.
    algorithm : {'auto', 'ball_tree', 'kd_tree', 'brute'}, optional
        Algorithm used to compute the nearest neighbors:
        - 'ball_tree' will use :class:`BallTree`
        - 'kd_tree' will use :class:`KDtree`
        - 'brute' will use a brute-force search.
        - 'auto' will attempt to decide the most appropriate algorithm
          based on the values passed to :meth:`fit` method.
        Note: fitting on sparse input will override the setting of
        this parameter, using brute force.
    leaf_size : int, optional (default = 30)
        Leaf size passed to BallTree or KDTree.  This can affect the
        speed of the construction and query, as well as the memory
        required to store the tree.  The optimal value depends on the
        nature of the problem.
    metric : string or DistanceMetric object (default='minkowski')
        the distance metric to use for the tree.  The default metric is
        minkowski, and with p=2 is equivalent to the standard Euclidean
        metric. See the documentation of the DistanceMetric class for a
        list of available metrics.
    p : integer, optional (default = 2)
        Power parameter for the Minkowski metric. When p = 1, this is
        equivalent to using manhattan_distance (l1), and euclidean_distance
        (l2) for p = 2. For arbitrary p, minkowski_distance (l_p) is used.
    outliers: callable, optional (default = None)
        a user-defined function that returns an array of the same shape
          containing the fallback save settings to use. Similar to weights.
        If set to None, ValueError is raised, when outlier is detected.
        Should accept three parameters:
        - dist, an array containing distances of neighbors
        - ind, an array containing indices of neighbors
        - target_space, TargetSpace instance that maps ind to other target info
    metric_params : dict, optional (default = None)
        Additional keyword arguments for the metric function.

    Notes
    -----
    See :ref:`Nearest Neighbors <neighbors>` in the online documentation
    for a discussion of the choice of ``algorithm`` and ``leaf_size``.
    http://en.wikipedia.org/wiki/K-nearest_neighbor_algorithm
    """

    def __init__(self, weights, target_space, radius=1.0,
                 algorithm='auto', leaf_size=30, p=2, metric='minkowski',
                 outliers=None, metric_params=None, **kwargs):
        self._init_params(radius=radius,
                          algorithm=algorithm,
                          leaf_size=leaf_size,
                          metric=metric, p=p, metric_params=metric_params,
                          **kwargs)
        self.outlier_function = outliers
        self.weight_function = weights
        self.target_space = target_space

    def predict(self, X):
        """Predict the class labels for the provided data
        Parameters
        ----------
        X : array-like, shape (n_query, n_features), \
                or (n_query, n_indexed) if metric == 'precomputed'
            Test samples.
        Returns
        -------
        y : array of shape [n_samples]
            Class labels for each data sample.
        """
        X = check_array(X, accept_sparse='csr')
        n_samples = X.shape[0]

        neigh_dist, neigh_ind = self.radius_neighbors(X)
        inliers = [i for i, nind in enumerate(neigh_ind) if len(nind) != 0]
        outliers = [i for i, nind in enumerate(neigh_ind) if len(nind) == 0]

        classes_ = self.classes_
        _y = self._y
        if not self.outputs_2d_:
            _y = self._y.reshape((-1, 1))
            classes_ = [self.classes_]
        n_outputs = len(classes_)

        if self.outlier_function is not None:
            neigh_dist[outliers] = 1e-6
        elif outliers:
            raise ValueError('No neighbors found for test samples %r, '
                             'you can try using larger radius, '
                             'give a label for outliers, '
                             'or consider removing them from your dataset.'
                             % outliers)

        weights = self.weight_function(neigh_dist=neigh_dist, neigh_ind=neigh_ind,
                               target_space=self.target_space)

        y_pred = np.empty((n_samples, n_outputs), dtype=classes_[0].dtype)
        for k, classes_k in enumerate(classes_):
            pred_labels = np.array([_y[ind, k] for ind in neigh_ind],
                                   dtype=object)
            if weights is None:
                mode = np.array([stats.mode(pl)[0]
                                 for pl in pred_labels[inliers]], dtype=np.int)
            else:
                mode = np.array([weighted_mode(pl, w)[0]
                                 for (pl, w)
                                 in zip(pred_labels[inliers], weights)],
                                dtype=np.int)

            mode = mode.ravel()

            y_pred[inliers, k] = classes_k.take(mode)

        if outliers:
            for outlier in outliers:
                y_pred[outlier, 0] = self.outlier_function.predict(X[outlier])

        if not self.outputs_2d_:
            y_pred = y_pred.ravel()

        return y_pred

    def refit(self):
        classifier.fit(self.target_space.tables['classifier_features'],
                       self.target_space.tables['classifier_classifications'])
