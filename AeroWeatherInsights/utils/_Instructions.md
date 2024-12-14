# Project Setup Guide

This guide provides instructions to set up your Python environment and install all necessary dependencies for your project.


## Prerequisites
- **Python Version**: Ensure Python `>=3.11` is installed on your system. You can download it from the [official Python website](https://www.python.org/downloads/).
- **Package Manager**: The guide assumes `pip` is installed with Python. You can verify this by running:
  ```bash
  python -m pip --version
  ```

---

## Installing Dependencies

The project has the following dependencies.

```plaintext
joblib>=1.4.2
matplotlib>=3.9.3
numpy>=2.2.0
pandas>=2.2.3
plotly>=5.24.1
requests>=2.32.3
schedule>=1.2.2
scikit-learn>=1.5.2
scipy
streamlit>=1.14.1
```

###  Install the Dependencies
To install the dependencies run the following command to install all dependencies listed in the `requirements.txt` file:
```bash
pip install -r requirements.txt
```



---


## Running the Project

1. Run the following command in the project directory:
```bash
streamlit run main.py
```
2. To view the project go to
http://localhost:5000/
The port and options can be configured in the file **.streamlit/config.toml**


## Troubleshooting

### Common Issues
1. **Compatibility Issues with Libraries**:
   If you encounter errors during installation, install core dependencies (`numpy`, `scipy`, `matplotlib`) in the following order:
   ```bash
   pip install numpy
   pip install scipy
   pip install matplotlib
   ```


2. **Permission Issues**:
   Run the installation command with administrative privileges:
   ```bash
   pip install -r requirements.txt --user
   ```


