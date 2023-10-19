#!/usr/bin/env python3

###########################################################################

if __name__ == "__main__":
    from . import main
    from .output import Log
    try:
        main()
    except Log.EXIT as e:
        pass
        e.Done()
