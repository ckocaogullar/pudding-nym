import asyncio
import websockets
import json
import time
import pandas as pd
from datetime import datetime


data = {
    "sent_surb_reply_text_time": [],
    "received_text_time": [],
    "received_surb_text_time": []
}

log_folder = datetime.now().strftime("%d/%m/%Y%:H%M%S")

self_address_request = json.dumps({
    "type": "selfAddress"
})


async def reply_text_with_surb():
    uri = "ws://localhost:1978"
    count = 0

    async with websockets.connect(uri) as websocket:
        while count < 20:
            await websocket.send(self_address_request)
            self_address = json.loads(await websocket.recv())
            print("our address is: {}".format(self_address["address"]))

            print("waiting to receive a message from the mix network...")
            received_message = json.loads(await websocket.recv())
            print("received '{}' from the mix network".format(received_message))
            message_received = time.time()
            # use the received surb to send an anonymous reply!
            reply_surb = received_message["replySurb"]
            reply_message = "hello from reply SURB!"

            if received_message["replySurb"]:
                data["received_surb_text_time"].append(message_received)
                reply = json.dumps({
                    "type": "reply",
                    "message": reply_message,
                    "replySurb": reply_surb
                })

                print("sending '{}' (using reply SURB!) over the mix network...".format(
                    reply_message))
                await websocket.send(reply)
                data["sent_surb_reply_text_time"] = time.time()

            else:
                data["received_text_time"].append(message_received)
                text_send = json.dumps({
                    "type": "send",
                    "message": reply_message,
                    "recipient": "FkwoDAdNkjLqgchPQEeSKGK5FaBWP8p7vLJMozFd7PdB.8q7XU4qch8KKGYk3b6o4NYJpniUUUogDwxLMZu8avSKX@CbxxDmmNCufXSsi7hqUnorchtsqqSLSZp7QfRJ5ugSRA",
                    "withReplySurb": True,
                })
                print("received text message without surb; time:",
                      data["received_text_time"][count])
                await websocket.send(text_send)
                print("Reply sent without Surb")

            count += 1


loop = asyncio.get_event_loop()
try:
    asyncio.ensure_future(reply_text_with_surb())
    loop.run_forever()
except KeyboardInterrupt:
    pass
finally:
    print("Closing Loop")
    df = pd.DataFrame(data)
    os.makedirs('logs/' + log_folder, exist_ok=True)
    df.to_csv('logs/' + log_folder + 'receiver.csv')
    loop.close()
