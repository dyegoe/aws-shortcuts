#!/usr/bin/env python3

import argparse
import boto3
import sys
import json
from tabulate import tabulate
from collections import OrderedDict


def main_parser() -> None:
    """
    Create the main parser.

    Returns:
        ArgumentParser: Argparser object.
    """
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
    parser.add_argument(
        "--output",
        choices=["json", "table"],
        help="Select the output format. You may use 'json' or 'table'",
        default="table",
    )
    subparsers = parser.add_subparsers(
        dest="command",
        help="You must select one of these options to move on. Additional info: <command> --help",
    )
    ec2_subparser(subparsers)
    eni_subparser(subparsers)
    elb_subparser(subparsers)
    return parser


def ec2_subparser(subparsers):
    """
    Create a subparser for EC2.

    Args:
        subparsers (_SubParsersAction[ArgumentParser]): Argparser subparsers.
    """
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


def eni_subparser(subparsers):
    """
    Create a subparser for ENIs.

    Args:
        subparsers (_SubParsersAction[ArgumentParser]): Argparser subparsers.
    """
    eni_parser = subparsers.add_parser(
        "eni",
        help="""Use it to search across ENIs (Elastic Network Interfaces).
                        You can search by private IPs or public IPs.""",
    )
    eni_arg_group = eni_parser.add_mutually_exclusive_group(required=True)
    eni_arg_group.add_argument(
        "-p",
        "--privateIps",
        help="Provide a list of comma-separated private IPs. e.g. --privateIps 172.16.0.1,172.17.1.254",
    )
    eni_arg_group.add_argument(
        "-P",
        "--publicIps",
        help="Provide a list of comma-separated public IPs. e.g. --publicIps 52.28.19.20,52.30.31.32",
    )


def elb_subparser(subparsers):
    """
    Create a subparser for ELBs.

    Args:
        subparsers (_SubParsersAction[ArgumentParser]): Argparser subparsers.
    """
    elb_parser = subparsers.add_parser(
        "elb",
        help="""Use it to search across ELBv2 (Elastic Load Balancer).
                        You can search by ARNs, by names or by DNS names.""",
    )
    elb_parser.set_defaults(func=elb)
    elb_arg_group = elb_parser.add_mutually_exclusive_group(required=True)
    elb_arg_group.add_argument(
        "-a",
        "--arns",
        help="""Provide a list of comma-separated ARNs.
                e.g. --arns arn:aws:elasticloadbalancing:eu-central-1:123456789012:loadbalancer/app/name-1/abc123def456ghi7""",
    )
    elb_arg_group.add_argument(
        "-n",
        "--names",
        help="""Provide a list of comma-separated names.
                e.g. --names name-1,name-2""",
    )
    elb_arg_group.add_argument(
        "-d",
        "--dnsNames",
        help="""Provide a list of comma-separated DNS names.
                e.g. --dnsNames internal-name-1-123456789.eu-central-1.elb.amazonaws.com,
                name-2-123abc456def789g.elb.eu-central-1.amazonaws.com""",
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
        try:
            session = boto3.Session(profile_name=profile_name, region_name="us-east-1")
            client = session.client("ec2")
            regions = client.describe_regions(
                Filters=[
                    {
                        "Name": "opt-in-status",
                        "Values": ["opt-in-not-required", "opted-in"],
                    }
                ]
            )["Regions"]
            for region in regions:
                yield from get_aws_session(profile_name, region["RegionName"])
        except Exception:
            yield None
    else:
        try:
            session = boto3.Session(profile_name=profile_name, region_name=region_name)
            yield session
        except Exception:
            yield None


def get_ec2_instances_by_ids(session, instance_ids):
    """
    Get all EC2 instances with a specific instance ID.
    """
    client = session.client("ec2")
    try:
        response = client.describe_instances(InstanceIds=instance_ids)
        return response
    except client.exceptions.ClientError as e:
        if e.response["Error"]["Code"] == "InvalidInstanceID.NotFound":
            return {"Reservations": []}
        else:
            return None
    except Exception as e:
        return None


def get_ec2_instances_by_tags(session, tag_key, tag_values):
    """
    Get all EC2 instances with a specific tag.
    """
    client = session.client("ec2")
    try:
        response = client.describe_instances(
            Filters=[{"Name": "tag:{}".format(tag_key), "Values": tag_values}]
        )
        return response
    except Exception:
        return None


def get_ec2_instances_by_private_ips(session, private_ips):
    """
    Get all EC2 instances with a specific private IP.
    """
    client = session.client("ec2")
    try:
        response = client.describe_instances(
            Filters=[{"Name": "private-ip-address", "Values": private_ips}]
        )
        return response
    except Exception:
        return None


def get_ec2_instances_by_public_ips(session, public_ips):
    """
    Get all EC2 instances with a specific public IP.
    """
    client = session.client("ec2")
    try:
        response = client.describe_instances(
            Filters=[{"Name": "ip-address", "Values": public_ips}]
        )
        return response
    except Exception:
        return None


def get_enis_by_private_ips(session, private_ips):
    """
    Get all ENIs with a specific private IP.
    """
    client = session.client("ec2")
    try:
        response = client.describe_network_interfaces(
            Filters=[{"Name": "addresses.private-ip-address", "Values": private_ips}]
        )
        return response
    except Exception:
        return None


def get_enis_by_public_ips(session, public_ips):
    """
    Get all ENIs with a specific public IP.
    """
    client = session.client("ec2")
    try:
        response = client.describe_network_interfaces(
            Filters=[{"Name": "addresses.association.public-ip", "Values": public_ips}]
        )
        return response
    except Exception:
        return None


def get_elbs_by_arns(session, arns):
    """
    Get all ELBs with a specific ARN.
    """
    client = session.client("elbv2")
    try:
        response = client.describe_load_balancers(LoadBalancerArns=arns)
        print(response)
        return response
    except Exception:
        return None


def get_elbs_by_names(session, names):
    """
    Get all ELBs with a specific name.
    """
    client = session.client("elbv2")
    try:
        response = client.describe_load_balancers(Names=names)
        return response
    except Exception:
        return None


def get_elbs_by_dns_names(session, dns_names):
    """
    Get all ELBs with a specific DNS name.
    """
    client = session.client("elbv2")
    try:
        elbs = client.describe_load_balancers()
        response = {"LoadBalancers": []}
        for elb in elbs["LoadBalancers"]:
            if elb["DNSName"] in dns_names:
                response["LoadBalancers"].append(elb)
        return response
    except Exception:
        return None


def deserialize(response):
    """
    Deserialize the response.
    """
    if "Reservations" in response:
        return deserialize_ec2_instances(response)
    elif "NetworkInterfaces" in response:
        return deserialize_enis(response)
    elif "LoadBalancers" in response:
        return deserialize_elbs(response)


def find_tag_name(instance):
    """
    Get the name of an instance.
    """
    if "Tags" in instance:
        for tag in instance["Tags"]:
            if tag["Key"] == "Name":
                return tag["Value"]
    return None


def deserialize_ec2_instances(response):
    """
    Deserialize the EC2 instances response.
    """
    instances = []
    for reservation in response["Reservations"]:
        for instance in reservation["Instances"]:
            instances.append(
                OrderedDict(
                    [
                        ("InstanceState", instance.get("State", None).get("Name")),
                        ("InstanceName", find_tag_name(instance)),
                        ("InstanceId", instance.get("InstanceId", None)),
                        ("InstanceType", instance.get("InstanceType", None)),
                        (
                            "AvailabilityZone",
                            instance.get("Placement", None).get(
                                "AvailabilityZone", None
                            ),
                        ),
                        ("PrivateIpAddress", instance.get("PrivateIpAddress", None)),
                        ("PublicIpAddress", instance.get("PublicIpAddress", None)),
                    ]
                )
            )
    return instances


def deserialize_enis(response):
    """
    Deserialize the ENIs response.
    """
    enis = []
    for eni in response["NetworkInterfaces"]:
        enis.append(
            OrderedDict(
                [
                    ("PrivateIp", eni.get("PrivateIpAddress", None)),
                    ("PublicIp", eni.get("Association", None).get("PublicIp", None)),
                    ("NetworkInterfaceId", eni.get("NetworkInterfaceId", None)),
                    ("InterfaceType", eni.get("InterfaceType", None)),
                    ("InstanceId", eni.get("Attachment", None).get("InstanceId", None)),
                    ("AvailabilityZone", eni.get("AvailabilityZone", None)),
                    ("Status", eni.get("Status", None)),
                ]
            )
        )
    return enis


def deserialize_elbs(response, dns_names=None):
    """
    Deserialize the ELBs response.
    """
    elbs = []
    for elb in response["LoadBalancers"]:
        elbs.append(
            OrderedDict(
                [
                    ("LoadBalancerName", elb.get("LoadBalancerName", None)),
                    ("DNSName", elb.get("DNSName", None)),
                    ("Type", elb.get("Type", None)),
                    ("Scheme", elb.get("Scheme", None)),
                    ("LoadBalancerArn", elb.get("LoadBalancerArn", None)),
                ]
            )
        )
    return elbs


def print_data(table_data, profile_name, region_name, output):
    """
    Print the data in a table.
    """
    if output == "table":
        print(
            "[+] Session created for profile '{}' and region '{}'".format(
                profile_name, region_name
            )
        )
        print(tabulate(table_data, headers="keys", tablefmt="pretty"))
    elif output == "json":
        print(
            json.dumps(
                {
                    "profile": profile_name,
                    "region": region_name,
                    "data": table_data,
                },
                indent=4,
            )
        )


def aws_search(profile_name, region_name, output, func, **kwargs):
    """
    Iterate over all AWS sessions and call the function with the provided arguments.
    """
    for session in get_aws_session(profile_name, region_name):
        if session is not None:
            response = func(session, **kwargs)
            if response is not None:
                table_data = deserialize(response)
                print_data(
                    table_data, session.profile_name, session.region_name, output
                )
        else:
            continue


def ec2(args):
    """
    Search for EC2 instances.
    """
    if args.ids:
        ids = args.ids.split(",")
        aws_search(
            args.profile,
            args.region,
            args.output,
            get_ec2_instances_by_ids,
            instance_ids=ids,
        )
    elif args.names:
        names = args.names.split(",")
        aws_search(
            args.profile,
            args.region,
            args.output,
            get_ec2_instances_by_tags,
            tag_key="Name",
            tag_values=names,
        )
    elif args.privateIps:
        privateIps = args.privateIps.split(",")
        aws_search(
            args.profile,
            args.region,
            args.output,
            get_ec2_instances_by_private_ips,
            private_ips=privateIps,
        )
    elif args.publicIps:
        publicIps = args.publicIps.split(",")
        aws_search(
            args.profile,
            args.region,
            args.output,
            get_ec2_instances_by_public_ips,
            public_ips=publicIps,
        )
    else:
        sys.exit("EC2: You didn't provide the right parameter")


def eni(args):
    """
    Search for ENIs.
    """
    if args.privateIps:
        privateIps = args.privateIps.split(",")
        aws_search(
            args.profile,
            args.region,
            args.output,
            get_enis_by_private_ips,
            private_ips=privateIps,
        )
    elif args.publicIps:
        publicIps = args.publicIps.split(",")
        aws_search(
            args.profile,
            args.region,
            args.output,
            get_enis_by_public_ips,
            public_ips=publicIps,
        )
    else:
        sys.exit("ENI: You didn't provide the right parameter")


def elb(args):
    """
    Search for ELBs.
    """
    if args.arns:
        arns = args.arns.split(",")
        aws_search(
            args.profile,
            args.region,
            args.output,
            get_elbs_by_arns,
            arns=arns,
        )
    elif args.names:
        names = args.names.split(",")
        aws_search(
            args.profile,
            args.region,
            args.output,
            get_elbs_by_names,
            names=names,
        )
    elif args.dnsNames:
        dnsNames = args.dnsNames.split(",")
        aws_search(
            args.profile,
            args.region,
            args.output,
            get_elbs_by_dns_names,
            dns_names=dnsNames,
        )
    else:
        sys.exit("ELB: You didn't provide the right parameter")


parser = main_parser()
args = parser.parse_args()

if args.command is None:
    parser.print_help()
    sys.exit(1)

if args.command == "ec2":
    ec2(args)
elif args.command == "eni":
    eni(args)
elif args.command == "elb":
    elb(args)
