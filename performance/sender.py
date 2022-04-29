import asyncio
from cmath import e
import json
import websockets
from datetime import datetime
import time
import config
import logging
import sys
import os
import math
import random
import string
logging.basicConfig(format='%(asctime)s - %(message)s', level=logging.INFO)
logging.basicConfig(format='%(asctime)s - %(message)s', level=logging.WARNING)


# Check and save system arguments
assert len(sys.argv) >= 3, "Sender must take at least three parameters: test type (latency or throughput), name of the log file and the number of messages per trial"
assert sys.argv[1] in ['throughput',
                       'latency'], "Test type must be 'throughput' or 'latency'"

test_with_surb = None

for i in range(len(sys.argv) - 1):
    if sys.argv[i] == '--surb':
        test_with_surb = sys.argv[i+1]
    if test_with_surb == None:
        assert "Must provide if test will be using SURB or not. Please do so using a --surb flag. Allowed inputs are 'TRUE' and 'FALSE'"
    else:
        assert test_with_surb == 'TRUE' or test_with_surb == 'FALSE', "Allowed inputs for the --surb flag are are 'TRUE' and 'FALSE'"

# Set constants
TEST_WITH_SURB = True if test_with_surb == 'TRUE' else False
MESSAGE_PER_TRIAL = int(sys.argv[3])
TEST_TYPE = sys.argv[1]

surb_folder = None
if TEST_WITH_SURB:
    surb_folder = 'with_surb/'
else:
    surb_folder = 'without_surb/'

LOG_PATH = TEST_TYPE + '_logs/' + \
    sys.argv[2] + '/' + surb_folder

if TEST_TYPE == 'throughput':
    LOG_PATH += str(MESSAGE_PER_TRIAL)

# For storing the test results on the run
latency_data = {
    "sent_text_time": dict(),
}

throughput_data = dict()

# The program needs make a self-address query to the client before it starts sending messages
self_address_request = json.dumps({
    "type": "selfAddress"
})


def save_to_file(data):
    logging.info('[SENDER] Writing to file')

    if not os.path.exists(TEST_TYPE + '_logs/' + sys.argv[2]):
        os.mkdir(TEST_TYPE + '_logs/' + sys.argv[2])

    if TEST_TYPE == 'throughput' and not os.path.exists(TEST_TYPE + '_logs/' + sys.argv[2] + '/' + surb_folder):
        os.mkdir(TEST_TYPE + '_logs/' + sys.argv[2] + '/' + surb_folder)

    if not os.path.exists(LOG_PATH):
        os.mkdir(LOG_PATH)

    with open(LOG_PATH + '/sender.json', 'w+') as file:
        json.dump(data, file)
        file.close()
    return 1


async def latency_test(surb_run):
    count = 0
    freq = config.INIT_FREQ
    reply_surbs = list()
    duplicates = list()
    messages = list()
    label = "sent_text_time"
    print(config.RECEIVER_ADDRESS)

    # If test is to be done with SURBs
    if surb_run:
        # Read SURBs from file
        with open('prepared_surbs/surb.json', 'r') as f:
            surb_dict = json.load(f)
            reply_surbs = surb_dict['surbs']
            duplicates = surb_dict['duplicates']

        # label = "sent_text_with_surb_time"

        while freq <= config.MAX_FREQ:
            for i in range(MESSAGE_PER_TRIAL):
                messages.append({
                    'type': "reply",
                    'message': str(i) + ' ' + str(freq) + " surb_reply",
                    'replySurb': reply_surbs.pop()
                }
                )
            latency_data[label][freq] = dict()
            freq = round(freq + config.FREQ_STEP, 1)

        # Save unused SURBs back to the file
        with open('prepared_surbs/surb.json', 'w') as f:
            surb_dict = {'surbs': reply_surbs, 'duplicates': duplicates}
            json.dump(surb_dict, f)

        logging.info("[SENDER] **Starting sending messages *with* SURB**")
    
    # If test is to be done without SURBs
    else:
        # label = "sent_text_without_surb_time"
        while freq <= config.MAX_FREQ:
            for i in range(MESSAGE_PER_TRIAL):
                messages.append({
                    "type": "send",
                    "message": str(i) + ' ' + str(freq),
                    "recipient": config.RECEIVER_ADDRESS,
                    "withReplySurb": False,
                }
                )
            latency_data[label][freq] = dict()
            freq = round(freq + config.FREQ_STEP, 1)

        logging.info("[SENDER] **Starting sending messages *without* SURB**")

    freq = config.INIT_FREQ
    async with websockets.connect(config.SENDER_CLIENT_URI) as websocket:
        await websocket.send(self_address_request)
        self_address = json.loads(await websocket.recv())
        logging.info("[SENDER] Our address is: {}".format(
            self_address["address"]))

        while freq <= config.MAX_FREQ:
            while count < MESSAGE_PER_TRIAL:
                await websocket.send(json.dumps(messages.pop(0)))
                latency_data[label][freq][count] = (time.time())
                logging.info(
                    "[SENDER] Sent {} message with frequency {}".format(count, freq))

                count += 1

                time.sleep(1 / freq)

            logging.info(
                "[SENDER] Sent {} messages with frequency {}".format(count, freq))
            freq = round(freq + config.FREQ_STEP, 1)
            count = 0


async def load_text():
    start = 0
    end = 0
    messages = list()
    message_timings = dict()
    label = "sent_time"

    # Prepare the messages you will send
    if TEST_WITH_SURB:
        with open('prepared_surbs/surb.json', 'r') as f:
            reply_surbs = json.load(f)['surbs']
            print(len(reply_surbs))

        for i in range(MESSAGE_PER_TRIAL + 1):
            messages.append({
                'type': "reply",
                'message': str(i),
                'replySurb': reply_surbs.pop()
            }
            )
        
        # Save unused SURBs back to the file
        with open('prepared_surbs/surb.json', 'w') as f:
            surb_dict = {'surbs': reply_surbs}
            json.dump(surb_dict, f)

        logging.info("[SENDER] **Starting sending messages *with* SURB**")

    else:
        for i in range(MESSAGE_PER_TRIAL + 1):
            messages.append({
                "type": "send",
                "message": str(i),
                "recipient": config.RECEIVER_ADDRESS,
                "withReplySurb": False,
            }
            )

        logging.info("[SENDER] **Starting sending messages *without* SURB**")

    async with websockets.connect(config.SENDER_CLIENT_URI) as websocket:
        await websocket.send(self_address_request)
        self_address = json.loads(await websocket.recv())
        logging.info("[SENDER] Our address is: {}".format(
            self_address["address"]))

        # Send messages to the receiver
        #
        # The number of messages is MESSAGE_PER_TRIAL + 2, because in each sending-receiving round, the receiver
        # starts recoring the time once it receives a message. Effectively, to be able to measure the total time for
        # receiving MESSAGE_PER_TRIAL messages, the receiver has to receive at least MESSAGE_PER_TRIAL messages.
        #
        # We add +2 comes from fact that when measuring the time for receiving SURB replies, the same thing will happen
        # twice: once when the receiver receives the text messages, and once when the sender receives the SURB replies
        #

        for i in range(MESSAGE_PER_TRIAL + 1):
            message = messages.pop(0)
            await websocket.send(json.dumps(message))
            message_timings[message['message']] = time.time()
            # Start the timer on the first sent message
            if i == 0:
                start = time.time()
                message_timings[message['message']] = time.time()

        end = time.time()

        throughput_data[label] = end - start
        throughput_data['message_timings'] = message_timings
        logging.info(
            '[SENDER] It took {} seconds to send {} messages'.format(throughput_data[label], MESSAGE_PER_TRIAL))


async def send_large_text():
    with open('large_text.txt', 'r') as file:
        line = file.readline()

    print(line)

    text_send = {
        "type": "send",
        "message": line,
        "recipient": config.RECEIVER_ADDRESS,
        "withReplySurb": False,
    }

    async with websockets.connect(config.SENDER_CLIENT_URI) as websocket:
        await websocket.send(self_address_request)
        self_address = json.loads(await websocket.recv())
        logging.info('[SENDER] Our address is {}'.format(self_address))

        logging.info("[SENDER] **Starting sending message**")

        await websocket.send(json.dumps(text_send))


if TEST_TYPE == 'latency':
    # asyncio.get_event_loop().run_until_complete(send_text())
    asyncio.get_event_loop().run_until_complete(latency_test(TEST_WITH_SURB))
    save_to_file(latency_data)
elif TEST_TYPE == 'throughput':
    asyncio.get_event_loop().run_until_complete(load_text())
    save_to_file(throughput_data)


logging.info("[SENDER] Sender loop complete")
