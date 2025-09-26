# 🔬 CR-39 Particle Counter: Requirements & Installation

> This guide provides all the necessary Python requirements and step-by-step installation instructions to run the CR-39 Particle Counter application.

<p align="center">
  <img src="https://i.imgur.com/your-image-url.png" alt="CR-39 Particle Counter Interface" width="800"/>
  <br>
  <em>(This is a placeholder. Replace with a real screenshot of your application.)</em>
</p>

---

## 📋 Requirements

To run this application, you'll need Python and a few specific external libraries.

### 1. Python 🐍
* **Python 3.x** is required. The application is built on Python 3 and is not compatible with Python 2. You can download the latest version from the [official Python website](https://www.python.org/downloads/).

### 2. Python Libraries 📚
The application depends on the following external libraries:

* **OpenCV (`opencv-python`)**: The core library for all image processing and analysis tasks, such as thresholding and the watershed algorithm.
* **NumPy (`numpy`)**: A fundamental package for scientific computing, used by OpenCV for handling image data as numerical arrays.
* **Pillow (`Pillow`)**: The modern fork of the Python Imaging Library (PIL), used here to interface between OpenCV image formats and the Tkinter UI.

> **Note**: The graphical user interface is built with **Tkinter**, which is part of Python's standard library and does **not** require a separate installation.

---

## ⚙️ Installation Instructions

Follow these steps to set up your environment and install all dependencies.

### Step 1: Install Python
If you don't have Python 3, download and install it from [python.org](https://www.python.org/downloads/).
> **✅ Important**: During the Windows installation, make sure to check the box that says **"Add Python to PATH"**. This will allow you to run Python and `pip` from your command prompt.

### Step 2: Download the Application Code
Download the `microscopic_pc.py` file and save it to a new folder on your computer.

### Step 3: Install Required Libraries (Two Methods)

You can install the libraries one by one or all at once using a `requirements.txt` file. The second method is recommended.

#### Method A: The Easy Way (Recommended)
1.  In the same folder where you saved the application, create a new text file named `requirements.txt`.
2.  Copy and paste the following lines into that file:
    ```txt
    numpy
    opencv-python
    Pillow
    ```
3.  Save the file.
4.  Open your command prompt or terminal, navigate to that folder, and run this single command:
    ```bash
    pip install -r requirements.txt
    ```
    This command tells `pip` (Python's package installer) to read the file and install all the listed libraries automatically.

#### Method B: Manual Installation
If you prefer to install the libraries individually, open your command prompt or terminal and run the following command:
```bash
pip install numpy opencv-python Pillow
