#!/usr/local/bin/python3

import argparse
from urllib import response
import boto3
from tabulate import tabulate
from sys import exit as sysexit


class AwsShortcuts():
    def __init__(self) -> None:
        self.tablefmt = 'pretty'
        self.parser = argparse.ArgumentParser(
            description="This script intends to create additional ways to perform AWS API requests.",
            epilog="See '<command> --help' to read about a specific sub-command.",
            formatter_class=argparse.ArgumentDefaultsHelpFormatter
        )
        self.parser.add_argument
        self.parser.add_argument(
            '--profile',
            help='Select the profile from ~/.aws/config',
            default='default'
        )
        self.parser.add_argument(
            '--region',
            help='Select a region to perform your API calls.',
            default='eu-central-1'
        )
        self.subparsers = self.parser.add_subparsers(
            dest='command',
            help='You must select one of these options to move on. Additional info: <command> --help'
        )
        self.createEC2parser()
        self.createENIparser()
        self.createELBparser()

    def createEC2parser(self):
        self.ec2_parser = self.subparsers.add_parser(
            'ec2', help='''Use it to search across EC2 instances.
                           You can search by name, by private IPs or public IPs.''')
        self.ec2_parser.set_defaults(func=self.ec2)
        ec2_arg_group = self.ec2_parser.add_mutually_exclusive_group(
            required=True)
        ec2_arg_group.add_argument(
            '--names',
            help='Provide a list of comma-separated names. It searchs using the `tag:Name`. e.g. --names instance-1,instance-2'
        )
        ec2_arg_group.add_argument(
            '--privateIps',
            help='Provide a list of comma-separated private IPs. e.g. --privateIps 172.16.0.1,172.17.1.254'
        )
        ec2_arg_group.add_argument(
            '--publicIps',
            help='Provide a list of comma-separated public IPs. e.g. --publicIps 52.28.19.20,52.30.31.32'
        )

    def createENIparser(self):
        self.eni_parser = self.subparsers.add_parser(
            'eni', help='''Use it to search across ENIs (Elastic Network Interfaces).
                           You can search by private IPs or public IPs.''')
        self.eni_parser.set_defaults(func=self.eni)
        eni_arg_group = self.eni_parser.add_mutually_exclusive_group(
            required=True)
        eni_arg_group.add_argument(
            '--privateIps',
            help='Provide a list of comma-separated private IPs. e.g. --privateIps 172.16.0.1,172.17.1.254'
        )
        eni_arg_group.add_argument(
            '--publicIps',
            help='Provide a list of comma-separated public IPs. e.g. --publicIps 52.28.19.20,52.30.31.32'
        )

    def createELBparser(self):
        self.elb_parser = self.subparsers.add_parser(
            'elb', help='''Use it to search across ELBv2 (Elastic Load Balancer).
                           You can search by ARNs, by names or by DNS names.''')
        self.elb_parser.set_defaults(func=self.elb)
        elb_arg_group = self.elb_parser.add_mutually_exclusive_group(
            required=True)
        elb_arg_group.add_argument(
            '--arns',
            help='''Provide a list of comma-separated ARNs.
                    e.g. --arns arn:aws:elasticloadbalancing:eu-central-1:123456789012:loadbalancer/app/name-1/abc123def456ghi7'''
        )
        elb_arg_group.add_argument(
            '--names',
            help='''Provide a list of comma-separated names.
                    e.g. --names name-1,name-2'''
        )
        elb_arg_group.add_argument(
            '--dnsNames',
            help='''Provide a list of comma-separated DNS names.
                    e.g. --dnsNames internal-name-1-123456789.eu-central-1.elb.amazonaws.com,
                    name-2-123abc456def789g.elb.eu-central-1.amazonaws.com'''
        )

    def aws(self):
        session = boto3.Session(
            profile_name=self.args.profile, region_name=self.args.region)
        if self.args.command == 'elb':
            return session.client('elbv2')
        else:
            return session.client('ec2')

    def ec2(self):
        if self.args.names != None:
            filters = [
                {
                    'Name': 'tag:Name',
                    'Values': self.args.names.split(',')
                },
            ]
        elif self.args.privateIps != None:
            filters = [
                {
                    'Name': 'private-ip-address',
                    'Values': self.args.privateIps.split(',')
                },
            ]
        elif self.args.publicIps != None:
            filters = [
                {
                    'Name': 'ip-address',
                    'Values': self.args.publicIps.split(',')
                },
            ]
        else:
            self.ec2_parser.print_help()
            sysexit('EC2: Something wrong')

        client = self.aws()
        response = client.describe_instances(
            Filters=filters, DryRun=False
        )
        instances = []
        for reservation in response['Reservations']:
            instanceTmp = {
                'ReservationId': reservation['ReservationId']
            }
            for instance in reservation['Instances']:
                for tag in instance['Tags']:
                    if tag['Key'] == 'Name':
                        instanceTmp['Name'] = tag['Value']
                instanceTmp['InstanceId'] = instance['InstanceId']
                instanceTmp['InstanceType'] = instance['InstanceType']
                instanceTmp['AvailabilityZone'] = instance['Placement']['AvailabilityZone']
                instanceTmp['PrivateIpAddress'] = instance['PrivateIpAddress']
                instanceTmp['PublicIpAddress'] = instance.get(
                    'PublicIpAddress', None)
            instances.append(instanceTmp)
        print(
            tabulate(
                instances,
                headers={
                    'ReservationId': 'ReservationId',
                    'Name': 'Name',
                    'InstanceId': 'InstanceId',
                    'InstanceType': 'InstanceType',
                    'AvailabilityZone': 'AvailabilityZone',
                    'PrivateIpAddress': 'PrivateIpAddress',
                    'PublicIpAddress': 'PublicIpAddress'
                },
                tablefmt=self.tablefmt
            )
        )

    def eni(self):
        if self.args.privateIps != None:
            filters = [
                {
                    'Name': 'addresses.private-ip-address',
                    'Values': self.args.privateIps.split(',')
                }
            ]
        elif self.args.publicIps != None:
            filters = [
                {
                    'Name': 'addresses.association.public-ip',
                    'Values': self.args.publicIps.split(',')
                }
            ]
        else:
            self.eni_parser.print_help()
            sysexit('ENI: Something wrong')

        client = self.aws()
        response = client.describe_network_interfaces(
            Filters=filters, DryRun=False
        )
        enis = []
        for eni in response['NetworkInterfaces']:
            # pprint(eni)
            eniTmp = {
                'PrivateIp': eni['PrivateIpAddress'],
                'PublicIp': eni['Association']['PublicIp'],
                'NetworkInterfaceId': eni['NetworkInterfaceId'],
                'InterfaceType': eni['InterfaceType'],
                'InstanceId': eni.get('Attachment', None).get('InstanceId', None),
                'AvailabilityZone': eni['AvailabilityZone'],
                'Status': eni['Status']

            }
            enis.append(eniTmp)
        print(
            tabulate(
                enis,
                headers={
                    'PublicIp': 'PublicIp',
                    'NetworkInterfaceId': 'NetworkInterfaceId',
                    'InterfaceType': 'InterfaceType',
                    'InstanceId': 'InstanceId',
                    'AvailabilityZone': 'AvailabilityZone',
                    'Status': 'Status'
                },
                tablefmt=self.tablefmt
            )
        )

    def elb(self):
        client = self.aws()
        if self.args.arns != None:
            try:
                response = client.describe_load_balancers(
                    LoadBalancerArns=self.args.arns.split(',')
                )
            except client.exceptions.ClientError as error:
                response = {'LoadBalancers': []}
        elif self.args.names != None:
            try:
                response = client.describe_load_balancers(
                    Names=self.args.names.split(',')
                )
            except client.exceptions.ClientError as error:
                response = {'LoadBalancers': []}
        elif self.args.dnsNames != None:
            response = client.describe_load_balancers()
        else:
            self.elb_parser.print_help()
            sysexit('ELB: Something wrong')

        elbs = []
        for elb in response['LoadBalancers']:
            if self.args.dnsNames is not None and elb['DNSName'] not in self.args.dnsNames:
                continue
            elbTmp = {
                'LoadBalancerArn': elb['LoadBalancerArn'],
                'LoadBalancerName': elb['LoadBalancerName'],
                'DNSName': elb['DNSName'],
                'Type': elb['Type'],
                'Scheme': elb['Scheme'],
            }
            elbs.append(elbTmp)

        print(
            tabulate(
                elbs,
                headers={
                    'LoadBalancerArn': 'LoadBalancerArn',
                    'LoadBalancerName': 'LoadBalancerName',
                    'DNSName': 'DNSName',
                    'Type': 'Type',
                    'Scheme': 'Scheme',
                },
                tablefmt=self.tablefmt
            )
        )


if __name__ == '__main__':
    n = AwsShortcuts()
    n.args = n.parser.parse_args()
    if n.args.command is not None:
        n.args.func()
    else:
        n.parser.print_help()
