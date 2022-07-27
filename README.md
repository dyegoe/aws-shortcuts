# aws-shortcuts

A Python script using Boto3 to make searching resources easier on AWS

## Installation

```txt
make install
```

It will copy the python script to `~/.local/bin/`. Make sure that this path is in your `$PATH`.

```txt
make requirements
```

## Usage

```txt
aws-shortcuts --help

usage: aws-shortcuts.py [-h] [--profile PROFILE] [--region REGION] [--output {json,table}] {ec2,eni,elb} ...

This script intends to create additional ways to perform AWS API requests.

positional arguments:
  {ec2,eni,elb}         You must select one of these options to move on. Additional info: <command> --help
    ec2                 Use it to search across EC2 instances. You can search by ids, names, by private IPs or public IPs.
    eni                 Use it to search across ENIs (Elastic Network Interfaces). You can search by private IPs or public IPs.
    elb                 Use it to search across ELBv2 (Elastic Load Balancer). You can search by ARNs, by names or by DNS names.

options:
  -h, --help            show this help message and exit
  --profile PROFILE     Select the profile from ~/.aws/config. You may use 'all' to search across all profiles. (default: default)
  --region REGION       Select a region to perform your API calls. You may use 'all' to search across all regions. (default: eu-central-1)
  --output {json,table}
                        Select the output format. You may use 'json' or 'table' (default: table)

See '<command> --help' to read about a specific sub-command.
```

For example, to lookup for instances with names `some-instance-1,another-instance-2`.

```txt
aws-shortcuts --profile some-profile --region eu-central-1 ec2 -n 'some-instance-1,another-instance-2'
```

To itarate across all profiles and/or regions

```txt
aws-shortcuts --profile all --region all ec2 -P 200.201.202.203
```
