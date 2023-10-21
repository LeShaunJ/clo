#!/usr/bin/env python3

###########################################################################

if __name__ == "__main__":
    import cProfile
    import pstats
    import io
    from pstats import SortKey

    stream = io.StringIO()
    sortby = SortKey.CUMULATIVE

    with cProfile.Profile() as profiler:

        from clo import CLI
        from clo.output import Log

        try:
            CLI()
        except Log.EXIT:
            pass

    stats = pstats.Stats(profiler, stream=stream).sort_stats(sortby)
    stats.print_stats(20)
    print(stream.getvalue())
