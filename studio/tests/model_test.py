import unittest
import uuid
import pip
import six
import os

from studio import model
from studio.auth import remove_all_keys
from studio.experiment import create_experiment



def get_test_experiment():
    filename = 'test.py'
    args = ['a', 'b', 'c']
    experiment_name = 'test_experiment_' + str(uuid.uuid4())
    experiment = create_experiment(filename, args, experiment_name)
    return experiment, experiment_name, filename, args



class ModelTest(unittest.TestCase):
    def test_create_experiment(self):
        _, experiment_name, filename, args = get_test_experiment()
        experiment_project = 'create_experiment_project'
        experiment = create_experiment(
            filename, args, experiment_name, experiment_project)
        packages = [
            p._key +
            '==' +
            p._version for p in pip.pip.get_installed_distributions(
                local_only=True)]

        self.assertTrue(experiment.key == experiment_name)
        self.assertTrue(experiment.filename == filename)
        self.assertTrue(experiment.args == args)
        self.assertTrue(experiment.project == experiment_project)
        self.assertTrue(experiment.pythonenv == packages)

    def test_get_config_env(self):
        value1 = str(uuid.uuid4())
        os.environ['TEST_VAR1'] = value1
        value2 = str(uuid.uuid4())
        os.environ['TEST_VAR2'] = value2

        config = model.get_config(
            os.path.join(os.path.dirname(os.path.realpath(__file__)),
                         'test_config_env.yaml'))
        self.assertEquals(config['test_key'], value1)
        self.assertEquals(config['test_section']['test_key'], value2)


if __name__ == "__main__":
    unittest.main()
