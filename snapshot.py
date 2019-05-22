import boto3
import botocore
import click

session = boto3.Session(profile_name='brianm')
ec2 = session.resource('ec2')

def filter_instances(backup):
    instances = []

    if backup:
        filters = [{'Name' : 'tag:Backup', 'Values':[backup]}]
        instances = ec2.instances.filter(Filters=filters)
    else:
        instances = ec2.instances.all()

    return instances

def has_pending_snapshot(volume):
    snapshots = list(volume.snapshots.all())
    return snapshots and snapshots[0].state == 'pending'
@click.group()
def cli():
    """Commands for cli"""

@cli.group('volumes')
def volumes():
    """Commands for volumes"""

@volumes.command('list')
@click.option('--backup', default=None, 
    help='Only instances for backup (tag Backup:<name>)')
def list_volumes(backup):
    "List EC2 volumes"

    instances = filter_instances(backup)

    for i in instances:
        for v in i.volumes.all():
            print(', '.join((
                v.id,
                i.id,
                v.state,
                str(v.size) + "GiB",
                v.encrypted and 'Encrypted' or 'Not Encyrpted'
            )))
    
    return
@cli.group('snapshots')
def snapshots():
    """Commands for snapshots"""

@snapshots.command('list')
@click.option('--backup', default=None, 
    help='Only instances for backup (tag Backup:<name>)')
@click.option('--all', 'list_all', default=False, is_flag=True,
    help='List all snapshots, not just the most recent')
def list_snapshots(backup,list_all):
    "List EC2 snapshots"

    instances = filter_instances(backup)

    for i in instances:
        for v in i.volumes.all():
            for s in v.snapshots.all():
                print(', '.join((
                    s.id,
                    v.id,
                    i.id,
                    s.state,
                    s.progress,
                    s.start_time.strftime('%c')
                )))

                if s.state == 'completed' and not list_all: break
    return

@cli.group('instances')
def instances():
    """Commands for instances"""

@instances.command('snapshot')
@click.option('--backup', default=None, 
    help='Only instances for backup (tag Backup:<name>)')
def create_snapshots(backup):
    "Create snapshots for EC2 instance"

    instances = filter_instances(backup)

    for i in instances:
        print('Stopping {0}...'.format(i.id))

        i.stop()
        i.wait_until_stopped()

        for v in i.volumes.all():
            if has_pending_snapshot(v):
                print(' Skipping {0}, snapshot already in progress'.format(v.id))
                continue

            print('Creating snapshot of {0}'.format(v.id))
            v.create_snapshot(Description='Created by Python Snapshot'),
                        
        print('Starting {0}...'.format(i.id))

        i.start()
        i.wait_until_running()

    print('Jobs Done!')
    
    return

@instances.command('list')
@click.option('--backup', default=None, 
    help='Only instances for backup (tag Backup:<name>)')
def list_instances(backup):
    "List EC2 Instances"

    instances = filter_instances(backup)

    for i in instances:
        tags = { t['Key']: t['Value'] for t in i.tags or []}
        print(','.join((
            i.id,
            i.instance_type,
            i.placement['AvailabilityZone'],
            i.state["Name"],
            i.public_dns_name,
            tags.get('Backup', '<no backup>')
            )))
        
    return

@instances.command('stop')
@click.option('--backup', default=None, 
    help='Only instances for backup')
def stop_instances(backup):
    'Stop EC2 Instances'

    instances = filter_instances(backup)

    for i in instances:
        print('Stopping {0}...'.format(i.id))
        try:
            i.stop()
        except botocore.exceptions.ClientError as e:
            print('Could not stop {0}. '.format(i.id) + str(e))
            continue

    return
@instances.command('start')
@click.option('--backup', default=None, 
    help='Only instances for backup')
def start_instances(backup):
    'Start EC2 Instances'

    instances = filter_instances(backup)

    for i in instances:
        print('Starting {0}...'.format(i.id))
        try:
            i.start()
        except botocore.exceptions.ClientError as e:
            print('Could not start {0}. '.format(i.id) + str(e))
            continue

    return

if __name__ == '__main__':
    cli()