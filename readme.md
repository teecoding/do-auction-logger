## About
- Simple python script which will log into darkorbit account, goes through all servers and stores latest auction history into json 

--- 

## Requirements
- Python (3.18.10)
- beautifulsoup4 (4.11.1)
- python-dotenv (0.20.0)
- requests (2.28.0)

--- 
## Before you start installation
- Make sure that the script is able to create files/directories in project folder
- The account you will be using to log into darkorbit with this script needs to atleast once log into all servers and chose company!

*Feel free to implement automatic detection of company selection screen and selecting random company.*

---

## Installation

- Create virtual enviroment with one of the following commands:
    - `virtualenv venv`
    - `python3 -m venv` 
- Install requirements in venv: `pip install -r /path/to/requirements.txt` 
- Copy `.env.example` into `.env` and fill your credentials
- Run `main.py` 
