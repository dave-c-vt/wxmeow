# ^.^____/

# the weather, right meow

## install

``` bash
git clone https://github.com/dave-c-vt/wxmeow
cd wxmeow/
python3 deploy.py
```

## what it does

the first time the ```deploy.py``` script is run, it creates a virtual environment and installs all the 
necessary packages for this Flask application, and then launches the app.


the next time the ```deploy.py``` script is run, it launches the app.


you can view it at http://localhost:5000.

## or do it docker

``` bash
docker build -t wxmeow:latest .
docker run --name wxdocker -d -p 8000:5000 --rm wxmeow:latest
```

and access at http://localhost:8000
