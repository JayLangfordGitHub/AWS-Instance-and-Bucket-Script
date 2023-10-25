import boto3
import time
import webbrowser
import uuid
import json
import subprocess
import requests
import random
import string

def write_urls_to_file(ec2_url, s3_url):
    # Writes the given EC2 and S3 URLs to a specified file
    filename = "jlangford-websites.txt" # Adjust as per your first initial and last name
    with open(filename, 'w') as file:
        file.write(f"EC2 URL: {ec2_url}\n") 
        file.write(f"S3 Bucket URL: {s3_url}\n")
    print(f"URLs written to {filename}")

def open_browser_with_http(url):
    # Opens the given URL in a browser tab
    print(f"Attempting to open URL: {url} ...")
    try:
        webbrowser.open(url, new=2)  # new=2 means open in a new tab, if possible
    except Exception as e:
        print(f"Failed to open the URL: {e}")

def wait_for_instance_status_checks(instance_id, max_retries=15, sleep_interval=20):
    # Waits for the EC2 instance to pass status checks
    print("Waiting for instance status checks...")
    ec2_client = boto3.client('ec2')

    retries = 0
    while retries < max_retries:
        response = ec2_client.describe_instance_status(InstanceIds=[instance_id])
        status_checks = response['InstanceStatuses']

        if status_checks and status_checks[0]['InstanceStatus']['Status'] == 'ok' and status_checks[0]['SystemStatus']['Status'] == 'ok':
            print("Instance passed status checks!")
            return True

        retries += 1
        print(f"Retry #{retries}...")
        time.sleep(sleep_interval)
    print("Instance failed to pass status checks within the expected time.")
    return False

def create_ec2_instance():
    # Creates an EC2 instance and returns its URL
    print("Creating EC2 instance...")
    # AWS configuration and user data to install and configure Apache on EC2
    ec2 = boto3.resource('ec2', region_name='us-east-1') # Adjust per your region
    user_data_script = """#!/bin/bash
    yum update -y
    yum install httpd -y
    systemctl enable httpd
    systemctl start httpd

    # Fetch EC2 instance metadata
    INSTANCE_ID=$(curl -s http://169.254.169.254/latest/meta-data/instance-id)
    INSTANCE_TYPE=$(curl -s http://169.254.169.254/latest/meta-data/instance-type)
    AVAILABILITY_ZONE=$(curl -s http://169.254.169.254/latest/meta-data/placement/availability-zone)

    # Create index.html with metadata information
    cat <<EOL > /var/www/html/index.html
    <html>
    <head>
    <title>EC2 Metadata</title>
</head>
<body>
    <h1>Welcome to my EC2 Instance!</h1>
    <p>Instance ID: $INSTANCE_ID</p>
    <p>Instance Type: $INSTANCE_TYPE</p>
    <p>Availability Zone: $AVAILABILITY_ZONE</p>
</body>
</html>
EOL
"""
    instance = ec2.create_instances(
        ImageId='ami-00c6177f250e07ec1',
        MinCount=1,
        MaxCount=1,
        InstanceType='t2.nano',
        KeyName='Boto3Week4KeyPair', # Adjust per your key pair
        SecurityGroupIds=['sg-00c7ffd6f993bca5e'], # Adjust per your security group
        UserData=user_data_script,
        TagSpecifications=[
            {
                'ResourceType': 'instance',
                'Tags': [
                    {
                        'Key': 'Name',
                        'Value': 'Assignment1' #Adjust per your desired instance name
                    }
                ]
            }
        ]
    )
    print(f'Created instance {instance[0].id}')
   
    # Wait for instnace to run
    ec2_client = boto3.client('ec2')
    waiter = ec2_client.get_waiter('instance_running')
    waiter.wait(InstanceIds=[instance[0].id])
   
    print("Instance Running.")
   
    # Wait for EC2 instance status checks to pass
    if not wait_for_instance_status_checks(instance[0].id):
        print("Error: Instance didn't pass status checks. Exiting.")
        return

    print("Waiting for the Apache server to start...")
    time.sleep(30)
   
    # Open new tab
    instance[0].reload()
    ec2_instance_url = f'http://{instance[0].public_dns_name}'
    print(f"EC2 instance creation completed. URL: {ec2_instance_url}")

    return ec2_instance_url


def random_string(length=6):
    # Generate a random string of given length
    print("Generating a random string...")
    letters = string.ascii_lowercase
    return ''.join(random.choice(letters) for i in range(length))
    print("Random string generation completed.")

def create_s3_bucket_and_setup_website():
    # Creates an S3 bucket, sets it up as a website, and returns its URL
    print("Starting S3 bucket creation and setup...")
    try:
        # Generate bucket name
        print("Generating bucket name...")
        first_initial = "j"  # Adjust as per your first initial
        last_name = "langford"  # Adjust as per your last name
        random_chars = random_string(6)
        bucket_name = f"{random_chars}-{first_initial}{last_name}"

        # Create bucket
        print("Creating S3 bucket...")
        s3 = boto3.resource('s3', region_name='us-east-1')
        s3.create_bucket(Bucket=bucket_name)
        
        # Download image
        print("Downloading image for S3 bucket...")
        image_url = "http://devops.witdemo.net/logo.jpg"
        image_response = requests.get(image_url)
        image_key = "logo.jpg"
        s3.Bucket(bucket_name).put_object(Key=image_key, Body=image_response.content)

        # Create index.html with the image
        print("Creating index.html with image for S3 bucket...")
        index_html_content = """
        <html>
            <body>
                <img src='logo.jpg' alt='Logo'>
            </body>
        </html>
        """
        s3.Bucket(bucket_name).put_object(Key='index.html', Body=index_html_content, ContentType='text/html')

        # Static website hosting configuration
        print("Setting up static website hosting for S3 bucket...")
        website_configuration = {
            'ErrorDocument': {'Key': 'error.html'},
            'IndexDocument': {'Suffix': 'index.html'},
        }
        bucket_website = s3.BucketWebsite(bucket_name)
        bucket_website.put(WebsiteConfiguration=website_configuration)
        
        # Allow public access
        print("Setting up public access for S3 bucket...")
        s3client = boto3.client("s3")
        s3client.delete_public_access_block(Bucket=bucket_name)
   
        # Bucket policy for public read access
        bucket_policy = {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Sid": "PublicReadGetObject",
                    "Effect": "Allow",
                    "Principal": "*",
                    "Action": ["s3:GetObject"],
                    "Resource": f"arn:aws:s3:::{bucket_name}/*"
                }
            ]
        }
        s3.Bucket(bucket_name).Policy().put(Policy=json.dumps(bucket_policy))

        s3_bucket_website_url = f"http://{bucket_name}.s3-website-us-east-1.amazonaws.com"
        print(f"Bucket {bucket_name} created successfully. Website URL: {s3_bucket_website_url}")
        
        return s3_bucket_website_url
    except Exception as e:
        print(f"An error occurred during S3 bucket creation/setup: {str(e)}")
        return None

def main():
    # Main function to orchestrate EC2 and S3 resource creation
    print("Script starting...")
    
    # Create and open EC2 instance in the browser
    ec2_instance_url = create_ec2_instance()
    if ec2_instance_url:
        open_browser_with_http(ec2_instance_url)

    # Create S3 bucket and open it in the browser
    s3_bucket_url = create_s3_bucket_and_setup_website()
    if s3_bucket_url:
        open_browser_with_http(s3_bucket_url)
        
    # Write the URLs to the specified file
    if ec2_instance_url and s3_bucket_url:
        write_urls_to_file(ec2_instance_url, s3_bucket_url)

    print("Script execution completed.")

if __name__ == "__main__":
    main()
