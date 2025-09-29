The python script added uses ThorLabs python package and should be included in the folder named "Scientific_Camera_Interfaces_Windows-2.1".

Note: Thorlabs programming interface package is difficult to upload to GitLab. It can be downloaded 
at "https://www.thorlabs.com/software_pages/ViewSoftwarePage.cfm?Code=ThorCam". Select the tab "Programming Interfaces" at the bottom of the page, select "Windows SDK and Doc. for Scientific Cameras" and press download from the drop-down.

The current setup I use has the folder "Scientific_Camera_Interfaces_Windows-2.1" at the same level as "python_code_test". The importance of this is explained in later steps.

If the folder "python_code_test" does not contain a folder called ".venv", make sure to make one using a terminal like PowerShell or the Command Prompt (cmd). First navigate to "python_code_test". Create a venv folder by entering: 

"python -m venv venv"

A venv folder is a local folder for python packages that only python scripts and folders at the same level will have access to. venv should be activated when installing packages and running scripts. To activate/deactivate venv, enter:

".venv\Scripts\activate"
".venv\Scripts\deactivate"

Once activated, install the packages declared in "package_requirements.txt". To install packages use:

"pip install (package)"

Now to install the thorlabs python package, first go to Scientific_Camera_Interfaces_Windows-2.1 -> Scientific Camera Interfaces -> SDK -> Python Toolkit in your file explorer and unzip thorlabs_tsi_camera_python_sdk_package. In your terminal, having .venv activated, navigate to (path\to)\Scientific_Camera_Interfaces_Windows-2.1\Scientific Camera Interfaces\SDK\Python Toolkit\thorlabs_tsi_camera_python_sdk_package\thorlabs_tsi_sdk-0.0.8. Install the package by entering:

"pip install -e ."

The package also requires dll files. The folders in "dlls" at Scientific_Camera_Interfaces_Windows-2.1\Scientific Camera Interfaces\SDK\Python Toolkit\dlls are empty from download. Luckily those files are provided at Scientific_Camera_Interfaces_Windows-2.1\Scientific Camera Interfaces\SDK\Native Toolkit\dlls. "dlls" itself contains two folders, one for 32-bit and the other for 64-bit. The files you are looking for are most likely in "64_lib", but you can always copy all files from both folders. Copy all files and paste them to the relevant folder at Scientific_Camera_Interfaces_Windows-2.1\Scientific Camera Interfaces\SDK\Python Toolkit\dlls.

The thorlabs package requires these files to be added to PATH. A function in main.py already configures the path, using a specific relative path to firstly find these files, and then adding them to PATH. However, the current relative path is specified according to certain folder order. If "Scientific_Camera_Interfaces_Windows-2.1" and "python_code_test" are at the same level, configure_path in main.py should work correctly. The compiler would otherwise issue a warning that it cannot find the dlls folder. 

If you want to organize your folders differently, just make sure "relative_path_to_dlls" in "def configure_path()" in main.py is the path from main.py to the dlls folder.

Everything should now be setup correctly. To start the program, navigate to the folder where main.py is located and enter:

"python main.py"

