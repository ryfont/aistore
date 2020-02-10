# coding: utf-8

"""
    AIS

    AIStore is a scalable object-storage based caching system with Amazon and Google Cloud backends.  # noqa: E501

    OpenAPI spec version: 1.1.0
    Contact: dfcdev@exchange.nvidia.com
    Generated by: https://openapi-generator.tech
"""


from __future__ import absolute_import

import unittest
import shutil
import tarfile, io, os
import json
from .helpers import bytestring, surpressResourceWarning

import ais_client
from ais_client.api.sort_api import SortApi  # noqa: E501
from ais_client.rest import ApiException

class TestSortApi(unittest.TestCase):
    """SortApi unit test stubs"""

    BUCKET_NAME = "python-client-test"
    SHARDS = 100
    PREFIX = "input-"

    def setUp(self):
        surpressResourceWarning()

        configuration = ais_client.Configuration()
        configuration.debug = False
        api_client = ais_client.ApiClient(configuration)

        self.sort = ais_client.api.sort_api.SortApi(api_client)
        self.bucket = ais_client.api.bucket_api.BucketApi(api_client)
        self.object = ais_client.api.object_api.ObjectApi(api_client)
        self.models = ais_client.models

        # Create local bucket
        input_params = self.models.InputParameters(self.models.Actions.CREATELB)
        self.bucket.perform_operation(self.BUCKET_NAME, input_params)

        # Create and send tars
        for i in range(0, self.SHARDS):
            out = io.BytesIO()
            object_name = "%s%d.tar" % (self.PREFIX, i)
            with tarfile.open(mode="w", fileobj=out) as tar:
                for j in range(0, 100):
                    b = "Hello world!".encode("ascii")
                    t = tarfile.TarInfo("%d.txt" % j)
                    t.size = len(b)
                    tar.addfile(t, io.BytesIO(b))

            self.object.put(self.BUCKET_NAME, object_name, body=bytestring(out.getvalue()))

    def tearDown(self):
        # Delete bucket
        input_params = self.models.InputParameters(self.models.Actions.DESTROYLB)
        self.bucket.delete(self.BUCKET_NAME, input_params)

    def test_abort_sort(self):
        """Test case for abort_sort

        Abort distributed sort operation
        """

        output_prefix="output-"
        spec = self.models.SortSpec(
            bucket=self.BUCKET_NAME,
            provider="ais",
            extension=".tar",
            output_shard_size="1024",
            input_format=self.PREFIX+'{0..'+str(self.SHARDS-1)+'}',
            output_format=output_prefix+'{0000..10000}',
        )
        sort_uuid = self.sort.start_sort(spec)
        self.sort.abort_sort(sort_uuid)
        finished = False
        while not finished:
            finished = True
            metrics = self.sort.get_sort_metrics(sort_uuid)
            for target_metrics in metrics.values():
                target_finished = True
                for phase in ['local_extraction', 'meta_sorting', 'shard_creation']:
                    target_finished = target_finished and target_metrics[phase]['finished']

                if target_metrics['aborted']:
                    finished = True
                    break

                finished = finished and target_finished

        metrics = self.sort.get_sort_metrics(sort_uuid)
        for target_metrics in metrics.values():
            self.assertTrue(target_metrics['aborted'])

    def test_start_sort(self):
        """Test case for start_sort

        Starts distributed sort operation on cluster
        """

        output_prefix="output-"
        spec = self.models.SortSpec(
            bucket=self.BUCKET_NAME,
            provider="ais",
            extension=".tar",
            output_shard_size="1024",
            input_format=self.PREFIX+'{0..'+str(self.SHARDS-1)+'}',
            output_format=output_prefix+'{0000..10000}',
        )
        sort_uuid = self.sort.start_sort(spec)
        finished = False
        while not finished:
            finished = True
            metrics = self.sort.get_sort_metrics(sort_uuid)
            for target_metrics in metrics.values():
                target_finished = True
                for phase in ['local_extraction', 'meta_sorting', 'shard_creation']:
                    target_finished = target_finished and target_metrics[phase]['finished']

                if target_metrics['aborted']:
                    finished = True
                    break

                finished = finished and target_finished

        metrics = self.sort.get_sort_metrics(sort_uuid)
        for target_metrics in metrics.values():
            self.assertFalse(target_metrics['aborted'])

if __name__ == '__main__':
    unittest.main()
