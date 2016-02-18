import numpy as np
from scipy import stats
import os.path
import csv
from datetime import datetime

from sklearn.base import ClassifierMixin
from sklearn.neighbors.base import NeighborsBase, RadiusNeighborsMixin, \
        SupervisedIntegerMixin
from sklearn.utils import check_array
from sklearn.utils.extmath import weighted_mode

import .config as config


def _within_range(x, min, max):
    """"""
    return min <= x and x <= max

def _within_range(x, tuple):
    """"""
    return _within_range(x, tuple[0], tuple[1])

def _check_background_coverage(hyperspaces):
    """"""
    # TODO: Add comparison of classes to those defined in hyperspace
    num_features_with_full_background = 0
    for feature in config.classifier_features:
        ranges = set()
        for rule in config.background_hyperspaces:
            rule_min = rule[feature][0]
            rule_max = rule[feature][1]
            for rng in ranges:
                #    *----*         original range (rng)
                #  |--------|       rule engulfs orig range
                if rule_min <= rng[0] and rng[1] <= rule_max:
                if _within_range()
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

def _scale_axis(value, axis_name):
    """Retrieves classifier axis bounds and scales value accordingly."""
    try:
        min_bound = config.classifier_axis_bounds[axis_name][0]
        max_bound = config.classifier_axis_bounds[axis_name][1]
    except KeyError:
        raise ValueError("Unable to scale axis {0}.".format(axis_name))

    return (value - min_bound) / (max_bound - min_bound)

def classification_weights(neigh_dist, neigh_ind, target_space):
    """Returns desired weights for targets in a given target space."""
    for i, ind in enumerate(neigh_ind):
        target = target_space.classifier_index_to_target[ind]
        source = target.source
        distance = neigh_dist[i]
        time_since_seen = datetime.now() - target.time_of_day

    return np.ones(neigh_dist.shape)

class BackgroundClassifier():
    """"""
    def fit(self, hyperspaces=config.background_hyperspaces):
        """"""
        self.hyperspaces = _check_background_coverage(hyperspaces)

    def predict(self, X):
        """"""
        for rule in self.hyperspaces:
            for i, feature in enumerate(config.classifier_features):
                if feature in rule and not _within_range(X[i], rule[feature]):
                    break
            else:
                # Success, none of the features in rule fail
                return rule['classification']
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

    def __init__(self, radius=1.0, weights,
                 algorithm='auto', leaf_size=30, p=2, metric='minkowski',
                 outliers=None, metric_params=None, **kwargs):
        self._init_params(radius=radius,
                          algorithm=algorithm,
                          leaf_size=leaf_size,
                          metric=metric, p=p, metric_params=metric_params,
                          **kwargs)
        self.outlier_function = _check_outlier_coverage(outliers)
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
        y : array of shape [n_samples] or [n_samples, n_outputs]
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

        weights = self.weights(dist=neigh_dist, ind=neigh_ind,
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
            y_pred[outliers, :] = self.outlier_label

        if not self.outputs_2d_:
            y_pred = y_pred.ravel()

        return y_pred
