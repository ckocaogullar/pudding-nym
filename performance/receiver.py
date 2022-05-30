import asyncio
from cmath import e
from dis import code_info
from itertools import count
import websockets
import json
import time
from datetime import datetime
import config
import logging
import sys
import os

logging.basicConfig(format='%(asctime)s - %(message)s', level=logging.INFO)

# Check and save system arguments
assert sys.argv[1] in ['test', 'surb_prep',
                       'surb_count', 'load'], "Run type must be 'test', 'surb_prep' or 'surb_count'"
assert sys.argv[1] in ['surb_prep', 'surb_count'] or len(
    sys.argv) >= 3, "Receiver must take at least three parameters for tests: 'test' keyword, name of the log file and the number of messages per trial"

test_with_surb = None
freq = None


if sys.argv[1] in ['test', 'load']:
    for i in range(len(sys.argv) - 1):
        if sys.argv[i] == '--surb':
            test_with_surb = sys.argv[i+1]
        if sys.argv[i] == '--freq':
            freq = int(sys.argv[i+1])
        if test_with_surb == None:
            assert "Must provide if test will be using SURB or not. Please do so using a --surb flag. Allowed inputs are 'TRUE' and 'FALSE'"
        else:
            assert test_with_surb == 'TRUE' or test_with_surb == 'FALSE', "Allowed inputs for the --surb flag are are 'TRUE' and 'FALSE'"

# Set constants
TEST_WITH_SURB = True if test_with_surb == 'TRUE' else False
TEST_TYPE = sys.argv[1]

if TEST_TYPE in ['test', 'load']:
    MESSAGE_PER_TRIAL = int(sys.argv[3])
elif TEST_TYPE in ['surb_prep']:
    MESSAGE_PER_TRIAL = int(sys.argv[2])

surb_folder = ''

if TEST_WITH_SURB:
    surb_folder = 'with_surb/'
else:
    surb_folder = 'without_surb/'

if TEST_TYPE not in ['surb_count']:
    LOG_PATH = 'test_logs/' + \
        sys.argv[2] + '/' + surb_folder

# For storing the test results on the run
latency_data = {"received_text_time": dict()}

prepared_surbs = {'surbs': [], 'duplicates': []}

# The program needs make a self-address query to the client before it starts sending messages
self_address_request = json.dumps({
    "type": "selfAddress"
})


def save_to_file(data, prep_surb=False):
    global prepared_surbs
    global latency_data
    logging.info('[RECEIVER] Writing to file')

    if prep_surb:
        with open('prepared_surbs/surb.json', 'r') as file:
            existing_surbs = json.load(file)

        with open('prepared_surbs/surb.json', 'w+') as file:
            existing_surbs['surbs'].extend(prepared_surbs['surbs'])
            existing_surbs['duplicates'].extend(prepared_surbs['duplicates'])
            prepared_surbs = {'surbs': [], 'duplicates': []}
            json.dump(existing_surbs, file)
            file.close()
    else:
        if not os.path.exists('test_logs/'):
            os.mkdir('test_logs/')

        if not os.path.exists('test_logs/' + sys.argv[2]):
            os.mkdir('test_logs/' + sys.argv[2])

        if not os.path.exists(LOG_PATH):
            os.mkdir(LOG_PATH)

        existing_data = {"received_text_time": {}}

        open(LOG_PATH + 'receiver.json', 'a').close()

        with open(LOG_PATH + 'receiver.json', 'r') as file:
            try:
                existing_data = json.load(file)
            except:
                logging.info('No existing data found')

        with open(LOG_PATH + 'receiver.json', 'w+') as file:
            for key in existing_data["received_text_time"]:
                if existing_data["received_text_time"][key]:
                    latency_data["received_text_time"][str(
                        key)] = existing_data["received_text_time"][key]
            json.dump(latency_data, file)
            file.close()


def surb_count():
    with open('prepared_surbs/surb.json', 'r') as file:
        data = json.load(file)

    logging.info('There are {} SURBs ready for use'.format(len(data['surbs'])))
    logging.info('{} clashes SURB duplications detected'.format(
        len(data['duplicates'])))


async def prepare_surbs():
    count = 0
    text_send = {
        "type": "send",
        "message": "",
        "recipient": config.RECEIVER_ADDRESS,
        "withReplySurb": True,
    }
    timeout_count = 0

    async with websockets.connect(config.RECEIVER_CLIENT_URI) as websocket:
        await websocket.send(self_address_request)
        self_address = json.loads(await websocket.recv())
        logging.info("[RECEIVER] Our address is: {}".format(
            self_address["address"]))

        # Send messages first without SURB, then with SURB
        logging.info(
            "[RECEIVER] **Starting sending messages *with* SURB to collect SURBs**")

        for _ in range(int(MESSAGE_PER_TRIAL/100)):
            while count < 100:
                await websocket.send(json.dumps(text_send))
                count += 1

            logging.info(
                '[RECEIVER] Sent {} SURBs addressed to myself'.format(count+1))
            count = 0
            logging.info('[RECEIVER] Now I wait for SURBs to arrive.')

            while count < 100 and timeout_count < 3:
                try:
                    message = json.loads(
                        await asyncio.wait_for(websocket.recv(), timeout=config.TIMEOUT))
                    timeout_count = 0
                except asyncio.TimeoutError:
                    message = {'type': 'timeout'}
                if message['type'] == 'error':
                    logging.error(
                        "[SENDER] Received error message from the mix network: {}".format(message))
                elif message['type'] == 'timeout':
                    timeout_count += 1
                    logging.warning(
                        '[RECEIVER] Timeout while waiting for message.')
                else:
                    timeout_count = 0
                    surb = message['replySurb']
                    logging.info(surb)
                    if surb in prepared_surbs['surbs']:
                        prepared_surbs['duplicates'].append(surb)
                    else:
                        prepared_surbs['surbs'].append(surb)
                    count += 1
            save_to_file(prepared_surbs, True)
            count = 0


async def receive_message():
    global freq
    count = 0
    timeout_count = 0
    max_message_seq = ''
    # total_message_num = MESSAGE_PER_TRIAL * \
    #     int(round((config.MAX_FREQ - config.INIT_FREQ) / config.FREQ_STEP) +
    #         1) if TEST_TYPE == 'test' and not freq else MESSAGE_PER_TRIAL

    # total_message_num = int(
    #     freq * config.TOTAL_TEST_TIME) if TEST_TYPE == 'test' else MESSAGE_PER_TRIAL

    total_message_num = MESSAGE_PER_TRIAL
    print('total message num for receiver is', total_message_num)

    freq = config.INIT_FREQ if not freq else float(freq)

    # Prepare data dictionary
    save_to_file(latency_data)

    freq_cnt = freq
    while freq_cnt <= config.MAX_FREQ:
        if freq_cnt not in latency_data["received_text_time"]:
            latency_data["received_text_time"][str(freq_cnt)] = dict()
            freq_cnt = round(freq_cnt + config.FREQ_STEP, 1)
    print('Receiver latency data is')
    print(latency_data)
    # Connect to receiver client and wait for messages
    async with websockets.connect(config.RECEIVER_CLIENT_URI) as websocket:
        await websocket.send(self_address_request)
        self_address = json.loads(await websocket.recv())
        logging.info("[RECEIVER] Our address is: {}".format(
            self_address['address']))

        # Wait for messages until all messages received or 10 consecutive messages have timed out
        while count < total_message_num and timeout_count < 10:
            try:
                message = json.loads(
                    await asyncio.wait_for(websocket.recv(), timeout=config.TIMEOUT))
                timeout_count = 0
            except asyncio.TimeoutError:
                message = {'type': 'timeout'}

            if message['type'] == 'error':
                logging.error(
                    "[RECEIVER] Received error message from the mix network: {}".format(message))
            elif message['type'] == 'timeout':
                timeout_count += 1
                logging.warning(
                    '[RECEIVER] Timeout while waiting for message.')
            else:
                recv_time = time.time()
                logging.info('[RECEIVER] Received message {}'.format(message))
                message_seq = message['message'].split()[0].strip()
                message_freq = float(message['message'].split()[1].strip())
                if str(message_freq) in latency_data["received_text_time"]:
                    latency_data["received_text_time"][str(
                        message_freq)][message_seq] = recv_time
                else:
                    print("WEIRD MESSAGE RECEIVED {}".format(message))
                    count -= 1
            count += 1

        logging.info('[RECEIVER] Finished receiving all messages.')


if TEST_TYPE == 'test' or TEST_TYPE == 'load':
    asyncio.get_event_loop().run_until_complete(receive_message())
    save_to_file(latency_data)
elif TEST_TYPE == 'surb_prep':
    asyncio.get_event_loop().run_until_complete(prepare_surbs())
    save_to_file(prepared_surbs, True)
elif TEST_TYPE == 'surb_count':
    surb_count()

logging.info("[RECEIVER] Receiver loop complete")
