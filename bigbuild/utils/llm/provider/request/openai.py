import signal
import time

import openai
from openai.types.chat import ChatCompletion

from bigbuild.utils.llm.provider.request import construct_message_list


def make_request(
    client: openai.Client,
    message: str,
    model: str,
    max_tokens: int = 512,
    temperature: float = 1,
    n: int = 1,
    system_msg="You are a helpful assistant good at coding.",
    **kwargs,
) -> ChatCompletion:
    return client.chat.completions.create(
        model=model,
        messages=construct_message_list(message, system_message=system_msg),
        max_tokens=max_tokens,
        temperature=temperature,
        n=n,
        **kwargs,
    )


def handler(signum, frame):
    # swallow signum and frame
    raise Exception("end of time")


def make_auto_request(*args, **kwargs) -> ChatCompletion:
    ret = None
    retry = 0
    max_try = 3
    while ret is None and retry < max_try:
        try:
            signal.signal(signal.SIGALRM, handler)
            signal.alarm(10)
            ret = make_request(*args, **kwargs)
            signal.alarm(0)
        except Exception as e:
            print(e)
            signal.alarm(0)
            time.sleep(5)
        except openai.RateLimitError:
            print("Rate limit exceeded. Waiting...")
            signal.alarm(0)
            time.sleep(5)
        except openai.APIConnectionError:
            print("API connection error. Waiting...")
            signal.alarm(0)
            time.sleep(5)
        except openai.APIError as e:
            if e.code == 400 or "reduce the length of the messages" in e.message:
                print(
                    "Error: Input exceeds the maximum context length allowed by the model."
                )
                break
            else:
                print("Unknown API error")
                print(e)
        except Exception as e:
            print("Unknown error. Waiting...")
            print(e)
            signal.alarm(0)
            time.sleep(5)
        retry += 1
    return ret
