# snapshot
AWS EC2 Snapshot

## About

This project uses boto3 to manage EC2 instance snapshots

## Configuration

Snapshot uses the configuration file created by AWS CLI.

`aws configure --profile`

## Running 

`pipenv run python snapshot.py <command> <sub commands> <--backup=Yes `

*command* is instances, volumes, or snapshots
*sub command* depends on command
*backup* is Tag Backup = Yes