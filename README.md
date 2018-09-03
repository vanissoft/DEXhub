# DEXhub
Is a work in progress for a portfolio management for Bitshares blockchain.
The account/keys are not disclosed and they keep local. 

## Description
Python Web based application.

*Makes use of Xeroc's pyBitshares library.

## Progress tracking
The progress is tracked in Kanban style notes:
* Front-end: https://github.com/vanissoft/DEXhub/projects/1
* Back-end: https://github.com/vanissoft/DEXhub/projects/2

## Instalation
Development OS is GNU/Linux so other OS would don't work.
Clone the repo and launch main.py and then dexhub_worker.py. It is in debugging/developing mode thus the manual launch of dexhub_worker.py.
Python will inform of the depencies like Sanic, Redis, and so on.
Once launched browse to http://127.0.0.1:8808/main.html

## Development
Recommended IDE is the fantastic PyCharm from JetBrains.
First start main.py and then dexhub_data.py in debug mode for being able to track server-part bugs.
Brython debugging is somewhat weird to bug hunting as the Python-Javascript conversion messes the source code, so there is need to make use of poor-man's debugging with print staments along the code.

Cheers.


Screenshots in issue #49 (https://github.com/vanissoft/DEXhub/issues/49)
