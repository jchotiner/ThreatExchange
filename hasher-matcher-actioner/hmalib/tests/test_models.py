# Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved

import unittest
from moto import mock_dynamodb2
from hmalib import models
import boto3
import datetime
import os


class TestPDQModels(unittest.TestCase):
    table = None
    TEST_CONTENT_ID = "image/test_photo.jpg"
    TEST_SIGNAL_ID = "5555555555555555"
    TEST_SIGNAL_SOURCE = "test_source"

    @staticmethod
    def mock_aws_credentials():
        """
        Mocked AWS Credentials for moto.
        (likely not needed based on local testing but just incase)
        """
        os.environ["AWS_ACCESS_KEY_ID"] = "testing"
        os.environ["AWS_SECRET_ACCESS_KEY"] = "testing"
        os.environ["AWS_SECURITY_TOKEN"] = "testing"
        os.environ["AWS_SESSION_TOKEN"] = "testing"

    @classmethod
    def setUpClass(cls):
        cls.mock_aws_credentials()
        cls.mock_dynamodb2 = mock_dynamodb2()
        cls.mock_dynamodb2.start()
        cls.create_mocked_table()

    @classmethod
    def tearDownClass(cls):
        cls.mock_dynamodb2.stop()

    @classmethod
    def create_mocked_table(cls):
        dynamodb = boto3.resource("dynamodb", region_name="us-east-1")
        table_name = "test-table"
        cls.table = dynamodb.create_table(
            AttributeDefinitions=[
                {"AttributeName": "PK", "AttributeType": "S"},
                {"AttributeName": "SK", "AttributeType": "S"},
                {"AttributeName": "GSI1-PK", "AttributeType": "S"},
                {"AttributeName": "GSI1-SK", "AttributeType": "S"},
                {"AttributeName": "GSI2-PK", "AttributeType": "S"},
                {"AttributeName": "UpdatedAt", "AttributeType": "S"},
            ],
            TableName=table_name,
            BillingMode="PAY_PER_REQUEST",
            KeySchema=[
                {"AttributeName": "PK", "KeyType": "HASH"},
                {"AttributeName": "SK", "KeyType": "RANGE"},
            ],
            GlobalSecondaryIndexes=[
                {
                    "IndexName": "GSI-1",
                    "KeySchema": [
                        {"AttributeName": "GSI1-PK", "KeyType": "HASH"},
                        {"AttributeName": "GSI1-SK", "KeyType": "RANGE"},
                    ],
                    "Projection": {
                        "ProjectionType": "INCLUDE",
                        "NonKeyAttributes": [
                            "ContentHash",
                            "UpdatedAt",
                            "SignalHash",
                            "SignalSource",
                            "HashType",
                        ],
                    },
                },
                {
                    "IndexName": "GSI-2",
                    "KeySchema": [
                        {"AttributeName": "GSI2-PK", "KeyType": "HASH"},
                        {"AttributeName": "UpdatedAt", "KeyType": "RANGE"},
                    ],
                    "Projection": {
                        "ProjectionType": "INCLUDE",
                        "NonKeyAttributes": [
                            "ContentHash",
                            "SignalHash",
                            "SignalSource",
                            "HashType",
                        ],
                    },
                },
            ],
        )

    @staticmethod
    def get_example_pdq_hash_record():
        return models.PipelinePDQHashRecord(
            TestPDQModels.TEST_CONTENT_ID,
            "f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0",
            datetime.datetime.now(),
            100,
        )

    @staticmethod
    def get_example_pdq_match_record():
        pdq_hash = "f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0"
        signal_hash = "f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f1"
        return models.PDQMatchRecord(
            TestPDQModels.TEST_CONTENT_ID,
            pdq_hash,
            datetime.datetime.now(),
            TestPDQModels.TEST_SIGNAL_ID,
            TestPDQModels.TEST_SIGNAL_SOURCE,
            signal_hash,
        )

    def test_write_hash_record(self):
        """
        Test PipelinePDQHashRecord write table with hardcode query
        """
        record = self.get_example_pdq_hash_record()

        record.write_to_table(self.table)

        result = self.table.get_item(
            Key={"PK": f"c#{TestPDQModels.TEST_CONTENT_ID}", "SK": "type#pdq"}
        )
        items = result.get("Item")
        content_hash = items.get("ContentHash")
        assert record.content_hash == content_hash

    def test_query_hash_record(self):
        """
        Test PipelinePDQHashRecord write table with get_from_content_key query
        """

        record = self.get_example_pdq_hash_record()
        record.write_to_table(self.table)

        query_record = models.PipelinePDQHashRecord.get_from_content_id(
            self.table, TestPDQModels.TEST_CONTENT_ID
        )

        assert record == query_record

    def test_write_match_record(self):
        """
        Test PDQMatchRecord write table with hardcode query
        """

        record = self.get_example_pdq_match_record()

        record.write_to_table(self.table)

        result = self.table.get_item(
            Key={
                "PK": f"c#{TestPDQModels.TEST_CONTENT_ID}",
                "SK": f"s#{TestPDQModels.TEST_SIGNAL_SOURCE}#{TestPDQModels.TEST_SIGNAL_ID}",
            },
        )
        items = result.get("Item")
        query_hash = items.get("SignalHash")
        assert record.signal_hash == query_hash

    def test_query_match_record_by_content_id(self):
        """
        Test PDQMatchRecord write table with get_from_content_key query
        """

        record = self.get_example_pdq_match_record()

        record.write_to_table(self.table)

        query_record = models.PDQMatchRecord.get_from_content_id(
            self.table, TestPDQModels.TEST_CONTENT_ID
        )[0]

        assert record == query_record

    def test_query_match_record_by_signal_id(self):
        """
        Test PDQMatchRecord write table with get_from_content_key query
        """

        record = self.get_example_pdq_match_record()

        record.write_to_table(self.table)

        query_record = models.PDQMatchRecord.get_from_signal(
            self.table, TestPDQModels.TEST_SIGNAL_ID, TestPDQModels.TEST_SIGNAL_SOURCE
        )[0]

        assert record == query_record

    def test_query_match_record_by_time(self):
        """
        Test PDQMatchRecord write table with get_from_content_key query
        """

        record = self.get_example_pdq_match_record()

        record.write_to_table(self.table)

        query_record = models.PDQMatchRecord.get_from_time_range(self.table)[0]

        assert record == query_record
