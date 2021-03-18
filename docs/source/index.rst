Welcome to pyfgc documentation!
===============================

Introduction
------------

pyfgc is a library that allows clients to communicate with Function Generation Controllers (FGCs) via
TCP/IP through a front-end computer, and/or through a serial interface. 


Installation
------------

Using the `acc-py Python package index
<https://wikis.cern.ch/display/ACCPY/Getting+started+with+acc-python#Gettingstartedwithacc-python-OurPythonPackageRepositoryrepo>`_
``pyfgc`` can be pip installed with::
   
   pip install pyfgc


Quick start
----------------------
The FGC library has different flavours to connect to an FGC. The default connection protocol is the sync NCRP. 
* Interact with a context manager: 

.. code:: python
   
    device = 'RFNA.866.01.ETH1'
    prop = 'LIMITS.I.POS'

    import pyfgc
    with pyfgc.fgc(device) as fgc:
        r = fgc.set(prop, 10)
        r = fgc.get(prop)

        try:
            r.value

        except pyfgc.FgcResponseError as e:
            print(f'Error while getting property {prop} from device {device}')

* One-shot commands: 

.. code:: python
   
    device = device
    prop = 'LIMITS.I.POS'

    import pyfgc
    r = pyfgc.get(device, prop)
    try:
        r.value

    except pyfgc.FgcResponseError as e:
        print(f'Error while getting property {prop} from device {device}')
    
* try/except block:

.. code:: python
   
    device = device
    prop = 'LIMITS.I.POS'

    import pyfgc
    try:
        session = pyfgc.connect(device)

    except pyfgc.PyfgcError:
        # Do something here
        pass

    else:
        r = session.get(prop)
        # do something with prop value here

    finally:
        session.close()

   

Contact
----------------------
Please send your bug/improvement reports to converter-controls-support@cern.ch


Documentation contents
----------------------

.. toctree::
   :maxdepth: 1

   guides/sync_serial.rst
   guides/fgc_response.rst
   guides/async.rst
   guides/monitor.rst
   guides/remoteterm.rst

