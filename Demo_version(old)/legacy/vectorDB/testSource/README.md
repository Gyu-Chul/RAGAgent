# HAB
A tool for visualizing and GUI debugging program execution in Python


This is the second technical side project of the OpenSW Open Developer Contest and DDRX team.

The program is a program that visually exposes the execution process of the source code written by the developer and
Furthermore, it is a program that allows source code modification with a mouse in a GUI-based area.


# How to Run the Program (Windows)

## 1. Activate the Virtual Environment  
Activate the virtual environment using the following command:  

    .\venv\Scripts\Activate  

If you are not using a virtual environment and can run the program with your system-wide Python installation, you may skip this step.  

## 2. Install Dependencies  
Ensure all required dependencies are installed by running:  

    pip install -r requirements.txt  

## 3. Set Environment Variables  
Set the necessary environment variables:  

    $env:DEBUG = "true"  

## 4. Check Python Version  
Verify that Python 3.13 is installed by running:  

    python --version  

Make sure you are using Python 3.13 to avoid compatibility issues.  

## 5. Run the Program  
Navigate to the root directory and execute the following command to start the program:  

    python hab.py  
