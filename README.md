# Scripts for the QKD key reconciliation phase

### The scripts structure

There are two scripts, bob.py and alice.py. They should be run on the Bob and Alice computers.

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

Edit config.py to set variables.
Create random_seed.dat file with several kilobytes of random data identical on both Alice and Bob side.

Run bob.py on the Bob computer:
```shell
.\venv\Scripts\python bob.py
```

Run alice.py on the Alice computer:
```shell
.\venv\Scripts\python alice.py
```


## Authors

* Cascade algorithm copied from https://github.com/brunorijsman/cascade-python
* **Anton Benderskiy** - *Initial work* - loderan (at) ruservice.ru.
