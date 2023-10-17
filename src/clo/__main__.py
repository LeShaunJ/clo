#!/usr/bin/env python3

from . import main

###########################################################################

if __name__ == "__main__":
    from .output import Log
    try:
        main()
    except Log.EXIT as e:
        pass
        e.Done()
