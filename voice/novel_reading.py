import os
from openai import OpenAI

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

text = """서울역에서... 엄마가 사라진 건, 일주일 전이었다.

아버지와 함께 서울에 올라온 엄마는, 지하철을 갈아타는 사이에 아버지의 손을 놓쳤다. 아버지는 사람들에 떠밀려 전동차에 올랐고... 문이 닫혔다. 아버지가 돌아보았을 때, 플랫폼에 서 있던 엄마는... 이미, 사라지고 없었다.

너는 그 소식을 듣고도... 바로 달려가지 않았다. 내일 가야지. 내일. 그렇게 사흘을 미뤘다. 엄마가 길을 잃는다는 건... 상상조차 해본 적이 없었으니까. 엄마는, 늘 거기 있었으니까. 부엌에서. 마당에서. 논밭에서. 불러도 대답 없을 때조차... 어딘가에 반드시 있는 사람이었으니까.

그런데 지금... 엄마가 없다.

그제야 너는 깨달았다. 네가 마지막으로 엄마에게 전화한 게... 언제였는지. 설이었나. 아니, 추석이었나. 기억나지 않았다. 기억나지 않는다는 게... 목을 조여왔다."""

output_path = "/home/ubuntu/.cokacdir/workspace/pfiuywu4/novel_reading_v2.mp3"

with client.audio.speech.with_streaming_response.create(
    model="gpt-4o-mini-tts",
    voice="nova",
    input=text,
    instructions="""You are reading a Korean novel passage alone, late at night, to one person sitting close by.
Imagine you are in a dim room, reading softly by lamplight.

Voice quality:
- Speak VERY softly. Almost a whisper at times, but always audible.
- Your voice should feel like it's coming from right next to the listener's ear.
- Breathy, intimate, gentle. Like telling a secret that hurts.
- Do NOT project your voice. Keep it close, personal, small.

Pacing:
- Extremely slow. Half the speed of normal conversation.
- Every period (.) is a full 1.5 second pause. Every "..." is 2 seconds of silence.
- Let the words hang in the air before moving to the next sentence.
- Between paragraphs, pause for 3 seconds. Let the listener absorb.

Emotional arc:
- Opening ("서울역에서..."): Start barely above a whisper. A memory surfacing.
- Subway scene: Slightly more present, but still soft. The closing doors — a tiny catch in your breath.
- "이미, 사라지고 없었다": Whisper this. Almost inaudible. The void.
- "내일 가야지. 내일.": Casual, dismissive — but your voice should betray that you know now how wrong this was. Quiet self-blame.
- "엄마는, 늘 거기 있었으니까": The warmest moment. Tender. Remember her with love. Slow, gentle, like touching something fragile.
- "부엌에서. 마당에서. 논밭에서.": Each place is its own memory. Pause between each. See each place in your mind.
- "그런데 지금... 엄마가 없다": The simplest sentence. Say it plainly. No drama. The plainness IS the devastation. A long, long pause after.
- Final paragraph: Your voice should tighten. Not crying — but the throat closing. "기억나지 않았다" — say it slowly, each syllable heavy. The last line should feel like you can barely get the words out.

Critical: Do NOT sound like a professional narrator or audiobook reader. Sound like a real person, alone, reading words that are breaking their heart. Imperfect. Human. Vulnerable.""",
) as response:
    response.stream_to_file(output_path)

print(f"Saved: {output_path}")
