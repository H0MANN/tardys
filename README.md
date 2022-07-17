# TAO ICS SWIMS
A Python library for the TAO/SWIMS Instrument Control System.


## Description
T.B.W.

## Install
Assume you have already installed TAO ICS `common`.
That requires you to have

* a directory `${HOME}/taoics`
* a directory `${HOME}/taoics_var`
* * sub directories `log`, `pid`, and `hb`


1. Move to `${HOME}/taoics` directory.
1. Clone this repository (git clone ssh://git@bitbucket.org/tao_project/swims.git).
    - A directory, `swims`, will be created.
1. Manually create a file `${HOME}/swims/.passwd` which contains the password for SWIMS.
1. Install Python configparser via PIP.
    - `sudo /usr/local/bin/pip-2.7 install configparser`