from django.shortcuts import render, redirect
from django.contrib import messages 
import boto3
from .forms import FileDeletionForm

s3_client = boto3.client('s3',region_name='us-east-2')
iam_client = boto3.client('iam')

#Bucket Creation
def create_bucket(request):
    regions = [
        'us-east-2',
        'us-west-1',
        'us-west-2',
        'eu-west-1',
        'eu-west-2']
    if request.method == 'POST':
        bucket_name = request.POST.get('bucket_name')
        region = request.POST.get('region')
        action = request.POST.get('action')

        if action == 'create_bucket':
            try:
                if region == '':
                    s3_client.create_bucket(Bucket=bucket_name)
                else:
                    s3_client = boto3.client('s3',region_name=region)
                    location = {'LocationConstraint':region}
                    s3_client.create_bucket(Bucket=bucket_name,CreateBucketConfiguration=location)
                messages.success(request, f'Successfully created bucket "{bucket_name}"')
            except Exception as e:
                messages.error(request, f'Failed to create bucket: {str(e)}')

    return render(request, 'create_bucket.html',{'regions':regions})


#Bucket Deletion
def delete_bucket(request):
    if request.method == 'POST':
        bucket_name = request.POST.get('bucket_name')
        action = request.POST.get('action')
        if action == 'delete_bucket' and bucket_name:
            try:
                s3_client.delete_bucket(Bucket=bucket_name)
                messages.success(request, f'Successfully deleted bucket "{bucket_name}"')
            except Exception as e:
                messages.error(request, f'Failed to delete bucket: {str(e)}')

    buckets = s3_client.list_buckets()['Buckets']

    return render(request, 'list_buckets.html', {'buckets': buckets})

#Listing buckets
def list_buckets(request):
    buckets = s3_client.list_buckets()['Buckets']
    return render(request, 'list_buckets.html', {'buckets': buckets})


#Uplaoding files
def upload_file(request):
    s3_client = boto3.client('s3')

    folders = []
    
    if request.method == 'POST':
        selected_bucket = request.POST.get('selected_bucket')

        try:
            list_objects_response = s3_client.list_objects_v2(Bucket = selected_bucket,Delimiter='/')
            if 'CommonPrefixes' in list_objects_response:
                folders = [prefix['Prefix'] for prefix in list_objects_response['CommonPrefixes']]
        except Exception as e:
            messages.error(request,f'Error listing folders: {str(e)}')
        
        try:
            s3_client.head_bucket(Bucket=selected_bucket)

            if request.FILES['file']:
                file_to_upload = request.FILES['file']
                folder_path = request.POST.get('folder_path','')
                key = folder_path + file_to_upload.name
                s3_client.upload_fileobj(file_to_upload, selected_bucket, key)
                messages.success(request, f'Successfully uploaded file "{key}" to bucket "{selected_bucket}"')
        except Exception as e:
            messages.error(request, f'Failed to upload file: {str(e)}')

    response = s3_client.list_buckets()
    buckets = [bucket['Name'] for bucket in response['Buckets']]

    return render(request, 'upload_file.html', {'buckets': buckets, 'folders':folders})


#Deleting File
def delete_files(request):
    buckets = {}

    if request.method == 'POST':
        action = request.POST.get('action')

        if action:
            bucket_name, file_key = action.split(' | ')

            try:
                s3_client.head_bucket(Bucket = bucket_name)

                s3_client.delete_object(Bucket = str(bucket_name), Key = str(file_key))
                messages.success(request,f'Successfully deleted file "{file_key}" from bucket "{bucket_name}"')

            except Exception as e:
                messages.error(request,f'Error deleting file "{file_key}" from bucket "{bucket_name}":{str(e)}')
    
    try:
        response = s3_client.list_buckets()
        for bucket in response['Buckets']:
            bucket_name = bucket['Name']
            objects_response = s3_client.list_objects_v2(Bucket=bucket_name)
            files = [obj['Key'] for obj in objects_response.get('Contents',[])]
            buckets[bucket_name] = files
    except Exception as e:
        messages.error(request, f'Error fetching bucket names and files: {str(e)}')

    return render(request, 'delete_files.html',{'buckets':buckets})


#Files Listing
def list_files(request):
    files = []

    if request.method == 'POST':
        bucket_name = request.POST.get('bucket_name')
        action = request.POST.get('action')

        if action == 'list_files' and bucket_name:

            try:
                s3_client.head_bucket(Bucket=bucket_name)

                response = s3_client.list_objects_v2(Bucket = bucket_name)
                files = [obj['Key'] for obj in response.get('Contents',[])]

                if not files:
                    messages.error(request,f'No files in the selected bucket')
                
            except Exception as e:
                messages.error(request,f'Error')
    
    try:
        response = s3_client.list_buckets()
        buckets = [(bucket['Name'], bucket['Name']) for bucket in response['Buckets']]
    except Exception as e:
        buckets = []
        messages.error(request,f'Error: {str(e)}')

    
    return render(request,'list_files.html',{'files':files, 'buckets':buckets})


#Copy Files
def copy_files(request):
    action = request.POST.get('action')
    buckets = s3_client.list_buckets()['Buckets']
    bucket_names = [bucket['Name'] for bucket in buckets]

    source_files = []
    source_bucket = request.POST.get('source_bucket')

    if request.method == 'POST':
        destination_bucket = request.POST.get('destination_bucket')
        selected_files = request.POST.getlist('selected_files')

        if action == 'get_files':
            selected_bucket = request.POST.get('source_bucket')

            request.POST = request.POST.copy()
            request.POST['selected_bucket'] = selected_bucket
            if source_bucket:
                try:
                    source_objects = s3_client.list_objects_v2(Bucket = str(selected_bucket))


                    if 'Contents' in source_objects:
                        source_files = [obj['Key'] for obj in source_objects['Contents']]
                    else:
                        messages.warning(request,f'{source_bucket} is empty. No files to copy')
                except Exception as e:
                    messages.error(request,f'Error listing files: {str(e)}')
        
        elif action == 'copy_files':
            selected_bucket = request.POST.get('selected_bucket')
            if not selected_files:
                messages.warning(request,'No files selected for copying')
            else:
                try:
                    for file_key in selected_files:
                        s3_client.copy_object(
                        CopySource = {'Bucket':selected_bucket, 'Key':str(file_key)},
                        Bucket=destination_bucket,
                        Key = str(file_key)
                        )
                    messages.success(request,f'Selected files copied from {selected_bucket} to {destination_bucket}')

                except Exception as e:
                    messages.error(request,f'Error copying files: {str(e)}')
    
    return render(request,'copy_files.html',{'buckets':bucket_names,'source_files':source_files,'source_bucket':source_bucket})


#Move Files
def move_files(request):
    action = request.POST.get('action')
    buckets = s3_client.list_buckets()['Buckets']
    bucket_names = [bucket['Name'] for bucket in buckets]

    source_files = []
    source_bucket = request.POST.get('source_bucket')

    if request.method == 'POST':
        destination_bucket = request.POST.get('destination_bucket')
        selected_files = request.POST.getlist('selected_files')


        if action == 'get_files':
            try:
                source_objects = s3_client.list_objects_v2(Bucket = source_bucket)


                if 'Contents' in source_objects:
                    source_files = [obj['Key'] for obj in source_objects['Contents']]
                else:
                    messages.warning(request,f'{source_bucket} is empty. No files to move')
            except Exception as e:
                messages.error(request,f'Error listing files: {str(e)}')
        
        elif action == 'move_files':
            selected_bucket = request.POST.get('selected_bucket')
            if not selected_files:
                messages.warning(request,'No files selected for moving')
            else:
                try:
                   for file_key in selected_files:
                        s3_client.copy_object(
                            CopySource = {'Bucket':selected_bucket, 'Key':str(file_key)},
                            Bucket=destination_bucket,
                            Key = str(file_key)
                        )
                        s3_client.delete_object(Bucket=str(selected_bucket), Key=str(file_key))

                        messages.success(request,f'Selected files moved from {selected_bucket} to {destination_bucket}')

                except Exception as e:
                    messages.error(request,f'Error moving files: {str(e)}')
    
    return render(request,'move_files.html',{'buckets':bucket_names,'source_files':source_files, 'source_bucket':source_bucket})


#Folder Creation
def create_folder(request):
    buckets = s3_client.list_buckets()['Buckets']
    bucket_names = [bucket['Name'] for bucket in buckets]

    if request.method == 'POST':
        selected_bucket = request.POST.get('selected_bucket')
        folder_name = request.POST.get('folder_name')

        try:
            if not folder_name.endswith('/'):
                folder_name += '/'

            s3_client.put_object(Bucket = selected_bucket, Key = folder_name)

            messages.success(request,f'Folder "{folder_name}" created in {selected_bucket}')
        
        except Exception as e:
            messages.error(request, f'Error creating folder: {str(e)}')
    
    return render(request, 'create_folder.html',{'buckets':bucket_names})