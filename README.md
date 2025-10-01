# DBT-group6

## Description

This repo is for group 6 in the course 'Design-Build-Test'. It is used to develop and maintain the python scripts for laser speckle imaging. 


## Camera 
Link to camera CS895CU
https://www.thorlabs.com/thorproduct.cfm?partnumber=CS895CU

## Setup and installing Thorlabs camera package
Navigate to the folder /main script and create your own virtual environment:
```
python -m venv venv
```
This is a container for the project so we only have the desired packages downloaded. 
Start by activating/deactivating it:
```
.venv\Scripts\activate.ps1
.venv\Scripts\deactivate.ps1
```
Change .ps1 for .bat if on CMD and not powershell.
After this we can general packages defined in a text file ```package_requirements.txt```, and also Thorlabs camera package.
```
python -m install -r ./package_requirements.txt
```
The thorlabs package can be installed online. 
Note: Thorlabs programming interface package is difficult to upload to GitLab. It can be downloaded 
at 
- [ ] https://www.thorlabs.com/software_pages/ViewSoftwarePage.cfm?Code=ThorCam

Select the tab "Programming Interfaces" at the bottom of the page, select "Windows SDK and Doc. for Scientific Cameras" and press download from the drop-down.
Now to install the thorlabs python package, first go to Scientific Camera Interfaces -> SDK -> Python Toolkit and unzip thorlabs_tsi_camera_python_sdk_package. In your terminal, having .venv activated, navigate to ```\Scientific Camera Interfaces\SDK\Python Toolkit\thorlabs_tsi_camera_python_sdk_package\thorlabs_tsi_sdk-0.0.8```. Install the package by entering:
```
python -m install -e .
```

The package also requires dll files. The folders in "dlls" at ```Scientific Camera Interfaces\SDK\Python Toolkit\dlls``` are empty from download. Luckily those files are provided at ```Scientific_Camera_Interfaces_Windows-2.1\Scientific Camera Interfaces\SDK\Native Toolkit\dlls```. "dlls" itself contains two folders, one for 32-bit and the other for 64-bit. The files you are looking for are most likely in "64_lib", but you can always copy all files from both folders. Copy all files and paste them to the relevant folder at ```Scientific Camera Interfaces\SDK\Python Toolkit\dlls```.

The path to these folders are given in ```main.py``` and we recommend to keep the ```Scientific Camera Interface``` package in there too (same as venv), but the path can be changed by the user too. 
Please dont try to push the Thorlabs package or your own venv to this git.
Now there should be no problem starting the program by writing:
```
python main.py 
```




