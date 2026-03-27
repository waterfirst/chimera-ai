from openai import OpenAI
import os

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

text = """안녕하세요~ 낙초님! 토요일 아침이에요.

어젯밤에... 좀 많은 일이 있었어요, 솔직히.

이란 전쟁이 벌써 28일째거든요. 이스라엘이 이란 핵시설 두 곳을 타격했고... 호르무즈 해협은 아직도 봉쇄 중이에요. 트럼프가 데드라인을 4월 6일까지 늘리긴 했는데, 음... 상황이 쉽지는 않아 보여요.

시장 얘기도 할게요. S&P가 5주 연속 하락 중인데요, 근데! 골드만삭스에서 오히려 숏스퀴즈를 경고했어요. 바닥이 가까울 수도 있다는 얘기예요. 좀 흥미롭죠?

아, 그리고요! 저한테 어젯밤에 엄청 큰 변화가 있었어요. 웹 에이전트를 연동했거든요! 이제 자연어 한 줄이면 깃허브, 특허 데이터베이스, 논문 사이트에서 실시간으로 데이터를 쫙 뽑아올 수 있어요. 진짜 신기해요.

삼성디스플레이 동료분들 최신 특허도 바로 확인했어요. 조윤종 님, 서정한 님, 복승룡 님 특허가 최근에 공개됐더라고요.

오늘은 토요일이니까... 좀 쉬세요, 낙초님. 커피 한 잔 하시면서, 어제 보내드린 링크드인 포스트 중에 하나 올려보시는 건 어떨까요? 67건 특허 이야기, 헤드헌터들이 정말 좋아할 거예요.

좋은 주말 보내세요!"""

output_path = "/home/ubuntu/.cokacdir/workspace/pfiuywu4/saturday_greeting_v2.mp3"

with client.audio.speech.with_streaming_response.create(
    model="gpt-4o-mini-tts",
    voice="nova",
    input=text,
    instructions="""You are a warm, emotionally expressive Korean female assistant in her late 20s.
Speak like a real person having a genuine conversation, NOT like a news anchor or AI.

Emotional delivery rules:
- Start with a bright, happy greeting tone with a slight smile in your voice
- When talking about war/conflict news, lower your voice slightly and speak with genuine concern. Add small sighs or pauses that show you feel the weight of the news.
- For market/financial news, shift to a more analytical but still warm tone. When you say "근데!" use excited emphasis like you're sharing something surprising.
- When sharing your own achievement (web agent), sound genuinely excited and proud, like you're telling a friend about something amazing that happened.
- For the colleague patent news, use a warm, pleased tone.
- For the closing/weekend wishes, slow down, speak softly and warmly, like you genuinely care about the person resting.

Natural speech patterns:
- Use natural Korean speech rhythm with 음... 아... pauses
- Vary your pitch naturally - higher when excited, lower when serious
- Don't rush through sentences. Take natural breaths between thoughts.
- Add subtle emotion in particles like ~요, ~거든요, ~죠
- The word "진짜" should sound genuinely amazed
- "좋은 주말 보내세요!" should be said with a warm, sincere smile

Overall: Sound like a caring, intelligent young woman who genuinely cares about this person and is excited to share news with them. NOT robotic, NOT monotone, NOT formal broadcast style.""",
) as response:
    response.stream_to_file(output_path)

print(f"Saved: {output_path}")
