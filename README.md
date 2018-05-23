# ssm-starter

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
ssm-starter --ssm-name my-app --command "/bin/bash run-app.sh"
```

Alternatively:

```shell
python -m ssm_starter --ssm-name my-app --command "/bin/bash run-app.sh"
```

Regarding format of ssm-name and pathing, note that all of the following are equivalent:

```shell
ssm-starter --ssm-name /dev/my-app --command "/bin/bash run-app.sh"
ssm-starter --ssm-name /dev/my-app/ --command "/bin/bash run-app.sh"
export AWS_ENV=dev && ssm-starter --ssm-name my-app --command "/bin/bash run-app.sh"
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
  $ ssm-starter --ssm-name my-app --command "/bin/bash run-app.sh"
  Reading parameters from SSM path: /dev/my-app/
  Read 3 parameters from SSM
  MYAPP_TEST_VAR - setting value from ssm: abc123
  MYAPP_DB_CONN_STRING - setting value from ssm (SecureString, 51 chars)
  MYAPP_TEST_TWO already in environment
  /bin/bash run-app.sh
```

After this runs these variables are in the environment and accessible to the application.  Notice that if the SSM parameter was stored as a SecureString, the value is not echoed to stdout, and that if an environment variable already exists with that name, it is not overwritten.  So if an environment variable is directly passed into the container through "docker run -e" or given to it by an orchestrator such as if it is defined in the task definition for ECS, that will take precidence.

## Arguments

**ssm-name**
The name prefix of your application.  If you have an environment variable AWS_ENV present, it will additionally prefix this with that.

**command**
  The command to execute after loading the SSM variables into the environment.  Needs to be enclosed in quotes if there are spaces.  This is simply passed to os.system(command).

**AWS_ENV (environment variable)**
  If present, this will be prefixed before the supplied ssm-name.  If you have a separate AWS accounts for each environment, you will not need this.  If however you are sharing a single AWS account for multiple environments (dev, stage, prod, etc) then this provides a way to partition the SSM variables.

**AWS_REGION (environment variable)**
  The AWS_REGION environment variable is expected to be present. Region is set by this environment variable rather than though an argument to ssm-starter so that the same configuration can be promoted to multiple environments that may be in different regions.  If only AWS_REGION is set, ssm-starter will also set AWS_DEFAULT_REGION to the same value.  If both are set and in conflict, ssm-starter will set both to the value in AWS_REGION.
