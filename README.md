# ssm-starter

[![PyPI version](https://badge.fury.io/py/ssm-starter.svg)](https://badge.fury.io/py/ssm-starter)

Loads AWS SSM Parameter Store parameters into local system environment variables and then executes your application so it has access to those environment variables.

This was inspired by the Twelve-Factor App principle [Store config in the environment](https://12factor.net/config).

The intended use case is to be used as the ENTRYPOINT to Docker containers which run in AWS where the application gets its configuration from SSM and stores it in the environment, then starts the application, which can reference these values through the environment. 

## Installation

```shell
pip install ssm-starter
```

## Usage

SSM-Starter is installed as a command line utility and can be run as:

```shell
ssm-starter --ssm-name /dev/my-app/ --command /bin/bash run-app.sh
```

Regarding format of ssm-name and pathing, note that all of the following are equivalent:

```shell
ssm-starter --ssm-name /dev/my-app --command /bin/bash run-app.sh
ssm-starter --ssm-name /dev/my-app/ --command /bin/bash run-app.sh
AWS_ENV=dev ssm-starter --ssm-name my-app --command /bin/bash run-app.sh
```

## Example

Let's say you have the following three AWS SSM Parameters and their values.

SSM Path | Value
---------|-------
/dev/my-app/MYAPP_TEST_VAR | abc123
/dev/my-app/MYAPP_DB_CONN_STRING | Server=myserver;Database=mydb;Uid=myuid;Pwd=secret;
/dev/my-app/MYAPP_TEST_TWO | xyz789

Running ssm-starter with the ssm-name "my-app" and environment variable AWS_ENV set to "dev" result in the following:

```shell
  $ export AWS_REGION=us-east-1
  $ export AWS_ENV=dev
  $ ssm-starter --ssm-name my-app --command /bin/bash run-app.sh
  Reading parameters from SSM path: /dev/my-app/
  Read 3 parameters from SSM
  MYAPP_TEST_VAR - setting value from ssm: abc123
  MYAPP_DB_CONN_STRING - setting value from ssm (SecureString, 51 chars)
  MYAPP_TEST_TWO already in environment
  /bin/bash run-app.sh
```

After this runs these variables are in the environment and accessible to the application.  Notice that if the SSM parameter was stored as a SecureString, the value is not echoed to stdout, and that if an environment variable already exists with that name, it is not overwritten.  So if an environment variable is directly passed into the container through "docker run -e" or given to it by an orchestrator such as if it is defined in the task definition for ECS, that will take precidence.

## Arguments

`--ssm-name`
The name prefix of your application.  If you have an environment variable AWS_ENV present, it will additionally prefix this with that.  Multiple `--ssm-name` arguments can be provided in which case SSM starter will read all parameters from each SSM path provided.

`--command`
The command to execute after loading the SSM variables into the environment.  The command does not need to be enclosed in quotes but *this should be the last argument as all arguments after this are assumed to be part of the command to execute*.

`--abort-if-duplicates`
This optional argument will instruct SSM Starter to abort (non-zero exit code) if any duplicate parameter names are found.  This would only occur if multiple `--ssm-name` arguments are provided.  The default behavior is to skip any encountered duplicates, which also logs a warning message.

`--overwrite-if-duplicates`
This optional argument will instruct SSM Starter to overwrite if any duplicate parameter names are found, so the last parameter "wins".  This would only occur if multiple `--ssm-name` arguments are provided.  The default behavior is to skip any encountered duplicates, which also logs a warning message.

`AWS_ENV` (environment variable)
If present, this will be prefixed before the supplied ssm-name.  If you have a separate AWS accounts for each environment, you will not need this.  If however you are sharing a single AWS account for multiple environments (dev, stage, prod, etc) then this provides a way to partition the SSM variables.

`AWS_REGION` (environment variable)
The AWS_REGION environment variable is expected to be present. Region is set by this environment variable rather than though an argument to ssm-starter so that the same configuration can be promoted to multiple environments that may be in different regions.  If only AWS_REGION is set, ssm-starter will also set AWS_DEFAULT_REGION to the same value.  If both are set and in conflict, ssm-starter will set both to the value in AWS_REGION.

## Build and test locally

```shell
docker build -t billtrust/ssm-starter:build -f Dockerfile.buildenv .

pip install iam-docker-run --user

# specify a valid IAM role name which has full permissions to SSM
export IAM_ROLE_NAME="role-ops-developers"

# specify a local AWS profile name which has access to assume the above IAM role
export AWS_PROFILE_NAME="dev"

# this executes the integration test using python scripttest in the context of
# the specified IAM role which has access to SSM
iam-docker-run \
  --image billtrust/ssm-starter:build \
  --aws-role-name $IAM_ROLE_NAME \
  --profile $AWS_PROFILE_NAME \
  --host-source-path . \
  --full-entrypoint "make test"
```

## Publishing Updates to PyPi

For the maintainer - to publish an updated version of ssm-search, increment the version number in version.py and run the following:

```shell
docker build -f ./Dockerfile.buildenv -t billtrust/ssm-starter:build .
docker run --rm -it --entrypoint make billtrust/ssm-starter:build publish
```

At the prompts, enter the username and password to the Billtrust pypi.org repo.

## License

MIT License

Copyright (c) 2018 Factor Systems Inc.

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
