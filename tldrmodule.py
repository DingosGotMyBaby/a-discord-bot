from textsum.summarize import Summarizer
import asyncio
from functools import wraps, partial

model = "philschmid/bart-large-cnn-samsum"

# load summarizer
summarizer = Summarizer(model_name_or_path=model,
                        token_batch_length=1024, use_cuda=False, max_length=100)

def wrap(func):
    @wraps(func)
    async def run(*args, loop=None, executor=None, **kwargs):
        if loop is None:
            loop = asyncio.get_event_loop()
        pfunc = partial(func, *args, **kwargs)
        return await loop.run_in_executor(executor, pfunc)
    return run

@wrap
def generate_summ(messages_to_summ: str):
    """
    Generates a summary of the input messages

    parameters:
    messages_to_summ: str
        The messages to summarize
    returns:
    full_summary: str
        The summary of the input messages
    """
    # Due to stupid design choices, we need to write our own wrapper for the summarizer
    # Calling summarize_string directly will output the string with tabs which we don't want
    # so easier to just write our own wrapper
    gen_summaries = summarizer.summarize_via_tokenbatches(
            messages_to_summ,
            batch_length=None, batch_stride=None) # type: ignore # function I call defaults to None so fuck it we ball
    sum_text = [s["summary"][0] for s in gen_summaries]
    full_summary = "\n".join(sum_text)
    return full_summary