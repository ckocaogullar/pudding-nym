import sys

# Nym network addresses of the clients
SENDER_ADDRESS = 'FzQpAFLmX7pA51b27E9U2hu9NUcu5bpw3soX3U6xokCt.94qKRz7mBkqZVw2sSnRdEwWhaoB5Uh8rJizMf2LXPKVn@sJ5oCULnicPnhwHwGMLBwWuaw52ERu9P3dCCLKNKXnz'
RECEIVER_ADDRESS = 'HdGd5AKvsy2B3EjSXypascXCWyEF55AqYesATUFFAB49.B9D4nzqJP6m8638RfDYDsJVKcMCkkaw6V9FzTNP5nZVE@E3mvZTHQCdBvhfr178Swx9g4QG3kkRUun7YnToLMcMbM'

# Where you are running the clients locally
SENDER_CLIENT_URI = "ws://localhost:1977"
RECEIVER_CLIENT_URI = "ws://localhost:1978"

# Test params
INIT_FREQ = 60.0
FREQ_STEP = 50.0
MAX_FREQ = 2010
TIMEOUT = 20
TOTAL_TEST_TIME = 60  # in seconds


def generate_performance_script():
    with open('performance-new.sh', 'w+') as f:
        for i in range(int(INIT_FREQ), int(MAX_FREQ+INIT_FREQ+1), int(FREQ_STEP)):
            f.write(
                'python3 receiver.py test "$NOW" 500 --surb FALSE --freq {} & \n'.format(i))
            f.write(
                'python3 sender.py test "$NOW" 500 --surb FALSE --freq {} & \n'.format(i))
            f.write('wait \n\n')

        for i in range(int(INIT_FREQ), int(MAX_FREQ+INIT_FREQ+1), int(FREQ_STEP)):
            f.write(
                'python3 receiver.py test "$NOW" 500 --surb TRUE --freq {} & \n'.format(i))
            f.write(
                'python3 sender.py test "$NOW" 500 --surb TRUE --freq {} & \n'.format(i))
            f.write('wait \n\n')


if sys.argv[1] == 'generate-performance-script':
    generate_performance_script()
