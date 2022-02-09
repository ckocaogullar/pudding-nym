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
import signal

assert len(sys.argv) == 3, "Sender must take two parameters: name of the log file and the number of messages per trial"

MESSAGE_PER_TRIAL = int(sys.argv[2])
LOG_PATH = 'logs/' + sys.argv[1] + '/' + str(MESSAGE_PER_TRIAL)

logging.basicConfig(format='%(asctime)s - %(message)s', level=logging.INFO)


self_address_request = json.dumps({
    "type": "selfAddress"
})

data = {
    "sent_text_with_surb_time": dict(),
    "sent_text_without_surb_time": dict(),
    "received_surb_reply_text_time": dict(),

}


def save_to_file():
    logging.info('writing to file')

    if not os.path.exists('logs/' + sys.argv[1]):
        os.mkdir('logs/' + sys.argv[1])

    if not os.path.exists(LOG_PATH):
        os.mkdir(LOG_PATH)

    # if os.path.exists(LOG_PATH + '_sender.json'):
    #     with open(LOG_PATH + '_sender.json', 'a+') as file:
    #         output = json.loads(file.read())
    #         output.update({MESSAGE_PER_TRIAL: data})
    #         json.dump(output, file)
    # else:
    #     logging.error('[SENDER] Path does not exist')
    with open(LOG_PATH + '/sender.json', 'w+') as file:
        json.dump({MESSAGE_PER_TRIAL: data}, file)
        file.close()
    return 1


async def send_text():
    count = 0

    async with websockets.connect(config.SENDER_CLIENT_URI) as websocket:
        await websocket.send(self_address_request)
        self_address = json.loads(await websocket.recv())
        logging.info("[SENDER] Our address is: {}".format(
            self_address["address"]))

        text_send = {
            "type": "send",
            "message": str(count),
            "recipient": config.RECEIVER_ADDRESS,
            "withReplySurb": False,
        }

        # Send messages without SURB
        logging.info("[SENDER] **Starting sending messages *without* SURB**")
        while count < MESSAGE_PER_TRIAL:
            text_send['message'] = str(count)
            logging.info(
                "[SENDER] Sending '{}' (*without* reply SURB) over the mix network...".format(text_send['message']))
            await websocket.send(json.dumps(text_send))
            data["sent_text_without_surb_time"][count] = (time.time())
            logging.info(
                "[SENDER] Waiting to receive a message from the mix network...")
            try:
                received_message = json.loads(
                    await asyncio.wait_for(websocket.recv(), timeout=10))
            except asyncio.TimeoutError:
                received_message = {'type': 'timeout'}
            if received_message['type'] == 'error':
                logging.error(
                    "[SENDER] Received error message from the mix network: {}".format(received_message))
            elif received_message['type'] == 'timeout':
                logging.error('Timeout. Assuming ack was received.')
            else:
                logging.info(
                    "[SENDER] Received message from: {}".format(received_message['message']))
            count += 1

        count = 0

        # Send messages with SURB
        logging.info("[SENDER] **Starting sending messages *with* SURB**")
        text_send['withReplySurb'] = True
        while count < MESSAGE_PER_TRIAL:
            text_send['message'] = str(count)
            logging.info(
                "[SENDER] Sending '{}' (*with* reply SURB) over the mix network...".format(text_send['message']))
            await websocket.send(json.dumps(text_send))
            data["sent_text_with_surb_time"][count] = time.time()
            logging.info(
                "[SENDER] Waiting to receive a message from the mix network...")

            try:
                received_message = json.loads(
                    await asyncio.wait_for(websocket.recv(), timeout=10))
            except asyncio.TimeoutError:
                received_message = {'type': 'timeout'}

            if received_message['type'] == 'error':
                logging.error(
                    "[SENDER] Received error message from the mix network: {}".format(received_message))
            elif received_message['type'] == 'timeout':
                logging.error('Timeout. Assuming ack was received.')
                data["received_surb_reply_text_time"][count] = -1
            else:
                logging.info(
                    "[SENDER] Received message from: {}".format(received_message['message']))
                data['received_surb_reply_text_time'][count] = (time.time())
            count += 1

        count = 0

asyncio.get_event_loop().run_until_complete(send_text())
logging.info("[SENDER] Sender loop complete")

save_to_file()
