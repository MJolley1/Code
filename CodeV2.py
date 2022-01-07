import os
import os.path
import time
import threading
import shutil
from datetime import datetime
from time import sleep

from s3cmd import client
from s3cmd import resource
from s3cmd import session

import cv2


# ---------------------------------- READ ME ----------------------------------
# This script is designed for a Windows OS and uploads data to a specified AWS S3 account.
# There are a few inputs that you need to work on before starting the script, these are listed and highlighted below.
# The rest of the script has been written so that it automatically changes everything without any further user input.
# To run this script, you need a second script located with it called "s3cmd.py", which will host your keys for AWS S3.
# You will also need to know things such as your cameras IP address. An alternative script is available for Pi Modules.
# This script was written by Martin Jolley, but a template file for the Pi modules was used that was created by
# Matthew Perks of Newcastle University. Let's begin...#

# ---------------------------------- USER INPUT ----------------------------------

#  Here we define some of the initial parameters, these need changing depending on module type.
saveDest = 'C:\\Users\\LattePanda\\Documents\\Code'  # Where do you want to save the folders and files?
# When changing directory above, be sure to double backstroke each path stage (\\)

#  Here, enter some of the site specifics...
zz = 15  # Enter the number of minutes between capturing videos. Recommended minimum of 15 mins.
siteName = 'trialpanda'  # Enter the name of the site the module is capturing from. Default is 'trial'. DO NOT
# INCLUDE ANY CAPITALS OR SPECIAL CHARACTERS OR IT WILL NOT WORK. keep it lowercase and simple
fps = 20  # What FPS do you want to capture the videos? Minimum and default would be 20fps
capture_duration = 30  # How long do you want to capture the videos for? Minimum advised is about 15-20s, default is 30
# Do you want to be able to see the camera feed as it is recording? 'y' or 'n'
CamFeed = 'n'

#  Define the IP camera's IP address and RTSP port
camAddress = "192.168.1.66:554"  # This default is for my PC. For a pi, set as default "169.254.240.100:554"

# ---------------------------------- DO NOT EDIT THE NEXT LINES ----------------------------------
# All of the following code updates given the user input from above. It will create a "Data" folder in your specified
# area, as well as a backup data folder. All new data will automatically be placed into the Data folder, while any
# data that is in a Data folder when the script is restarted is copied over to the backup folder instead of being
# deleted. It is then subsequently uploaded to AWS along with any new data.

# To help with the naming of files, capture the date and time of script run with the following code:
d = datetime.now()
inityear = "%04d" % d.year
initmonth = "%02d" % d.month
initdate = "%02d" % d.day
inithour = "%02d" % d.hour
initmins = "%02d" % d.minute
initsecs = "%02d" % d.second

# String these together for simplicity...
time_string = inityear + initmonth + initdate + inithour + initmins
buckettocreate = siteName + "-" + time_string  # The bucket name we wish to create is our site name and the time
# the time the script is being ran, gathered from the above lines.

# These are the lines that tell us where we want to put our Data and BackupData folders
# in our save destination specified above.
save_Data = os.path.join(saveDest, "Data")
save_backup = os.path.join(saveDest, 'backupData')

# Create the data and backup folders
os.chdir(saveDest)  # change path to home directory (or where you want it to store)
if os.path.exists('backupData'):  # create a backup for files still in Data folder
    pass  # do nothing
else:  # If the backup folder doesnt exist, then...
    os.makedirs("backupData")  # create the backup folder
if os.path.exists('Data'):  # If the data folder exists, then...
    folderlist = [d for d in os.listdir('Data') if
                  os.path.isdir(os.path.join('Data', d))]  # list the subfolders
    if len(folderlist) > 0:  # If there are more than 0 files in the folder
        for root, dirs, files in os.walk(save_Data):  # for the files in the folder get the names...
            for file in files:  # and for these files....
                path_file = os.path.join(root, file)  # select their pathways...
                shutil.copy2(path_file, 'backupData')  # and copy the files from the Data folder
        shutil.rmtree(save_Data)  # remove the data folder and its now empty sub-folders
        os.makedirs('Data')  # Make a new Data folder
else:  # If the data folder doesn't exist
    os.makedirs('Data')  # Then create the data folder

#  Create the folder to save the files to within the data folder (e.g. sitename+date) and create the buckets on AWS
# ready for our uploading of data.
condition = 1
while condition == 1:
    try:
        # Creating a bucket in AWS S3
        location = {'LocationConstraint': 'eu-west-2'}  # the location of the servers we save to. EU-West-2 is London
        client.create_bucket(
            Bucket=buckettocreate,  # This was defined above as site name and time string
            CreateBucketConfiguration=location
        )
        print('Successfully created bucket.')
        os.chdir(save_Data)  # go to the data folder
        os.makedirs(buckettocreate)  # Create the sub-folder in Data
        sleep(1)
        bucketpathway = save_Data + "\\" + buckettocreate  # Identify the string that takes us to our sub-folder in Data
        bucketcreated = buckettocreate  # Here we rename it as bucketcreated as we are also defining it differently
        # below and we want our code to be consistent later using bucket created
        condition = 2  # arbituary variable but needs to start on 2 to pull us from the loop.
        os.chdir(bucketcreated)  # change to the sub folder directory
    except:  # where there are any errors, do the following lines instead. It simply adds "-b" to avoid duplicates
        print('Name already taken... altering code to accommodate, please wait (30s).')
        buckettocreate2 = buckettocreate + "-b"
        sleep(30)

        # Creating a bucket in AWS S3
        location = {'LocationConstraint': 'eu-west-2'}
        client.create_bucket(
            Bucket=buckettocreate2,
            CreateBucketConfiguration=location
        )
        print('Name has been changed to successfully create the bucket. Please see', buckettocreate2,
              ' to see the created bucket')
        os.chdir(save_Data)
        os.makedirs(buckettocreate2)
        bucketpathway = save_Data + "\\" + buckettocreate2
        bucketcreated = buckettocreate2
        condition = 2
        os.chdir(bucketcreated)

def ipcamera():
    global camAddress
    global bucketcreated
    global bucketpathway
    global saveDest
    global fps
    global siteName
    global zz
    global CamFeed
    global fps
    global capture_duration
    while True:
        os.chdir(saveDest)
        print('Starting ip camera')
        # Create a VideoCapture object
        cap = cv2.VideoCapture("rtsp://" + "admin:password11@" + camAddress + "/channel2")  #  define where to find
        # the IP camera to begin capturing video
        if cap.isOpened() == False:   # Check if camera opened successfully
            print("Unable to read camera feed")

# Redefine the time to get upto date stamps for each video
        e = datetime.now()
        inityear2 = "%04d" % e.year
        initmonth2 = "%02d" % e.month
        initdate2 = "%02d" % e.day
        inithour2 = "%02d" % e.hour
        initmins2 = "%02d" % e.minute
        initsecs = 0

        time_string2 = inityear2 + initmonth2 + initdate2 + inithour2 + initmins2  # again, string it together
        tempname = "Temp" + siteName + '.avi'  # the name of our videos with be the site, the time, and in the
        # .avi format for videos

        # Default resolutions of the frame are obtained.The default resolutions are system dependent.
        # We convert the resolutions from float to integer.
        frame_width = int(cap.get(3))
        frame_height = int(cap.get(4))

        # Define the codec and create VideoWriter object.The output is stored in 'filename.avi' file.
        out = cv2.VideoWriter(tempname, cv2.VideoWriter_fourcc('M', 'J', 'P', 'G'), fps, (frame_width, frame_height))
        # here we redefine the videos from .avi to .mjpg

        start_time = time.time()
        while int(time.time() - start_time) < capture_duration:
            ret, frame = cap.read()
            if ret == True:
                # Write the frame into the file 'filename'
                out.write(frame)
                if CamFeed == 'y':
                    # Display the resulting frame
                    cv2.imshow('frame', frame)
                else:
                    pass
                # Press Q on keyboard to stop recording
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break
                pass
        # When everything done, release the video capture and video write objects
        cap.release()
        out.release()
        # Closes all the frames
        cv2.destroyAllWindows()

        f = datetime.now()
        initsecs2 = "%02d" % f.second
        bias = int(initsecs2) - initsecs  # Calculate the timing bias
        print('IP camera Exiting')
        filename = siteName + time_string2 + '.avi'
        oldpath = os.path.join(saveDest, tempname)
        print(oldpath, "is the oldpath")
        if os.path.exists(oldpath):
            print(oldpath, "name of old path")
            newfilename = os.path.join(bucketpathway, filename)
            print(newfilename, "newfile name")
            shutil.copy(oldpath, newfilename)
            os.remove(tempname)
        else:
            print("No temp video files to exchange, continuing.")
        time.sleep(zz * 60 - bias)  # Wait zz minutes before next capture minus bias
        # produced during the photo capture to prevent timing drift


AWS_REGION = "eu-west-2"
S3_RESOURCE = resource

sleep(2)
client = client
resource = resource
session = session


# Here I define the process requried to upload a specific file to the AWS servers. This is used in loops to
# upload multiple files
def upload_file(file_name, bucket, object_name=None, args=None):
    if object_name is None:
        object_name = file_name

    client.upload_file(file_name, bucket, object_name, ExtraArgs=args)
    print(f"'{file_name}' has been uploaded to '{bucket}'")


def uploadall():  # Upload data to AWS
    global client
    global bucketcreated
    global resource
    global session
    global save_backup
    global bucketpathway
    counter = 0
    while True:
        print('Starting upload all')
        os.system("ping -n 10 www.google.com > pingresult.txt")  # ping to google and display response
        sizer = os.path.getsize('pingresult.txt')
        os.remove('pingresult.txt')
        if sizer > 0:
            file_list = os.listdir(bucketpathway)  # list the files
            print('file list is:', file_list)
            print('bucket created is:', bucketcreated)

            backupfile_list = os.listdir(save_backup)  # list the files in the backup
            print('backup file list is:', backupfile_list)

            itemstoremove = file_list  # Specify the files being uploaded/deleted
            iter1 = len(itemstoremove)  # Number of files in the directory

            itemstoremove2 = os.listdir(save_backup)  # Specify the files being uploaded/deleted in the backup
            iter2 = len(itemstoremove2)  # Number of files in the directory
            print('Number of items in Data folder:', iter1)
            print('Number of items in backup folder:', iter2)
            sleep(2)


            # Upload new data to AWS servers
            if iter1 == 0:
                pass
            else:
                os.chdir(bucketpathway)
                filenumber = 0
                while filenumber < iter1:
                    sleep(2)
                    file_name = file_list[filenumber]
                    print('filename is: ', file_name)
                    sleep(1)
                    print('Beginning file upload:', file_name)
                    upload_file(file_name, bucketcreated)
                    filenumber = filenumber + 1
                    sleep(3)
                else:
                    print("---------- New data uploaded to AWS ----------")
                    pass

            # Generate the list of files already in the bucket
            s3 = session.resource('s3')
            awsbucket = s3.Bucket(bucketcreated)

            if iter1 > 0:  # if there are files in the Data directory
                for x in range(0, iter1):  # Run this for the number of files in the directory
                    for obj in awsbucket.objects.all():
                        if itemstoremove[x] in obj.key:  # if the item in Data already exists in s3
                            sleep(15)
                            os.remove(itemstoremove[x])  # Remove them one-by-one
                            print(itemstoremove[x], 'has been deleted')
                        else:
                            pass
            else:
                print('nothing to transfer')

            # Upload backup data to AWS servers
            filenumber2 = 0
            if iter2 == 0:
                pass
            else:
                while filenumber2 < iter2:
                    print('Uploading backup files')
                    os.chdir(save_backup)
                    file_name2 = backupfile_list[filenumber2]
                    print('Backup filename being uploaded is:', file_name2)
                    upload_file(file_name2, bucketcreated)
                    filenumber2 = filenumber2 + 1
                else:
                    print("---------- Backup data uploaded to AWS ----------")
                    pass

            if iter2 > 0:
                os.chdir(save_backup)
                for xx in range(0, iter2):  # Remove each of the uploaded files through this loop:
                    for obj2 in awsbucket.objects.all():
                        if itemstoremove2[xx] in obj2.key:  # if the item in Data already exists in s3
                            os.remove(itemstoremove2[xx])  # Remove them one-by-one
                            print('Backup file:', itemstoremove2[xx], 'has been deleted')
                        else:
                            pass
            else:
                print('nothing to transfer')

            print('Exiting upload all')
            sleep(120)  # After a successful sync allow the upload routine to rest for 120 seconds before restarting
            counter = 0  # Reset the counter after success

        else:
            # subprocess.Popen("sudo wvdial",shell=True).wait # Run wvdial incase it has falled over
            print('No internet connection available')
            counter = counter + 1
            sleep(30)

        if counter == 250:
            os.system("shutdown /r")

# Find the next timestamp with a multiple of zz
a = range(0 ,60, zz)
z = int(initmins)
takeClosest = lambda num ,collection:min(collection,key=lambda x:abs(x-num))
startAt = takeClosest(z,a)+zz
if startAt == 60:
    startAt = 0
print('Start at:', startAt)

if 1 <= startAt <= 55:
    y = d.replace(minute=startAt, second =0, microsecond=0)
else:
    y = d.replace(hour=d.hour+1, minute=0, second=0, microsecond=0)

delta_t = y-d
secs = delta_t.seconds+1
print('time until execution:', secs) # Number of seconds until program executes
time.sleep(secs)

# Created threads:

thread1 = threading.Thread(name='ipcamera', target=ipcamera)
thread2 = threading.Thread(name='uploadall', target=uploadall)

# Uncomment to run threads:
thread1.start()
thread2.start()
thread2.join()

print("Exiting main thread")
