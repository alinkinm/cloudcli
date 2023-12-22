#!/usr/bin/env python3chmod
import click
import boto3
from botocore.client import ClientError
from pathlib import Path
import os
import sys

@click.group(chain=True)
def main():
    pass


@click.command()
@click.option("--name", prompt="Enter your name: ", help="The name of the user")
def hello(name):
    click.echo(f"Hello {name}")


@click.command(name='upload')
@click.option("--album")
@click.option("--path", default="Default")
def upload(album, path):

    _, client, bucket = create_session()

    if path == "Default":
        files = [f for f in os.listdir('.') if os.path.isfile(f)]
        if len(files) == 0:
            sys.stderr.write('No files in dir')
        for f in files:
            if ".jpg" in f or ".ipeg" in f:
                client.upload_file(os.path.join(path, f), bucket, album + "-" + f)

    else:
        files = [f for f in os.listdir(path) if os.path.isfile(os.path.join(path, f))]
        if len(files) == 0:
            sys.stderr.write('No files in dir')
        for f in files:
            if ".jpg" in f or ".ipeg" in f:
                client.upload_file(os.path.join(path, f), bucket, album + "-" + f)


@click.command(name='download')
@click.option("--album")
@click.option("--path", default="Default")
def download(album, path):
    session, client, bucket = create_session()
    response = client.list_objects(Bucket=bucket)

    no_album = 0

    for file in response['Contents']:
        if album in file['Key']:
            no_album +=1
            if path == "Default":
                client.download_file(bucket, file['Key'], file['Key'])
            else:
                client.download_file(bucket, file['Key'], os.path.join(path, file['Key']))
        else:
            pass

    if no_album == 0:
        sys.stderr.write('No album exception')


@click.command(name='list')
@click.option("--album", default="Default")
def list(album):
    session, client, bucket = create_session()
    response = client.list_objects(Bucket=bucket)

    albums = []
    if album == "Default":
        for file in response['Contents']:
            name = file['Key'].split('-')[0]
            if not (name in albums):
                albums.append(name)
        if len(albums) == 0:
            sys.stderr.write('No albums in bucket')

        for name in albums:
            print(name)

    else:
        no_album = 0
        for file in response['Contents']:
            if album in file['Key']:
                no_album+=1
                name = file['Key'].split('-')[1]
                print(name)

        if no_album==0:
            sys.stderr.write('No such album or no photos in the album error')



@click.command(name='delete')
@click.option("--album")
@click.option("--photo", default="Default")
def delete(album, photo):
    session, client, bucket = create_session()
    response = client.list_objects(Bucket=bucket)

    if photo=="Default":
        no_album = 0
        for file in response['Contents']:
            if album in file['Key']:
                no_album+=1
                response = client.delete_object(
                    Bucket=bucket,
                    Key=file['Key'],
                )
        if no_album==0:
            sys.stderr.write('No such album error')
    else:
        check = 0
        no_album = 0
        for file in response['Contents']:
            if album in file['Key']:
                no_album += 1
                if file['Key'] == album+'-'+photo:
                    check+=1
                    response = client.delete_object(
                        Bucket=bucket,
                        Key=album+'-'+photo,
                    )
        if no_album == 0:
            sys.stderr.write('No such album error')
        if check == 0:
            sys.stderr.write('no photo with this name in this album')




@click.command(name='mksite')
#@click.option()
def mksite():
    pass


@click.command(name='init')
#@click.option()
def init():
    aws_access_key_id = click.prompt('Please enter aws access key id:', type=str)
    aws_secret_access_key = click.prompt('Please enter aws secret access key:', type=str)
    bucket = click.prompt('Please enter a bucket name:', type=str)

    home = str(Path.home())
    path = home+"/.config/cloudphoto/"
    Path(path).mkdir(parents=True, exist_ok=True)
    filename = 'cloudphotorc' + '.ini'

    with open(os.path.join(path, filename), 'r') as file:
        filedata = file.read()
        filedata = filedata.replace('INPUT_BUCKET_NAME', bucket)
        filedata = filedata.replace('INPUT_AWS_ACCESS_KEY_ID', aws_access_key_id)
        filedata = filedata.replace('INPUT_AWS_SECRET_ACCESS_KEY', aws_secret_access_key)

    with open(os.path.join(path, filename), 'w') as file:
        file.write(filedata)

    with open(os.path.join(path, filename), 'r') as file:
        for i, line in enumerate(file):
            if '= ' in line:
                result = line.split(' = ')[-1].strip()

                if i == 0:
                    bucket1 = result
                elif i == 1:
                    access_key = result
                elif i == 2:
                    secret_key = result
                elif i == 3:
                    def_reg = result
                elif i == 4:
                    endpoint = result


            if i == 4:
                break

    print(bucket1)
    print(access_key)
    print(secret_key)


    client = boto3.client(
        's3',
        aws_access_key_id=access_key,
        aws_secret_access_key=secret_key,
        region_name=def_reg,
        endpoint_url=endpoint
    )


    buck = client.create_bucket(Bucket=bucket1)

def create_session():
    home = str(Path.home())
    path = home+"/.config/cloudphoto/"
    Path(path).mkdir(parents=True, exist_ok=True)
    filename = 'cloudphotorc' + '.ini'

    with open(os.path.join(path, filename), 'r') as file:
        for i, line in enumerate(file):
            if '= ' in line:
                result = line.split(' = ')[-1].strip()

                if i == 0:
                    bucket1 = result
                elif i == 1:
                    access_key = result
                elif i == 2:
                    secret_key = result
                elif i == 3:
                    def_reg = result
                elif i == 4:
                    endpoint = result


            if i == 4:
                break

    client = boto3.client(
        's3',
        aws_access_key_id=access_key,
        aws_secret_access_key=secret_key,
        region_name=def_reg,
        endpoint_url=endpoint
    )

    session = boto3.Session(
        aws_access_key_id=access_key,
        aws_secret_access_key=secret_key,
        region_name=def_reg
    )

    return session, client, bucket1




main.add_command(init)
main.add_command(upload)
main.add_command(download)
main.add_command(list)
main.add_command(delete)


if __name__ == '__main__':
    main()
