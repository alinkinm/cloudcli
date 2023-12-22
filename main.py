#!/usr/bin/env python3chmod
import click
import boto3
from botocore.client import ClientError
from pathlib import Path
import os
import sys
import json
import io
from bs4 import BeautifulSoup
from collections import OrderedDict

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

    print(bucket)

    response = client.list_objects(Bucket=bucket)

    no_album = 0

    for file in response['Contents']:
        if album in file['Key']:
            no_album +=1
            if path == "Default":
                client.download_file(bucket, file['Key'], file['Key'])
                # download_response = client.get_object(Bucket=bucket, Key=file['Key'])
                # with io.FileIO(file['Key'], 'w') as file:
                #     for i in download_response['Body']:
                #         file.write(i)
            else:
                # download_response = client.get_object(Bucket=bucket, Key=file['Key'])
                # with io.FileIO(os.path.join(path, file['Key']), 'w') as file:
                #     for i in download_response['Body']:
                #         file.write(i)
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
def mksite():
    session, client, bucket = create_session()
    print(bucket)

    bucket_policy = {
        'Version': '2012-10-17',
        'Statement': [{
            'Effect': 'Allow',
            'Principal': "*",
            'Action': ['s3:GetObject', 's3:GetObjectVersion', 's3:PutObject',
                       's3:DeleteObject', 's3:DeleteObjectVersion', 's3:GetObjectAcl', 's3:PutObjectAcl','s3:GetBucketWebsite'],
            'Resource': f'arn:aws:s3:::{bucket}/*'
        },{
            'Effect': 'Allow',
            'Principal': "*",
            'Action': ['s3:GetBucketWebsite', 's3:PutBucketWebsite', 's3:ListBucket', 's3:GetObject', 's3:GetObjectVersion', 's3:PutObject',
                       's3:DeleteObject', 's3:DeleteObjectVersion', 's3:GetObjectAcl', 's3:PutObjectAcl','s3:GetBucketWebsite'],
            'Resource': f'arn:aws:s3:::{bucket}'
        }
        ]
    }

    #id = client.get_caller_identity().get('Account')

    bucket_policy = json.dumps(bucket_policy)
    response = client.put_bucket_policy(Bucket=bucket, Policy=bucket_policy)
    print(response)

    website_configuration = {
        'ErrorDocument': {'Key': 'error.html'},
        'IndexDocument': {'Suffix': 'index.html'},
    }

    client.put_bucket_website(Bucket=bucket,
                          WebsiteConfiguration=website_configuration)

    response = client.list_objects(Bucket=bucket)
    print(response)

    albums = []
    for file in response['Contents']:
        if ".jpg" in file['Key'] or ".jpeg" in file['Key']:
            albums.append(file['Key'].split('-')[0])

    print(albums)
    album_list = []
    for i in range(len(albums)):
        if albums[i] in album_list:
            pass
        else:
            album_list.append(albums[i])

    for i in range(len(album_list)):
        img_src_list = []
        img_name_list = []
        for file in response['Contents']:
            name = file['Key'].split('-')[0]
            if album_list[i] == name:
                img_name_list.append(file['Key'])

                try:
                    pre_url = client.generate_presigned_url('get_object',
                                                                Params={'Bucket': bucket,
                                                                        'Key': file['Key']},
                                                                ExpiresIn=950400)
                    pre = f"https://{bucket}.storage.yandexcloud.net/{file['Key']}"
                    img_src_list.append(pre)
                except ClientError as e:
                    sys.stderr.write(e.response)

        with open('album_page.html', 'r') as file:
            html_content = file.read()

        soup = BeautifulSoup(html_content, 'html.parser')

        new_div = soup.new_tag('div')
        new_div['class'] = "galleria"

        for i in range(len(img_src_list)):
            attributes = OrderedDict([
                ('src', img_src_list[i]),
                ('data-title', img_name_list[i])
            ])
            new_img = soup.new_tag('img', **attributes)

            new_div.append(new_img)

        target_location = soup.find('body')

        target_location.insert(1, new_div)

        with open(f'album{i+1}.html', 'w') as output_file:
            output_file.write(str(soup))

        client.upload_file(f'album{i+1}.html', bucket, f'album{i+1}.html')

    with open('index.html', 'r') as file:
        html_content = file.read()

    soup = BeautifulSoup(html_content, 'html.parser')

    new_ul = soup.new_tag('ul')

    for i in range(len(album_list)):
        new_li = soup.new_tag('li')

        attributes = OrderedDict([
            ('href', f'album{i+1}.html')
        ])

        new_a = soup.new_tag('a', **attributes)
        new_a.insert(0, album_list[i])
        new_li.append(new_a)

        new_ul.append(new_li)

    target_location = soup.find('ul')
    target_location.replace_with(new_ul)

    with open('index.html', 'w') as output_file:
        output_file.write(str(soup))

    client.upload_file('index.html', bucket, 'index.html')
    client.upload_file('error.html', bucket, 'error.html')

    print(f'http://{bucket}.website.yandexcloud.net/')

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
    try:
        client.head_bucket(Bucket=bucket1)
    except ClientError:
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
main.add_command(mksite)


if __name__ == '__main__':
    main()

