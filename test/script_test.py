import unittest
import os
import boto3
import logging
from scripttest import TestFileEnvironment


class TestSsmStarter(unittest.TestCase):
    def setUp(self):
        # silence boto debug output to make output more readable
        logging.getLogger('boto').setLevel(logging.ERROR)
        logging.getLogger('botocore').setLevel(logging.ERROR)

        ssm = boto3.client('ssm')
        ssm.put_parameter(
            Name='/dev/ssm_starter_test_app/TEST_STRING1',
            Value='This is the value of test string 1',
            Type='String',
            Overwrite=True
        )
        ssm.put_parameter(
            Name='/dev/ssm_starter_test_app/TEST_STRING2',
            Value='This is the value of test string 2',
            Type='String',
            Overwrite=True
        )
        ssm.put_parameter(
            Name='/dev/ssm_starter_test_app/TEST_SECURE1',
            Value='Some secret',
            Type='SecureString',
            Overwrite=True
        )
        ssm.put_parameter(
            Name='/dev/ssm_starter_test_global/TEST_STRING2',
            Value='This may conflict with another String 1',
            Type='String',
            Overwrite=True
        )
        ssm.put_parameter(
            Name='/dev/ssm_starter_test_global_distinct/TEST_DISTINCT1',
            Value='This should not conflict with anything',
            Type='String',
            Overwrite=True
        )

    def tearDown(self):
        pass

#
# Tests
#

    def test_all_missing_args_yield_errcode(self):
        command = [
            'ssm-starter'
        ]
        env = TestFileEnvironment('./test-output')
        result = env.run(' '.join(command), expect_error=True)
        assert not result.returncode == 0


    def test_missing_command_arg_yield_errcode(self):
        command = [
            'ssm-starter',
            '--ssm-name /dev/ssm_starter_test_app',
        ]
        env = TestFileEnvironment('./test-output')
        result = env.run(' '.join(command), expect_error=True)
        assert not result.returncode == 0


    def test_missing_ssmname_arg_yield_errcode(self):
        command = [
            'ssm-starter',
            '--command "echo"',
        ]
        env = TestFileEnvironment('./test-output')
        result = env.run(' '.join(command), expect_error=True)
        assert not result.returncode == 0


    def test_load_single_path(self):
        command = [
            'ssm-starter',
            '--ssm-name /dev/ssm_starter_test_app',
            '--command "env | grep TEST"'
        ]
        os.environ['AWS_ENV'] = ''
        env = TestFileEnvironment('./test-output')
        result = env.run(' '.join(command))
        assert 'TEST_STRING1 - setting value from ssm' in result.stdout


    def test_load_multiple_paths_no_duplicates(self):
        command = [
            'ssm-starter',
            '--ssm-name /dev/ssm_starter_test_app',
            '--ssm-name /dev/ssm_starter_test_global_distinct',
            '--command "env | grep TEST"'
        ]
        os.environ['AWS_ENV'] = ''
        env = TestFileEnvironment('./test-output')
        result = env.run(' '.join(command))
        assert 'TEST_STRING2 - setting value from ssm: This is the value of test string 2' in result.stdout


    def test_load_multiple_paths_skip_duplicates(self):
        command = [
            'ssm-starter',
            '--ssm-name /dev/ssm_starter_test_app',
            '--ssm-name /dev/ssm_starter_test_global',
            '--command "env | grep TEST"'
        ]
        os.environ['AWS_ENV'] = ''
        env = TestFileEnvironment('./test-output')
        result = env.run(' '.join(command))
        assert 'TEST_STRING2 - setting value from ssm: This is the value of test string 2' in result.stdout


    def test_load_multiple_paths_abort_duplicates(self):
        command = [
            'ssm-starter',
            '--ssm-name /dev/ssm_starter_test_app',
            '--ssm-name /dev/ssm_starter_test_global',
            '--abort-if-duplicates',
            '--command "env | grep TEST"'
        ]
        os.environ['AWS_ENV'] = ''
        env = TestFileEnvironment('./test-output')
        result = env.run(' '.join(command), expect_error=True)
        assert not result.returncode == 0


    def test_load_multiple_paths_overwrite_duplicates(self):
        command = [
            'ssm-starter',
            '--ssm-name /dev/ssm_starter_test_app',
            '--ssm-name /dev/ssm_starter_test_global',
            '--overwrite-if-duplicates',
            '--command "env | grep TEST"'
        ]
        os.environ['AWS_ENV'] = ''
        env = TestFileEnvironment('./test-output')
        result = env.run(' '.join(command))
        assert 'TEST_STRING2 - setting value from ssm: This may conflict with another String 1' in result.stdout


    def test_securestrings_kept_secret(self):
        command = [
            'ssm-starter',
            '--ssm-name /dev/ssm_starter_test_app',
            '--command "env | grep TEST"'
        ]
        os.environ['AWS_ENV'] = ''
        env = TestFileEnvironment('./test-output')
        result = env.run(' '.join(command))
        assert 'TEST_SECURE1 - setting value from ssm (SecureString, 11 chars)' in result.stdout


    def test_with_awsenv_set(self):
        command = [
            'ssm-starter',
            '--ssm-name ssm_starter_test_app',
            '--command "env | grep TEST"'
        ]
        os.environ['AWS_ENV'] = 'dev'
        env = TestFileEnvironment('./test-output')
        result = env.run(' '.join(command))
        assert 'TEST_STRING1 - setting value from ssm' in result.stdout


    def test_with_awsenv_set(self):
        command = [
            'ssm-starter',
            '--ssm-name ssm_starter_test_app',
            '--command "env | grep TEST"'
        ]
        os.environ['AWS_ENV'] = 'dev'
        env = TestFileEnvironment('./test-output')
        result = env.run(' '.join(command))
        assert 'TEST_STRING1 - setting value from ssm' in result.stdout


    def test_invalid_ssm_name(self):
        command = [
            'ssm-starter',
            '--ssm-name ssm_starter_test_app',
            '--command "echo"'
        ]
        os.environ['AWS_ENV'] = ''
        env = TestFileEnvironment('./test-output')
        result = env.run(' '.join(command), expect_error=True)
        assert not result.returncode == 0


    def test_invalid_conflicting_ssm_name(self):
        command = [
            'ssm-starter',
            '--ssm-name /dev/ssm_starter_test_app',
            '--command "echo"'
        ]
        os.environ['AWS_ENV'] = 'dev'
        env = TestFileEnvironment('./test-output')
        result = env.run(' '.join(command), expect_error=True)
        assert not result.returncode == 0

