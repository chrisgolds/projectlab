# ProjectLab #

Final year project assignment


Christopher Goldsbrough - 170306575

BSc Software Engineering for Business

Queen Mary University of London


This is a web application software written in and supported by Python Django.

To install and run this project, follow the below instructions:

1 - Place the unzipped contents of this directory in a folder called ```projectlab```

2 - Create a new Python 3 virtual environment **anywhere outside** the folder with the code:

```
python3 -m venv projectlab-env
```

(This may take some time to install if you are using Python 3 command line tools for the first time)

3 - Activate the environment:

Windows
```
projectlab-env\Scripts\activate.bat
```

Linux/macOS
```
source projectlab-env/bin/activate
```

4 - Navigate to the ```projectlab``` directory using ```cd```

5 - Install dependencies within requirements.txt

```
(IMPORTANT - Ensure you are using the latest version of pip by first running: pip install --upgrade pip)
pip install -r requirements.txt
```

6 - Migrate models to database by running:

```
python manage.py migrate
```

7 - Run server:

```
python manage.py runserver 0.0.0.0:8000
```

8 - Open web browser of your choice and go to: 127.0.0.1:8000/projectlab
(And to access from other devices on the same network, go to <public_ip_address_of_machine>:8000/projectlab


