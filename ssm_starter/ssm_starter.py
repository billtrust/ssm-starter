# -*- coding: utf-8 -*-

from __future__ import print_function
import os
import sys
import argparse
import boto3

__version__ = "0.1.16"


def load_ssm_envvars(ssm_path):
    """Reads all AWS SSM parameters under the given path and adds them to
    the system environment."""
    session = boto3.session.Session()

    client = session.client('ssm')
    next_token = ''
    full_params = []

    print("Reading parameters from SSM path: {}".format(ssm_path))
    try:
        response = client.get_parameters_by_path(
            Path=ssm_path,
            Recursive=True,
            WithDecryption=True
        )
        full_params.extend(response['Parameters'])
        if 'NextToken' in response:
            full_params = response['NextToken']
    except Exception as e:
        print("Error querying list of ssm parameters: {}".format(repr(e)))
        raise

    while next_token:
        try:
            response = client.get_parameters_by_path(
                Path=ssm_path,
                Recursive=True,
                WithDecryption=True,
                NextToken=next_token
            )
            full_params.extend(response['Parameters'])
            if 'NextToken' in response:
                next_token = response['NextToken']
            else:
                next_token = ""
        except Exception as e:
            print("Error querying list of ssm parameters: {}".format(repr(e)))
            raise

    print("Read {} parameters from SSM".format(len(full_params)))

    for parameter in full_params:
        try:
            envvar_name = parameter['Name'].split('/')[-1]
            envvar_value = parameter['Value']
            envvar_type = parameter['Type']
            if envvar_name in os.environ:
                print("{} already in environment".format(envvar_name))
            else:
                if not envvar_type == 'SecureString':
                    print(
                        "{} - setting value from ssm: {}".format(envvar_name, envvar_value))
                else:
                    print(
                        "{} - setting value from ssm (SecureString, {} chars)".format(envvar_name, len(envvar_value)))
                os.environ[envvar_name] = envvar_value
        except Exception as e:
            print("Error processing parameter: {}".format(str(e)))


def required_envvars_present():
    """Ensure that the required environment variables are present."""
    missing_required = False
    required_envs = [
        'AWS_REGION'
    ]
    for required_env in required_envs:
        if not required_env in os.environ:
            print("ERROR: {} not found in environment".format(required_env))
            missing_required = True
    if missing_required:
        return False

    # ensure both AWS_REGION and AWS_DEFAULT_REGION are set
    if 'AWS_REGION' in os.environ and not 'AWS_DEFAULT_REGION' in os.environ:
        os.environ['AWS_DEFAULT_REGION'] = os.environ['AWS_REGION']

    # if AWS_REGION and AWS_DEFAULT_REGION are in conflict, set both to AWS_REGION
    if os.environ['AWS_REGION'] != os.environ['AWS_DEFAULT_REGION']:
        print("ERROR: AWS_REGION ({}) and AWS_DEFAULT_REGION ({}) are in conflict.".format(
            os.environ['AWS_REGION'], os.environ['AWS_DEFAULT_REGION']))
        print("Resolving by setting both to {}".format(os.environ['AWS_REGION']))
        os.environ['AWS_DEFAULT_REGION'] = os.environ['AWS_REGION']

    return True


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--ssm-name', required=True,
                        help='The SSM name prefix to load parameters from.')
    parser.add_argument('--command', required=True,
                        help='The command to run after loading SSM parameters into the environment.')
    args = parser.parse_args()
    return args


def main():
    print("SSM Starter version {}".format(__version__))

    args = parse_args()
    if not required_envvars_present():
        sys.exit(1)

    env_name = os.environ.get('AWS_ENV', None)
    ssm_path = '' if not env_name else "/{}/".format(env_name)
    ssm_path += args.ssm_name
    if not ssm_path[-1] == '/':
        ssm_path +='/'
    load_ssm_envvars(ssm_path)

    # after loading SSM parameters into the environment, run the given
    # command to start the application
    print(args.command)
    exit_code = os.system(args.command)

    print("SSM Starter - application ended with exit code {}".format(exit_code))
    if exit_code > 127 or exit_code < 0:
        print("Exit code from application out of range, overriding to exit code 1")
        exit_code = 1
    sys.exit(exit_code)
