# Social Robotics - Training with Seniors Using NAO Robot

Functionality focused on training with elderly people using Nao robot and various technologies







## Docker Integration

The orchestrated functionality can be run using docker compose and each standalone application using Docker


run:  

```docker compose up --build```





## Developer Section





### Windows  



- Download Ubuntu 18.04 version (last version supporting python2.7-dev library using apt + runs fast on Windows and does not contain some bugs (problems with drawn folders inside))

&nbsp;	-open https://releases.ubuntu.com/18.04/

&nbsp;	-download iso image called ubuntu-18.04.6-desktop-amd64.iso

- Download and Install VirtualBox latest version (https://www.virtualbox.org/wiki/Downloads)

- Download VirtualBox Guest Addons to share files and commands (https://download.virtualbox.org/virtualbox/7.1.12/ ->  VBoxGuestAdditions\_7.1.12.iso)

&nbsp;	- open iso and run proper installer

- Install Ubuntu on VirtualBox

&nbsp;	- open VirtualBox

&nbsp;	- click new

&nbsp;	- choose iso image of Ubuntu 18.04

&nbsp;	- fill name and do not forget to hit Skip Unattended Installation (makes problems such as problems accessing root user, etc.)

&nbsp;	- set amount of RAM, number of processors, and space to allocate

&nbsp;	- wait for installation to complete

&nbsp;	![Installing Ubuntu](https://github.com/jperdek/socialRobotEnv/tree/master/documentation/windowsTutorial/virtualBoxUbuntuInstall.png)

- Log In to Ubuntu

- Install Guest Additions on guest Ubuntu (on upper panel click devices -> insert image with guest additions)

&nbsp;	- allow Ubuntu to install them

&nbsp;	![VirtualBox Guest Additions for Ubuntu guest operating system](https://github.com/jperdek/socialRobotEnv/tree/master/documentation/windowsTutorial/installingGuestAdditionsOnGuestUbuntu.png)



- Hit Ctrl + T or open terminal

&nbsp;	-run Python installation using command

&nbsp;	```sudo apt-get update	&& apt-get install -y wget python-pip python2.7-dev gcc make openssl libffi-dev libgdbm-dev libsqlite3-dev libssl-dev zlib1g-dev && apt-get clean ```

&nbsp;	-copy pynaoqi library (https://github.com/AnonKour/pynaoqi) to /pynaoqi

&nbsp;		```sudo apt-get install git```

&nbsp;		```git clone git@github.com:AnonKour/pynaoqi.git```

&nbsp;		```cp ./pynaoqi /```

&nbsp;	-make libraries dependent on Linux available with Python2.7:

&nbsp;	``` export PYTHONPATH=${PYTHONPATH}:/pynaoqi```

- Download this repo into Windows (in my case it is E:\\robotics)

- Share folder with this repo on Windows with installed Ubuntu running on VirtualBox (in my case /robotics)

&nbsp;	- In VirtualBox click on image with Ubuntu

&nbsp;	- Click Settings

&nbsp;	- Scroll down to Shared Folders

&nbsp;	- Click add shared folder under machine folders

&nbsp;	- Set paths and confirm

&nbsp;	![Shared folder in VirtualBox configuration](https://github.com/jperdek/socialRobotEnv/tree/master/documentation/windowsTutorial/configuringSharedFolder.png)

- Open Ubuntu and switch to sudo to access shared folder using ```sudo su``` command

&nbsp;	![Shared folder on Ubuntu command line](https://github.com/jperdek/socialRobotEnv/tree/master/documentation/windowsTutorial/roboticsFolder.png) 

- Make modifications on Windows and Run Apps on Ubuntu (Linux)



![My VirtualBox configuration for Ubuntu 18.04 image](https://github.com/jperdek/socialRobotEnv/tree/master/documentation/windowsTutorial/myConfiguration.png)



&nbsp; 









