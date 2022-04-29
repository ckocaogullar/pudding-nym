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
import math
logging.basicConfig(format='%(asctime)s - %(message)s', level=logging.INFO)

# Check and save system arguments
assert sys.argv[1] in ['throughput', 'latency',
                       'surb_prep', 'surb_count'], "Test type must be 'throughput', 'latency' or 'surb_prep'"
assert sys.argv[1] in ['surb_prep', 'surb_count'] or len(
    sys.argv) >= 3, "Receiver must take at least three parameters for tests: test type (latency or throughput), name of the log file and the number of messages per trial"

test_with_surb = None
if sys.argv[1] in ['throughput', 'latency']:
    for i in range(len(sys.argv) - 1):
        if sys.argv[i] == '--surb':
            test_with_surb = sys.argv[i+1]
        if test_with_surb == None:
            assert "Must provide if test will be using SURB or not. Please do so using a --surb flag. Allowed inputs are 'TRUE' and 'FALSE'"
        else:
            assert test_with_surb == 'TRUE' or test_with_surb == 'FALSE', "Allowed inputs for the --surb flag are are 'TRUE' and 'FALSE'"

# Set constants
TEST_WITH_SURB = True if test_with_surb == 'TRUE' else False
TEST_TYPE = sys.argv[1]

if TEST_TYPE in ['throughput', 'latency']:
    MESSAGE_PER_TRIAL = int(sys.argv[3])
elif TEST_TYPE in ['surb_prep']:
    MESSAGE_PER_TRIAL = int(sys.argv[2])

surb_folder = ''

if TEST_WITH_SURB:
    surb_folder = 'with_surb/'
else:
    surb_folder = 'without_surb/'

if TEST_TYPE not in ['surb_count']:
    LOG_PATH = TEST_TYPE + '_logs/' + \
        sys.argv[2] + '/' + surb_folder

if TEST_TYPE == 'throughput':
    LOG_PATH += str(MESSAGE_PER_TRIAL)

# For storing the test results on the run
latency_data = {
    "sent_surb_reply_text_time": dict(),
    "received_text_time": dict(),
    "received_surb_text_time": dict(),
    'received_text_without_surb_time': dict(),
    'received_text_with_surb_time': dict(),
}
throughput_data = dict()

prepared_surbs = {'surbs': [], 'duplicates': []}

# The program needs make a self-address query to the client before it starts sending messages
self_address_request = json.dumps({
    "type": "selfAddress"
})


def save_to_file(data, prep_surb=False):
    global prepared_surbs
    logging.info('[RECEIVER] Writing to file')

    if prep_surb:
        # with open('prepared_surbs/surb.json', 'w+') as file:
        #     json.dump(data, file)
        #     file.close()
        with open('prepared_surbs/surb.json', 'r') as file:
            existing_surbs = json.load(file)

        with open('prepared_surbs/surb.json', 'w+') as file:
            existing_surbs['surbs'].extend(data['surbs'])
            existing_surbs['duplicates'].extend(data['duplicates'])
            prepared_surbs = {'surbs': [], 'duplicates': []}
            json.dump(existing_surbs, file)
            file.close()
    else:
        if not os.path.exists(TEST_TYPE + '_logs/' + sys.argv[2]):
            os.mkdir(TEST_TYPE + '_logs/' + sys.argv[2])

        if TEST_TYPE == 'throughput' and not os.path.exists(TEST_TYPE + '_logs/' + sys.argv[2] + '/' + surb_folder):
            os.mkdir(TEST_TYPE + '_logs/' + sys.argv[2] + '/' + surb_folder)

        if not os.path.exists(LOG_PATH):
            os.mkdir(LOG_PATH)

        with open(LOG_PATH + '/receiver.json', 'w+') as file:
            json.dump(data, file)
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
                print(count)

            count = 0
            print('Now we wait')
            while count < 100 and timeout_count < 3:
                try:
                    message = json.loads(
                        await asyncio.wait_for(websocket.recv(), timeout=10))
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
                    print(surb)
                    if surb in prepared_surbs['surbs']:
                        prepared_surbs['duplicates'].append(surb)
                    else:
                        prepared_surbs['surbs'].append(surb)
                    count += 1
            save_to_file(prepared_surbs, True)
            count = 0


async def receive_single_text():
    count = 0
    freq = config.INIT_FREQ
    timeout_count = 0
    total_message_num = MESSAGE_PER_TRIAL * \
        int(round((config.MAX_FREQ - config.INIT_FREQ) / config.FREQ_STEP) + 1)
    print('total_message_num', total_message_num)

    # Prepare data dictionary
    while freq <= config.MAX_FREQ:
        # latency_data["received_text_without_surb_time"][freq] = dict()
        # latency_data["received_text_with_surb_time"][freq] = dict()
        latency_data["received_text_time"][freq] = dict()
        freq = round(freq + config.FREQ_STEP, 1)

    async with websockets.connect(config.RECEIVER_CLIENT_URI) as websocket:
        await websocket.send(self_address_request)
        self_address = json.loads(await websocket.recv())
        logging.info("[RECEIVER] Our address is: {}".format(
            self_address['address']))

        while count < total_message_num and timeout_count < 10:
            try:
                message = json.loads(
                    await asyncio.wait_for(websocket.recv(), timeout=20))
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
                recv_time = time.time()
                logging.info('[RECEIVER] Received message {}'.format(message))
                message_seq = message['message'].split()[0].strip()
                freq = float(message['message'].split()[1].strip())
                latency_data["received_text_time"][freq][message_seq] = recv_time
            count += 1

        logging.info('[RECEIVER] Finished receiving all messages')


async def receive_text_load():
    start = 0
    end = 0
    timeout_count = 0
    messages = dict()
    label = "received_time"

    async with websockets.connect(config.RECEIVER_CLIENT_URI) as websocket:
        await websocket.send(self_address_request)
        self_address = json.loads(await websocket.recv())
        logging.info("[RECEIVER] Our address is: {}".format(
            self_address['address']))

        for i in range(MESSAGE_PER_TRIAL + 1):
            if timeout_count < 10:
                try:
                    message = json.loads(
                        await asyncio.wait_for(websocket.recv(), timeout=20))
                    # Stop the timer when the MESSAGE_PER_TRIALth message is received
                    end = time.time()

                    messages[message['message']] = end
                    logging.info(
                        '[RECEIVER] Received message {}'.format(message))

                except asyncio.TimeoutError:
                    logging.info('[RECEIVER] Timeout.')
                    timeout_count += 1

                # Start the timer on the first received message
                if i == 0:
                    start = time.time()

        throughput_data[label] = end - start
        throughput_data['message_timings'] = messages
        logging.info(
            '[RECEIVER] It took {} seconds to receive {} messages'.format(throughput_data[label], MESSAGE_PER_TRIAL))


if TEST_TYPE == 'latency':
    # asyncio.get_event_loop().run_until_complete(reply_text())
    asyncio.get_event_loop().run_until_complete(receive_single_text())
    save_to_file(latency_data)
elif TEST_TYPE == 'throughput':
    asyncio.get_event_loop().run_until_complete(receive_text_load())
    save_to_file(throughput_data)
elif TEST_TYPE == 'surb_prep':
    asyncio.get_event_loop().run_until_complete(prepare_surbs())
    save_to_file(prepared_surbs, True)
elif TEST_TYPE == 'surb_count':
    surb_count()

logging.info("[RECEIVER] Receiver loop complete")
