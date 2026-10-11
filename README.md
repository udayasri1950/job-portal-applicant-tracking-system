# Python Flask Job Portal

A Job Portal Web Application built using Python and Flask.

## Requirements

- Python 3.9 or compatible version
- Packages listed in `requirements.txt`

## Local Environment Setup

### 1. Create a virtual environment

```bash
python -m venv venv
```

### 2. Activate the virtual environment

**Windows (PowerShell):**
```powershell
.\venv\Scripts\Activate.ps1
```

**Windows (Command Prompt):**
```cmd
venv\Scripts\activate.bat
```

**Linux:**
```bash
source venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment variables

Create a `.env` file in the project root and configure the required Flask secret key and MySQL database settings.

Do not upload your `.env` file or database credentials to GitHub.

### 5. Run the application

```bash
python run.py
```

Open the local address shown in your terminal, usually:

`http://127.0.0.1:5000/`

## Features

- User registration and login
- Separate access for job seekers and companies
- Job posting and job searching
- Job applications and resume uploads
- Application tracking
- Interview scheduling
- Website reviews

## Technologies Used

- Python
- Flask
- HTML
- CSS
- JavaScript
- MySQL
- SQLAlchemy

## License

This project is distributed under the license included in this repository.