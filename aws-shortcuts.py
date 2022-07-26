#!/usr/bin/env python3

import argparse
import boto3
import sys
from tabulate import tabulate
from collections import OrderedDict


def main_parser() -> None:
    parser = argparse.ArgumentParser(
        description="This script intends to create additional ways to perform AWS API requests.",
        epilog="See '<command> --help' to read about a specific sub-command.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument
    parser.add_argument(
        "--profile",
        help="Select the profile from ~/.aws/config. You may use 'all' to search across all profiles.",
        default="default",
    )
    parser.add_argument(
        "--region",
        help="Select a region to perform your API calls. You may use 'all' to search across all regions.",
        default="eu-central-1",
    )
    subparsers = parser.add_subparsers(
        dest="command",
        help="You must select one of these options to move on. Additional info: <command> --help",
    )
    ec2_subparser(subparsers)
    return parser


def ec2_subparser(subparsers):
    ec2_parser = subparsers.add_parser(
        "ec2",
        help="""Use it to search across EC2 instances.
                        You can search by ids, names, by private IPs or public IPs.""",
    )
    ec2_arg_group = ec2_parser.add_mutually_exclusive_group(required=True)
    ec2_arg_group.add_argument(
        "-i",
        "--ids",
        help="Provide a list of comma-separated ids. e.g. --ids i-xxxxxxxxxxxxxxxxx,i-xxxxxxxxxxxxxxxxx",
    )
    ec2_arg_group.add_argument(
        "-n",
        "--names",
        help="Provide a list of comma-separated names. It searchs using the `tag:Name`. e.g. --names instance-1,instance-2",
    )
    ec2_arg_group.add_argument(
        "-p",
        "--privateIps",
        help="Provide a list of comma-separated private IPs. e.g. --privateIps 172.16.0.1,172.17.1.254",
    )
    ec2_arg_group.add_argument(
        "-P",
        "--publicIps",
        help="Provide a list of comma-separated public IPs. e.g. --publicIps 52.28.19.20,52.30.31.32",
    )


def get_aws_session(profile_name, region_name):
    """
    Get an AWS session using the profile and region names.
    """
    if profile_name == "all":
        profiles = boto3.Session().available_profiles
        for profile in profiles:
            yield from get_aws_session(profile, region_name)
    elif region_name == "all":
        regions = (
            boto3.Session(profile_name=profile_name, region_name="us-east-1")
            .client("ec2")
            .describe_regions(
                Filters=[
                    {
                        "Name": "opt-in-status",
                        "Values": ["opt-in-not-required", "opted-in"],
                    }
                ]
            )["Regions"]
        )
        for region in regions:
            yield from get_aws_session(profile_name, region["RegionName"])
    else:
        try:
            session = boto3.Session(profile_name=profile_name, region_name=region_name)
            print(
                "[+] Session created for profile '{}' in region '{}'".format(
                    profile_name, region_name
                )
            )
            yield session
        except Exception as e:
            print("Error: {}".format(e))


def get_ec2_instances_by_ids(session, instance_ids):
    """
    Get all EC2 instances with a specific instance ID.
    """
    ec2 = session.client("ec2")
    try:
        instances = ec2.describe_instances(InstanceIds=instance_ids)
    except ec2.exceptions.ClientError as error:
        instances = {"Reservations": []}
    return instances


def get_ec2_instances_by_tags(session, tag_key, tag_values):
    """
    Get all EC2 instances with a specific tag.
    """
    ec2 = session.client("ec2")
    instances = ec2.describe_instances(
        Filters=[{"Name": "tag:{}".format(tag_key), "Values": tag_values}]
    )
    return instances


def get_ec2_instances_by_private_ips(session, private_ips):
    """
    Get all EC2 instances with a specific private IP.
    """
    ec2 = session.client("ec2")
    instances = ec2.describe_instances(
        Filters=[{"Name": "private-ip-address", "Values": private_ips}]
    )
    return instances


def get_ec2_instances_by_public_ips(session, public_ips):
    """
    Get all EC2 instances with a specific public IP.
    """
    ec2 = session.client("ec2")
    instances = ec2.describe_instances(
        Filters=[{"Name": "ip-address", "Values": public_ips}]
    )
    return instances


def deserialize_ec2_instances(response):
    """
    Deserialize the EC2 instances response.
    """
    instances = []
    for reservation in response["Reservations"]:
        for instance in reservation["Instances"]:
            for tag in instance["Tags"]:
                if tag["Key"] == "Name":
                    instance_name = tag["Value"]
            instances.append(
                OrderedDict(
                    [
                        ("InstanceState", instance["State"]["Name"]),
                        ("InstanceName", instance_name),
                        ("InstanceId", instance["InstanceId"]),
                        ("InstanceType", instance["InstanceType"]),
                        ("AvailabilityZone", instance["Placement"]["AvailabilityZone"]),
                        ("PrivateIpAddress", instance.get("PrivateIpAddress", None)),
                        ("PublicIpAddress", instance.get("PublicIpAddress", None)),
                    ]
                )
            )
    return instances


def print_table(table_data):
    if table_data is not None:
        if len(table_data) > 0:
            print(tabulate(table_data, headers="keys", tablefmt="pretty"))


def aws_search(profile_name, region_name, func, **kwargs):
    for session in get_aws_session(profile_name, region_name):
        print_table(deserialize_ec2_instances(func(session, **kwargs)))


parser = main_parser()
args = parser.parse_args()

if args.command is None:
    parser.print_help()
    sys.exit(1)

if args.command == "ec2":
    if args.ids:
        ids = args.ids.split(",")
        table_data = aws_search(
            args.profile, args.region, get_ec2_instances_by_ids, instance_ids=ids
        )
    elif args.names:
        names = args.names.split(",")
        table_data = aws_search(
            args.profile,
            args.region,
            get_ec2_instances_by_tags,
            tag_key="Name",
            tag_values=names,
        )
    elif args.privateIps:
        privateIps = args.privateIps.split(",")
        table_data = aws_search(
            args.profile,
            args.region,
            get_ec2_instances_by_private_ips,
            private_ips=privateIps,
        )
    elif args.publicIps:
        publicIps = args.publicIps.split(",")
        table_data = aws_search(
            args.profile,
            args.region,
            get_ec2_instances_by_public_ips,
            public_ips=publicIps,
        )
    else:
        sys.exit("EC2: Something wrong")
    print_table(table_data)
