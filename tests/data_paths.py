import os


current = os.path.dirname(os.path.realpath(__file__))


shared = os.path.join(os.path.dirname(current),
                      'data_files')


FILE = os.path.join(shared,
                    'HIFI00195790.nxs')


FILTER = os.path.join(shared,
                      'load_filter.json')


BADFILTER = os.path.join(shared,
                         'load_bad_filter.json')
