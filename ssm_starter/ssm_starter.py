# -*- coding: utf-8 -*-

from __future__ import print_function
import os
import sys
import argparse
import boto3


__version__ = "0.2.2"


def load_ssm_params(ssm_path):
    """Reads all AWS SSM parameters under the given path and adds them to
    the system environment."""
    session = boto3.session.Session()

    client = session.client('ssm')
    next_token = ''
    page = 1
    full_params = []

    print("Reading parameters from SSM path: {}".format(ssm_path))
    try:
        response = client.get_parameters_by_path(
            Path=ssm_path,
            Recursive=True,
            MaxResults=10,
            WithDecryption=True
        )
        full_params.extend(response['Parameters'])
        if 'NextToken' in response:
            next_token = response['NextToken']
    except Exception as e:
        print("Error querying list of ssm parameters: {}".format(repr(e)))
        raise

    while next_token:
        page += 1
        print("Reading page {} of parameters by path...".format(page))
        try:
            response = client.get_parameters_by_path(
                Path=ssm_path,
                Recursive=True,
                WithDecryption=True,
                MaxResults=10,
                NextToken=next_token
            )
            if not response['Parameters']:
                print("Error - No additional parameters found in subsequent page read!")
            full_params.extend(response['Parameters'])
            if 'NextToken' in response:
                next_token = response['NextToken']
            else:
                next_token = ''
        except Exception as e:
            print("Error querying list of ssm parameters: {}".format(repr(e)))
            raise

    print("Read {} parameters from SSM".format(len(full_params)))
    return full_params


def export_ssm_envvars(ssm_params, overwrite_duplicates):
    duplicate_envvar_names = []
    for parameter in ssm_params:
        try:
            envvar_name = parameter['Name'].split('/')[-1]
            envvar_value = parameter['Value']
            envvar_type = parameter['Type']
            is_duplicate = envvar_name in os.environ
            if is_duplicate:
                duplicate_envvar_names.append(envvar_name)

                if overwrite_duplicates:
                    print("WARNING: Will OVERWRITE {} existing environment variable with {}".format(
                        envvar_name, parameter['Name']))
                else:
                    # default behavior is to skip
                    print("WARNING: {} already in environment, skipping {}".format(
                        envvar_name, parameter['Name']))
                    continue

            if not envvar_type == 'SecureString':
                print(
                    "{} - setting value from ssm: {}".format(envvar_name, envvar_value))
            else:
                print(
                    "{} - setting value from ssm (SecureString, {} chars)".format(envvar_name, len(envvar_value)))
            os.environ[envvar_name] = envvar_value
        except Exception as e:
            print("Error processing parameter: {}\nParameter: {}".format(str(e), parameter))
    return duplicate_envvar_names


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


def valid_ssm_path(ssm_name):
    env_name = os.environ.get('AWS_ENV', None)
    # you can't specify a full path with an AWS_ENV name
    if ssm_name[0] == '/' and env_name:
        print(''.join((
            "SSM Starter - Invalid SSM parameter name; AWS_ENV can not be combined ",
            "with fully qualified path: {}".format(ssm_name)
            )))
        return False
    if not ssm_name[0] == '/' and not env_name:
        print(''.join((
            "SSM Starter - Invalid SSM parameter name; AWS_ENV not specified and ",
            "fully qualified path not given for: {}".format(ssm_name)
            )))
        return False
    return True


def build_full_ssm_path(ssm_name):
    env_name = os.environ.get('AWS_ENV', None)
    ssm_path = '' if not env_name else "/{}/".format(env_name)
    ssm_path += ssm_name
    # ssm path must begin with a /
    if not ssm_path[0] == '/':
        ssm_path = '/' + ssm_path
    # and end with a /
    if not ssm_path[-1] == '/':
        ssm_path +='/'
    return ssm_path


def validate_ssm_path_names(ssm_names):
    for ssm_name in ssm_names:
        if not valid_ssm_path(ssm_name):
            return False
    return True    

def load_ssm_params_into_environment(ssm_names, overwrite_duplicates, abort_if_duplicates):
    ssm_params = []
    for ssm_name in ssm_names:
        ssm_path = build_full_ssm_path(ssm_name)
        ssm_params.extend(load_ssm_params(ssm_path))

    duplicate_envvar_names = \
        export_ssm_envvars(ssm_params, overwrite_duplicates)
    return duplicate_envvar_names


def start_entrypoint(command):
    print(command)
    exit_code = os.system(command)
    print("SSM Starter - application ended with exit code {}".format(exit_code))
    if exit_code > 127 or exit_code < 0:
        print("Exit code from application out of range, overriding to exit code 1")
        exit_code = 1
    return exit_code


def create_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument('--ssm-name', required=True, action='append', dest='ssm_names',
                        help='The SSM name prefix to load parameters from.')
    mutually_exclusive_group = parser.add_mutually_exclusive_group(required=False)
    mutually_exclusive_group.add_argument('--abort-if-duplicates', action='store_true',
                        default=False,
                        help='If set will abort (non-zero exit) if dupliate SSM parameter names are encountered.')
    mutually_exclusive_group.add_argument('--overwrite-if-duplicates', action='store_true',
                        default=False,
                        help='If set will overwrite the last value if dupliate SSM parameter names are encountered.')
    parser.add_argument('--command', required=True, nargs=argparse.REMAINDER,
                        help='The command to run after loading SSM parameters into the environment.')
    return parser


def main():
    print("SSM Starter version {}".format(__version__))

    args = create_parser().parse_args()
    if not required_envvars_present():
        print("SSM Starter - ERROR, exiting due to missing required environment variables")
        sys.exit(1)

    valid = validate_ssm_path_names(args.ssm_names)
    if not valid:
        print("SSM Starter - ERROR, exiting due to invalid SSM parameter names given")
        sys.exit(1)

    duplicate_envvar_names = \
        load_ssm_params_into_environment(
            args.ssm_names,
            args.overwrite_if_duplicates,
            args.abort_if_duplicates)

    if duplicate_envvar_names:
        if args.abort_if_duplicates:
            print("SSM Starter - ERROR, duplicate SSM param names found and --abort-if-duplicates argument present")
            sys.exit(1)

    # after loading SSM parameters into the environment, run the given command
    # to start the application

    command = ' '.join(args.command)
    exit_code = start_entrypoint(command)
    sys.exit(exit_code)
