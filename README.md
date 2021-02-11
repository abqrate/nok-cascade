# Scripts for key reconciliation phase of QKD

### The scripts structure

There are two scripts, bob.py and alice.py. They should be run on the Bob and Alice computers.
Both scripts are implemented as REST web services.
They are also communicating each other via HTTP REST to do all the work.

In order to reconcile some pair of keys one should first call PUT method on the Bob computer:
```shell
http PUT http://127.0.0.1:15995/bob/api/v1.0/key key=<bob_key>
```

Next - call POST method on the Alice computer:
```shell
http POST http://127.0.0.1:15994/alice/api/v1.0/reconcile key=<alice_key> bob_ip=127.0.0.1 qber=0.05
```
The latter returns reconciled key and number of bits leaked to Eve.

### The Cascade algorithm

Documentation of the algorithm is available here: https://cascade-python.readthedocs.io

### Installing

Recreate Python Virtual Environment and install requirements

```shell
rmdir /s /q venv
python.exe -m venv venv
.\venv\Scripts\python -m pip install --upgrade pip
.\venv\Scripts\python\pip install -r requirements.txt
```

### Configuring & Running

Optionally edit common.py to modify the webservices listening IP and ports.

Run bob.py on the Bob computer, alice.py on the Alice computer.


## Authors

* Cascade algorithm copied from https://github.com/brunorijsman/cascade-python
* **Anton Benderskiy** - *Initial work* - loderan (at) ruservice.ru.
