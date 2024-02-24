# RandomMapTogether
Simple pyplanet application to add RMC mode online 

## Installation
### docker
If u don't know how to set up a TM2020 server I advise to use the following
docker compose [RMT-Docker-server](https://github.com/thexivn/RMT-Docker-server).
### requirements
- TM2020
- pyplanet
### RMT
1. clone the following repository 
```bash 
git clone https://github.com/thexivn/RandomMapTogether 
cd RandomMapTogether
```
2. activate the `pyenv` in which `pyplanet` was installed
``` bash
pyenv activate pyplanet
```
3. Install the package. Use one of this follownog commands
```bash
python3 setup.py install
#or
pip install -e .
```
4. Add the package `'it.thexivn.random_maps_together'` to `apps.py`
inside the pyplanet settings folder

## configurations
| ***setting***       | ***values***         | ***description***                                                                                                      |
|---------------------|----------------------|------------------------------------------------------------------------------------------------------------------------|
| game_time           | int                  | time in `seconds`. Default 1h (3600s)                                                                                  |
| AT_time             | AT, GOLD, SILVER     | time to beat to advance to next map                                                                                    |
| GOLD_time           | GOLD, SILVER, BRONZE | time to beat that allow you to `take GOLD` and skip to next map                                                        |
| min_perm_start      | 0,1,2,3              | level required to start the game <br/>LEVEL_PLAYER = 0<br/>LEVEL_OPERATOR = 1<br/>LEVEL_ADMIN = 2<br/>LEVEL_MASTER = 3 |
| infinite_free_skips | bool                 | if enabled allow to always skips                                                                                       |

~~Also set `S_ForceLapsNb` to `-1`, this will use the validation laps for those 
maps that have multi-laps~~ When the RMT game start automatically set `S_ForceLapsNb` to `-1`