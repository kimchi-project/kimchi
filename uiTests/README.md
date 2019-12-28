# Kimchi E2E Tests

The tests are located in uiTests. You should go to the directory to start them
```
$ cd uiTests
```

## How to run

First you need to install all dependencies to run the tests

### Optional: install a virtual environment

```
$ python3 -m venv .env
$ source .env/bin/activate
```

### Install deps
```
$ pip install -r requirements.txt
```

### Run in headless mode
The Makefile expect some environment variables to run kimchi, which are:

```
Expect environment variables:
KIMCHI_USERNAME: username for the host   default: root
KIMCHI_PASSWORD: password for the host
KIMCHI_HOST: host for kimchi             default: localhost
KIMCHI_PORT: port for kimchi             default: 8001
```

So, if you are running against a remote host:

```
$ read -s pass; KIMCHI_HOST=<HOST> KIMCHI_PASSWORD=$pass make
```

### Run in debug mode
If you use the command above, the browser will no be visible for you.

To see the browser action, add the variable `DEBUG`

```
$ read -s pass; KIMCHI_HOST=<HOST> KIMCHI_PASSWORD=$pass DEBUG=true make
```
