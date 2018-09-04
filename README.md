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

# Screenshots
![](https://user-images.githubusercontent.com/4522822/43274568-d3d9c134-90ff-11e8-961f-63946af6d3f3.png?raw=true "Balances")

![](https://user-images.githubusercontent.com/4522822/43274594-e0b3f992-90ff-11e8-943f-52bb2ebf8993.png?raw=true "Balances")

![](https://user-images.githubusercontent.com/4522822/43274631-f1de0d70-90ff-11e8-983a-1723ff37ebeb.png?raw=true "Master Password")

![](https://user-images.githubusercontent.com/4522822/43274657-09c42ab4-9100-11e8-8833-7acb18617a66.png?raw=true "Stats")

![](https://user-images.githubusercontent.com/4522822/43274691-27a2777a-9100-11e8-8faa-c84d7a7e257e.png?raw=true "Charts")

![](https://user-images.githubusercontent.com/4522822/44983418-6712f780-af79-11e8-8548-e104e718e2a1.png?raw=true "Charts")

![](https://user-images.githubusercontent.com/4522822/45027315-5f1e8a80-b041-11e8-8930-37a92e89cf9e.gif?raw=true "Demo")

