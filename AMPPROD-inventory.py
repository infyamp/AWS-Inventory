import boto3  
import collections  
import datetime  
import csv  
from time import gmtime, strftime 
import smtplib  
from email.MIMEMultipart import MIMEMultipart  
from email.MIMEBase import MIMEBase  
from email.MIMEText import MIMEText  
from email import Encoders  
import os
import re

#EC2 connection beginning
ec = boto3.client('ec2')  
#S3 connection beginning
s3 = boto3.resource('s3')

#lambda function beginning
def lambda_handler(event, context):  
    #get to the curren date
    date_fmt = strftime("%Y_%m_%d", gmtime())
    timestamp = datetime.datetime.now()
    #Give your file path
    filepath ='/tmp/AMPPRD_AWS_Resources_' + date_fmt + '.csv'
    #Give your filename
    filename ='AMPPRD_AWS_Resources_' + date_fmt + '.csv'
    csv_file = open(filepath,'w+')
    instanceid = 'null'
    VolumeId='null'
    instancetype = ''
    launchtime = ''
    Placement = ''
    instancecc = ''
    Instancename= ''
    VolumeName = ''
    VolumeCostCenter = ''
    State=''
    #Platform=''
    IP=''
    #boto3 library ec2 API describe region page
    #http://boto3.readthedocs.org/en/latest/reference/services/ec2.html#EC2.Client.describe_regions
    regions = ec.describe_regions().get('Regions',[] )
    for region in regions:
        reg=region['RegionName']
        regname='REGION :' + reg
        #EC2 connection beginning
        ec2con = boto3.client('ec2',region_name=reg)
        #boto3 library ec2 API describe instance page
        #http://boto3.readthedocs.org/en/latest/reference/services/ec2.html#EC2.Client.describe_instances
        reservations = ec2con.describe_instances().get(
        'Reservations',[] 
        )
        instances = sum(
            [
                [i for i in r['Instances']]
                for r in reservations
            ], [])
        instanceslist = len(instances)
        
        if instanceslist > 0:
            csv_file.write("%s,%s,%s,%s,%s,%s\n"%('','','','','',''))
            csv_file.write("%s,%s,%s,%s,,%s,%s\n"%('EC2 INSTANCE',regname,'','','TIMESTAMP:',timestamp))
            csv_file.write("%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s\n"%('HostName','IP','InstanceID','Instance_Type','Instance_CostCenter','AWSAccount','Zone','inSupportScope?','Application','AMPPortfolio','Owner','OS','ManagedThroughCEH?','Instance_Placement','Instance_State','LaunchTime'))
        #    csv_file.write("%s,%s,%s,%s,%s,%s,%s\n"%('InstanceID','Instance_State','InstanceName','Instance_Type','LaunchTime','Instance_Placement','Instance_CostCenter'))
            csv_file.flush()

        for instance in instances:
            state=instance['State']['Name']
            if state =='running' or state == 'stopped' :
                instanceid=instance['InstanceId']
                instancetype=instance['InstanceType']
                launchtime =instance['LaunchTime']
                Placement=instance['Placement']['AvailabilityZone']
                IP=instance['PrivateIpAddress']
               # Platform=instance['Platform']
                if 'Tags' in instance :
                    for tags in instance['Tags']:
                        key= tags['Key']
                        if key == 'Name' :
                            Instancename= tags['Value']
                        if key == 'Cost Center' :
                            instancecc= tags['Value']
                            if 'TF 820' in instancecc :
                                instancecc = 'TF 820 - CEH'
                if instanceid != 'null' :
                    csv_file.write("%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s\n"% (Instancename,IP,instanceid,instancetype,instancecc,'','','','','','','','Yes',Placement,state,launchtime))
                    csv_file.flush()


        #boto3 library ec2 API describe volumes page
        #http://boto3.readthedocs.org/en/latest/reference/services/ec2.html#EC2.Client.describe_volumes
        ec2volumes = ec2con.describe_volumes().get('Volumes',[])
        volumes = sum(
            [
                [i for i in r['Attachments']]
                for r in ec2volumes
            ], [])
        volumeslist = len(volumes)
        if volumeslist > 0:
            csv_file.write("%s,%s,%s,%s\n"%('','','',''))
            csv_file.write("%s,%s\n"%('EBS Volume',regname))
            csv_file.write("%s,%s,%s,%s,%s,%s,%s,%s,%s,%s\n"%('VolumeId','InstanceId','AttachTime','State','VolumeType', 'Size', 'Encrypted','VolumeName', 'VolumeCostCenter','State'))             
            csv_file.flush()

        for volumeD in ec2volumes:
            #print volumeD
            for volume in volumeD['Attachments']:
                AttachTime=volume['AttachTime'] 
                InstanceId=volume['InstanceId']
                VolumeId=volume['VolumeId']
                State=volume['State']
            if 'Tags' in volumeD :
                for tags in volumeD['Tags']:
                    key= tags['Key']
                    if key == 'Name' :
                        VolumeName= tags['Value']
                        #print VolumeName
                    if key == 'Cost Center' :
                        VolumeCostCenter= tags['Value']
                        if 'TF 820' in VolumeCostCenter :
                            VolumeCostCenter = 'TF 820 - CEH'
            VolumeType=volumeD['VolumeType']
            Size=volumeD['Size']
            Encrypted=volumeD['Encrypted']
            state=volumeD['State']
            if state == 'available':
                VolumeId= volumeD['VolumeId']
                AttachTime= ' '
                State= ' '
                InstanceId= ' '  
            csv_file.write("%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,\n" % (VolumeId,InstanceId,AttachTime,State,VolumeType,Size,Encrypted,VolumeName,VolumeCostCenter,state)) 
            csv_file.flush()
            VolumeId = ''
            InstanceId=''
            AttachTime=''
            State=''
            VolumeType=''
            Size=''
            Encrypted=''
            VolumeName=''
            VolumeCostCenter=''
            state=''
            
                
        #Give your owner ID
        account_ids=''    
        #boto3 library ec2 API describe snapshots page
        #http://boto3.readthedocs.org/en/latest/reference/services/ec2.html#EC2.Client.describe_snapshots
        ec2snapshot = ec2con.describe_snapshots(OwnerIds=[
            account_ids,
        ],).get('Snapshots',[])
        ec2snapshotlist = len(ec2snapshot)
        if ec2snapshotlist > 0:
            csv_file.write("%s,%s,%s,%s\n" % ('','','',''))
            csv_file.write("%s,%s\n"%('EC2 SNAPSHOT',regname))
            csv_file.write("%s,%s,%s,%s\n" % ('SnapshotId','VolumeId','StartTime','VolumeSize'))
            csv_file.flush()

        for snapshots in ec2snapshot:
            SnapshotId=snapshots['SnapshotId']
            VolumeId=snapshots['VolumeId']
            StartTime=snapshots['StartTime']
            VolumeSize=snapshots['VolumeSize']
            csv_file.write("%s,%s,%s,%s\n" % (SnapshotId,VolumeId,StartTime,VolumeSize))
            csv_file.flush()   

        #boto3 library ec2 API describe addresses page    
        #http://boto3.readthedocs.org/en/latest/reference/services/ec2.html#EC2.Client.describe_addresses
        addresses = ec2con.describe_addresses().get('Addresses',[] )
        addresseslist = len(addresses)
        if addresseslist > 0:
            csv_file.write("%s,%s,%s,%s,%s\n"%('','','','',''))
            csv_file.write("%s,%s\n"%('EIPS INSTANCE',regname))
            csv_file.write("%s,%s,%s\n"%('PublicIp','AllocationId','Domain'))
            csv_file.flush() 
            for address in addresses:
                PublicIp=address['PublicIp']
                AllocationId=address['AllocationId']
                Domain=address['Domain']
                csv_file.write("%s,%s,%s\n"%(PublicIp,AllocationId,Domain))
                csv_file.flush() 

        #RDS Connection beginning    
        rdscon = boto3.client('rds',region_name=reg)

        #boto3 library RDS API describe db instances page    
        #http://boto3.readthedocs.org/en/latest/reference/services/rds.html#RDS.Client.describe_db_instances
        rdb = rdscon.describe_db_instances().get(
        'DBInstances',[] 
        )
        rdblist = len(rdb)
        if rdblist > 0:
            csv_file.write("%s,%s,%s,%s\n" %('','','',''))
            csv_file.write("%s,%s\n"%('RDS INSTANCE',regname))
            csv_file.write("%s,%s,%s,%s\n" %('DBInstanceIdentifier','DBInstanceStatus','DBName','DBInstanceClass'))
            csv_file.flush()

        for dbinstance in rdb:
            DBInstanceIdentifier = dbinstance['DBInstanceIdentifier']
            DBInstanceClass = dbinstance['DBInstanceClass']
            DBInstanceStatus = dbinstance['DBInstanceStatus']
            DBName = dbinstance['DBName']
            csv_file.write("%s,%s,%s,%s\n" %(DBInstanceIdentifier,DBInstanceStatus,DBName,DBInstanceClass))
            csv_file.flush()

       
    
    date_fmt = strftime("%Y_%m_%d", gmtime())
    #Give your file path
    filepath ='/tmp/AMPPRD_AWS_Resources_' + date_fmt + '.csv'
    #Give your filename
    #mail("chandan_choudhury@amp.com.au", "cloudops@amp.com.au", "PFA for the AWS resource of cloudops account.", "AWS Inventory attached!", filepath)
    s3.Object('cloudops-inventory-ampprd', filename).put(Body=open(filepath, 'rb'))
