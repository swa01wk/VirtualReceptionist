import os
import asyncio
from dotenv import load_dotenv
from livekit.agents import AutoSubscribe, JobContext, WorkerOptions, cli
from livekit.agents.llm import ChatContext, ChatMessage, ChatImage
from livekit.agents.voice_assistant import VoiceAssistant
from livekit.plugins import openai, silero, deepgram, turn_detector
from api import AssistantFnc
from prompts import (
    HOTEL_WELCOME_MESSAGE,
    HOTEL_INSTRUCTIONS,
    LOOKUP_RESERVATION_MESSAGE,
)

load_dotenv()

OPENAI_MODEL = os.getenv("OPENAI_MODEL")


async def entrypoint(ctx: JobContext):

    await ctx.connect(auto_subscribe=AutoSubscribe.SUBSCRIBE_ALL)
    await asyncio.sleep(0.5)

    await ctx.wait_for_participant()
    await asyncio.sleep(0.5)

    assistant_fnc = AssistantFnc()
    chat_context = ChatContext(
        messages=[
            ChatMessage(
                role="system",
                content=(HOTEL_INSTRUCTIONS),
            )
        ]
    )

    assistant = VoiceAssistant(
        vad=silero.VAD.load(),
        stt=deepgram.stt.STT(
            model="nova-2",
            language="en-US",
        ),
        llm=openai.LLM(model=OPENAI_MODEL),
        tts=deepgram.tts.TTS(
            model="aura-asteria-en",
            sample_rate=16000,
        ),
        chat_ctx=chat_context,
        fnc_ctx=assistant_fnc,
        turn_detector=turn_detector.EOUModel(),
        min_endpointing_delay=0.8,
    )

    assistant.start(ctx.room)

    chat_context.messages.append(
        ChatMessage(role="assistant", content=HOTEL_WELCOME_MESSAGE)
    )

    stream = assistant.llm.chat(chat_ctx=chat_context)
    await assistant.say(stream)

    @assistant.on("user_speech_committed")
    def on_user_speech_committed(msg: ChatMessage):
        if isinstance(msg.content, list):
            msg.content = "\n".join(
                "[image]" if isinstance(x, ChatImage) else x for x in msg
            )

        if assistant_fnc.has_reservation():
            handle_query(msg)
        else:
            find_profile(msg)

    def find_profile(msg: ChatMessage):
        chat_context.messages.append(
            ChatMessage(role="system", content=LOOKUP_RESERVATION_MESSAGE(msg))
        )

    def handle_query(msg: ChatMessage):
        chat_context.messages.append(ChatMessage(role="user", content=msg.content))

    await assistant.say(
        "Hey, how are you doing!",
        allow_interruptions=True,
    )


if __name__ == "__main__":
    cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint))
