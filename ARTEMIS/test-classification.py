import unittest
import classification as cl
import numpy as np

class testWeightedClassification(unittest.TestCase):
# test one - test load_detectedTargets
    def test_load_detectedTargets(self):
        nbrs = cl.weightedNeighbors(radius=3.0)

        result = nbrs.current_model_targets[0].features
        self.assertEqual(result,[1,2,3,4,5,6,7])

        result = nbrs.current_model_targets[3].features
        self.assertEqual(result,[7,6,5,4,3,2,1.4])

    def test_classification(self):
        nbrs = cl.weightedNeighbors(radius=4.0)
        nbrs.fitModel()

        classResult,indResult = nbrs.classify(np.array([1,2,3,4,5,6,7],ndmin=2))
        self.assertEqual(classResult,'1.1')
        self.assertTrue(all(np.isclose(indResult[0],np.array([0,2,6,7]))))

if __name__ == '__main__':
    unittest.main()
