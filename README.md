# EC2 and S3 Website Creation Script

SETU BSc (Hons) in Computer Science (Cloud &amp; Networks) Year 3 Semester 1 Developer Operations Assignment 1

This script automates the creation of an Amazon EC2 instance and an Amazon S3 bucket, and sets up both as simple websites. The EC2 instance is configured with an Apache server, and the S3 bucket is setup as a static website.

## Prerequisites

- **Python**
- **boto3** 

## How to Use

- Clone the repository using the command **git clone https://github.com/JayLangfordGitHub/AWS-Instance-and-Bucket-Script**
- Run the script using the command **python3 devops_1.py**

## Customizations
This script contains several comments that allow users to customize specific data as per their requirements. For instance:

- **Instance Name:** Adjust the instance name as per your requirements.
- **First Initial and Last Name:** Adjust these values for filename and S3 bucket naming purposes.
- **Region:** Adjust the region to the AWS region you want to operate in.
- **Key Pair:** Adjust the name of the key pair to be used for the EC2 instance.
- **Security Group:** Adjust the security group ID for your EC2 instance.
Make sure to go through the script and look for comments, which will guide you on what and where to adjust.

## Features
- Creates an EC2 instance, installs and configures Apache, and then displays metadata information.
- Creates an S3 bucket, sets it up as a static website, and displays a logo image.
- Opens both the EC2 instance and S3 bucket in the default web browser.
- Writes the URLs of both the EC2 instance and S3 bucket to a specified file.

