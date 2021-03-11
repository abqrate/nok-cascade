# -*- coding: utf-8 -*-

BOB_IP = '127.0.0.1'                      # Bob's IP address
KEYS_FOLDER_ALICE = 'keys\\Alice'         # Bob's directory where raw key files are read and result files are saved
KEYS_FOLDER_BOB = 'keys\\Bob'             # Alice's directory where raw key files are read and result files are saved
RANDOM_SEED_FILENAME = 'random_seed.dat'  # filename with random bytes for Toeplitz matrix construction

KEYFRAME_SIZE = 2048                      # size of reconciliation keyframes, in bytes
KEYPART_QBER_ESTIMATION = 0.1             # this part of each keyframe are used for QBER estimation
KEYPART_QBER_ESTIMATION_SPLITS = 10       # number of blocks on which this part is split across keyframe
COMPARE_FRAME_TOEPLITZ_HEIGHT = 40        # size of hash used to compare reconciled keys, in bits

FLASK_HOST = '0.0.0.0'                    # IP address of Bob's REST service
FLASK_PORT = 15995                        # port of Bob's REST service

HTTP_RETRIES_BEFORE_FAILURE = 3600        # number of tries to call Bob's REST service before failure
HTTP_RETRIES_DELAY_ON_ERROR = 1.0         # seconds between the tries

MAX_ESTIMATED_QBER = 0.09                 # if estimated QBER is greater, keyframe is skipped
