import asyncio
from cmath import e
import json
from operator import xor
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
assert len(sys.argv) >= 2, "Sender must take at least two parameters: name of the log file and the number of messages per trial"

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
MESSAGE_PER_TRIAL = int(sys.argv[2])

surb_folder = None
if TEST_WITH_SURB:
    surb_folder = 'with_surb/'
else:
    surb_folder = 'without_surb/'

LOG_PATH = 'test_logs/' + sys.argv[1] + '/' + surb_folder


# For storing the test results on the run
latency_data = {"sent_text_time": dict(), }

# The program needs make a self-address query to the client before it starts sending messages
self_address_request = json.dumps({
    "type": "selfAddress"
})


def save_to_file(data):
    logging.info('[SENDER] Writing to file')

    if not os.path.exists('test_logs/'):
        os.mkdir('test_logs/')

    if not os.path.exists('test_logs/' + sys.argv[1]):
        os.mkdir('test_logs/' + sys.argv[1])

    if not os.path.exists(LOG_PATH):
        os.mkdir(LOG_PATH)

    with open(LOG_PATH + '/sender.json', 'w+') as file:
        json.dump(data, file)
        file.close()


def prepare_messages(with_surb, reply_surbs=None):
    assert bool(with_surb) == bool(
        reply_surbs), "You must provide reply_surbs if you want me to prepare you messages with SURBs. Otherwise, no need to provide that."

    messages = list()
    freq = config.INIT_FREQ

    while freq <= config.MAX_FREQ:
        for i in range(MESSAGE_PER_TRIAL):
            if with_surb:
                message = {
                    'type': "reply",
                    'message': str(i) + ' ' + str(freq) + " surb_reply",
                    'replySurb': reply_surbs.pop()
                }
            else:
                message = {
                    "type": "send",
                    "message": str(i) + ' ' + str(freq),
                    "recipient": config.RECEIVER_ADDRESS,
                    "withReplySurb": False,
                }
            messages.append(message)

        latency_data['sent_text_time'][freq] = dict()
        freq = round(freq + config.FREQ_STEP, 1)
    return messages


async def send_messages(surb_run):
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

        messages = prepare_messages(True, reply_surbs)

        # Save unused SURBs back to the file
        with open('prepared_surbs/surb.json', 'w') as f:
            surb_dict = {'surbs': reply_surbs, 'duplicates': duplicates}
            json.dump(surb_dict, f)

        logging.info("[SENDER] **Starting sending messages *with* SURB**")

    # If test is to be done without SURBs
    else:
        messages = prepare_messages(False)

        logging.info("[SENDER] **Starting sending messages *without* SURB**")

    async with websockets.connect(config.SENDER_CLIENT_URI) as websocket:
        await websocket.send(self_address_request)
        self_address = json.loads(await websocket.recv())
        logging.info("[SENDER] Our address is: {}".format(
            self_address["address"]))

        while freq <= config.MAX_FREQ:
            for count in range(MESSAGE_PER_TRIAL):
                await websocket.send(json.dumps(messages.pop(0)))
                latency_data[label][freq][count] = (time.time())
                logging.info(
                    "[SENDER] Sent message {} with frequency {}".format(count, freq))

                time.sleep(1 / freq)

            logging.info(
                "[SENDER] Sent all {} messages with frequency {}".format(count, freq))
            freq = round(freq + config.FREQ_STEP, 1)


# A function I wrote to test what happens if I send a very large payload. Answer is, the client seamlessly splits it into
# multiple packets and the program does not experience any disruption. Just as promised in the docs. It naturally takes
# longer to than to send a small payload
async def send_large_text():
    with open('large_text.txt', 'r') as file:
        line = file.readline()

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


asyncio.get_event_loop().run_until_complete(send_messages(TEST_WITH_SURB))
save_to_file(latency_data)

logging.info("[SENDER] Sender loop complete")
