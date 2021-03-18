VERSION 1.4.1; 21.08.2020
    - [EPCCCS-8303] Use self._token instead of self.token to store the RBAC token

VERSION 1.4.0; 21.08.2020
    - [EPCCCS-8303] Acquire token if rbac_token kw argument explicitly set to None

VERSION 1.3.9; 20.08.2020
    - [EPCCCS-8285] Lock serial channel for multithreaded operations
    - 
VERSION 1.3.4; 12.06.2020
    - [EPCCCS-xxxx] Fix pyfgc long timeout on serial response errors.

VERSION 1.3.3; 22.05.2020
    - [EPCCCS-xxxx] Renew RBAC token automatically if one hour to expire (FgcSession).
  
VERSION 1.3.2; 06.05.2020
    - [EPCCCS-xxxx] Updated version requirements of pyfgc_rbac and pyfgc_decoders.

VERSION 1.3.1; 29.04.2020
    - [EPCCCS-xxxx] Bug fix on pyfgc rbac_token argument. RBAC can now be disabled explicitly by passing None.

VERSION 1.3.0; 28.04.2020
    - [EPCCCS-xxxx] Modified pyfgc async interface. Fixed broken tests.
    - [EPCCCS-8011] Revision of pyfgc error parsing.

VERSION 1.2.3; 17.04.2020
    - [EPCCCS-xxxx] Fixed concurrency issues in pyfgc async.

VERSION 1.2.2; 16.04.2020
    - [EPCCCS-7975] Allow multiple serial connections
    - [EPCCCS-XXXX] Improve logging in sync_fgc

VERSION 1.2.1; 02.04.2020
    - [EPCCCS-XXXX] Bug fixes in async_pyfgc.

VERSION 1.2.0; 21.02.2020
    - [EPCCCS-7843] pyfgc async module

VERSION 1.1.6; 05.02.2020
    - [EPCCCS-7425] Include placeholders for get/set coroutines.
    - [EPCCCS-7425] Rearrange code in fgc_session.
    - [EPCCCS-xxxx] Fixed several pyfgc monitor bugs.

VERSION 1.1.5; 02.12.2019
    - [EPCCCS-7425] Add 'fgc' as a fgc_session member

VERSION 1.1.4; 29.11.2019
    - [EPCCCS-XXXX] Simplify pyfgc api allowing one connection at a time only. Changes in monitor classes
    - [EPCCCS-XXXX] Correct bug in fgc_session by which wrong device name is passed to pyfgc_name
    - [EPCCCS-XXXX] Avoid calling pyfgc_name and pyfgc_rbac if protocol is serial
    - [EPCCCS-7455] Rename protocol modules. Add consistency in function arguments naming
    - [EPCCCS-7425] Change library's API
    - [EPCCCS-6851] Improve pyfgc responses
