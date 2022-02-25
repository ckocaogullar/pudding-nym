import asyncio
from cmath import e
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
assert len(sys.argv) >= 3, "Receiver must take at least three parameters: test type (latency or throughput), name of the log file and the number of messages per trial"
assert sys.argv[2] == 'throughput' or sys.argv[2] == 'latency', "Test type must be 'throughput' or 'latency'"
throughput_with_surb = None
if sys.argv[2] == 'throughput':
    for i in range(len(sys.argv) - 1):
        if sys.argv[i] == '--surb':
            throughput_with_surb = sys.argv[i+1]
        if throughput_with_surb == None:
            assert "Must provide is throughput test will be using SURB or not. Please do so using a --surb flag. Allowed inputs are 'TRUE' and 'FALSE'"
        else:
            assert throughput_with_surb == 'TRUE' or throughput_with_surb == 'FALSE', "Allowed inputs for the --surb flag are are 'TRUE' and 'FALSE'"

# Set constants
THROUGHPUT_WITH_SURB = throughput_with_surb
MESSAGE_PER_TRIAL = int(sys.argv[3])
TEST_TYPE = sys.argv[2]

surb_folder = None

if TEST_TYPE == 'latency':
    surb_folder = ''
elif TEST_TYPE == 'throughput':
    if THROUGHPUT_WITH_SURB == 'TRUE':
        surb_folder = 'with_surb/'
    else:
        surb_folder = 'without_surb/'

LOG_PATH = TEST_TYPE + '_logs/' + \
    sys.argv[1] + '/' + surb_folder + str(MESSAGE_PER_TRIAL)

# For storing the test results on the run
latency_data = {
    "sent_surb_reply_text_time": dict(),
    "received_text_time": dict(),
    "received_surb_text_time": dict()
}
throughput_data = dict()

# The program needs make a self-address query to the client before it starts sending messages
self_address_request = json.dumps({
    "type": "selfAddress"
})


def save_to_file(data):
    logging.info('[RECEIVER] Writing to file')

    if not os.path.exists(TEST_TYPE + '_logs/' + sys.argv[1]):
        os.mkdir(TEST_TYPE + '_logs/' + sys.argv[1])

    if not os.path.exists(TEST_TYPE + '_logs/' + sys.argv[1] + '/' + surb_folder):
        os.mkdir(TEST_TYPE + '_logs/' + sys.argv[1] + '/' + surb_folder)

    if not os.path.exists(LOG_PATH):
        os.mkdir(LOG_PATH)

    with open(LOG_PATH + '/receiver.json', 'w+') as file:
        # json.dump({MESSAGE_PER_TRIAL: data}, file)
        json.dump(data, file)
        file.close()


async def reply_text():
    count = 0
    seq_num = 0

    async with websockets.connect(config.RECEIVER_CLIENT_URI) as websocket:
        await websocket.send(self_address_request)
        self_address = json.loads(await websocket.recv())
        logging.info("[RECEIVER] Our address is: {}".format(
            self_address['address']))

        while count < MESSAGE_PER_TRIAL * config.NUM_TRIALS:
            logging.info(
                "[RECEIVER] Waiting to receive a message from the mix network...")

            try:
                received_message = json.loads(
                    await asyncio.wait_for(websocket.recv(), timeout=20))
            except asyncio.TimeoutError:
                received_message = {'type': 'timeout'}

            message_received = time.time()
            if received_message['type'] == 'error':
                logging.error(
                    "[RECEIVER] Received error message from the mix network: {}".format(received_message))
            elif received_message['type'] == 'timeout':
                logging.error(
                    '[RECEIVER] Timeout. Assuming ack was received.')
            else:
                logging.info(
                    "[RECEIVER] Received message from the mix network: {}".format(received_message['message']))

                # use the received surb to send an anonymous reply!
                reply_surb = received_message["replySurb"]
                seq_num = received_message['message']

                if reply_surb:
                    latency_data['received_surb_text_time'][seq_num] = (
                        message_received)
                    text_send = json.dumps({
                        'type': "reply",
                        'message': seq_num + '.with_surb',
                        'replySurb': reply_surb
                    })

                    logging.info(
                        "[RECEIVER] Sending '{}' over the mix network, *using* reply SURB".format(seq_num))
                    await websocket.send(text_send)
                    latency_data['sent_surb_reply_text_time'][seq_num] = (
                        time.time())

                else:
                    latency_data['received_text_time'][seq_num] = (
                        message_received)
                    text_send = json.dumps({
                        'type': "send",
                        'message': seq_num,
                        'recipient': config.SENDER_ADDRESS[0],
                        'withReplySurb': True,
                    })
                    await websocket.send(text_send)
                    logging.info(
                        "[RECEIVER] Reply '{}' sent, *not using* a SURB".format(seq_num))

                count += 1


async def receive_text():
    global latency_data
    count = 0

    async with websockets.connect(config.RECEIVER_CLIENT_URI) as websocket:
        await websocket.send(self_address_request)
        self_address = json.loads(await websocket.recv())
        logging.info("[RECEIVER] Our address is: {}".format(
            self_address['address']))
        start = time.time()
        if THROUGHPUT_WITH_SURB == 'FALSE':
            while count < MESSAGE_PER_TRIAL:
                await websocket.recv()
                # logging.info("[RECEIVER] Received message number {}".format(count))
                count += 1
        else:
            received_messages = list()
            while count < MESSAGE_PER_TRIAL:
                received_messages.append(await websocket.recv())
                # logging.info("[RECEIVER] Received message number {}".format(count))
                count += 1

        end = time.time()

        if THROUGHPUT_WITH_SURB == 'TRUE':
            throughput_data["received_text_with_surb_time"] = end - start
            logging.info(
                '[RECEIVER] It took {} seconds to receive {} messages *with* SURB'.format(throughput_data["received_text_with_surb_time"], MESSAGE_PER_TRIAL))
            logging.info('[RECEIVER] Sending SURBs back')
            received_messages = [json.loads(msg)['replySurb']
                                 for msg in received_messages]
            surb_replies = [json.dumps({
                    'type': "reply",
                            'message': str(count),
                            'replySurb': reply_surb
                }) for reply_surb in received_messages]
            
            start = time.time()
            
            for reply_surb in surb_replies:
                await websocket.send(reply_surb)
            end = time.time()
            
            logging.info('[RECEIVER] Receiver has sent {} SURB reply messages'.format(
                len(received_messages)))
            throughput_data["sent_surb_time"] = end - start
        else:
            throughput_data["received_text_without_surb_time"] = end - start
            logging.info(
                '[RECEIVER] It took {} seconds to receive {} messages *without* SURB'.format(throughput_data["received_text_without_surb_time"], MESSAGE_PER_TRIAL))


if TEST_TYPE == 'latency':
    asyncio.get_event_loop().run_until_complete(reply_text())
    save_to_file(latency_data)
elif TEST_TYPE == 'throughput':
    asyncio.get_event_loop().run_until_complete(receive_text())
    save_to_file(throughput_data)
logging.info("[RECEIVER] Receiver loop complete")
