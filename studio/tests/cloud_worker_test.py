import unittest
import os

from studio.cloud_worker import GCloudWorkerManager
from local_worker_test import stubtest_worker


@unittest.skipIf(
    'GOOGLE_APPLICATION_CREDENTIALS' not in os.environ.keys(),
    'GOOGLE_APPLICATION_CREDENTIALS environment ' +
    'variable not set, won'' be able to use google cloud')
class GCloudWorkerTest(unittest.TestCase):
    def get_worker_manager(self):
        project = 'studio-ed756'
        return GCloudWorkerManager(project)

    def test_worker(self):

        stubtest_worker(
            self,
            experiment_name='test_cloud_worker',
            runner_args=['--cloud=gcloud'],
            config_name='test_config.yaml',
            test_script='tf_hello_world.py',
            script_args=['arg0'],
            expected_output='[ 2.  6.]',
        )


if __name__ == '__main__':
    unittest.main()