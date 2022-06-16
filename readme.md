## About
- Simple python script which will log into darkorbit account, goes through all servers and stores latest auction history into json 

--- 

## Requirements
- Python (3.18.10)
- beautifulsoup4 (4.11.1)
- lxml (4.9.0)
- python-dotenv (0.20.0)
- requests (2.28.0)

--- 
## Before you start installation
- Make sure that the script is able to create files/directories in project folder
- The account you will be using to log into darkorbit with this script needs to atleast once log into all servers and chose company!

*Feel free to implement automatic detection of company selection screen and selecting random company.*

---

## Installation

### Local 
- Clon this repo `git clone https://github.com/teecoding/do-auction-logger.git`
- Create virtual enviroment with one of the following commands:
    - `virtualenv venv`
    - `python3 -m venv` 
- Install requirements in venv: `pip install -r /path/to/requirements.txt` 
- Copy `.env.example` into `.env` and fill your credentials
- Run script: `python main.py` 

### Docker 
- Clon this repo `git clone https://github.com/teecoding/do-auction-logger.git`
- Copy `.env.example` into `.env` and fill your credentials
- Build docker image: `docker build . --no-cache -t do-auction-logger`
- Run docker: `docker run -v <path_to_fodler_where_you_wanna_store_logged_jsons>:/do-auction-logger/data do-auction-logger:latest`