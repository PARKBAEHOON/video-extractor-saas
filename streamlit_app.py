# streamlit_app.py - SaaS용 영상 자동 추출 앱

import streamlit as st
import os
import subprocess
from datetime import datetime
from pathlib import Path
import whisper

# 세션 상태 초기화
if "extracted" not in st.session_state:
    st.session_state.extracted = False
    st.session_state.video_path = ""
    st.session_state.audio_path = ""
    st.session_state.subtitle_path = ""

# 영상 다운로드 함수
def download_video(url, output_dir, resolution='best'):
    ytdlp_cmd = [
        "yt-dlp",
        "-f", resolution,
        "--write-auto-sub",
        "--sub-lang", "ko,en",
        "--convert-subs", "srt",
        "--merge-output-format", "mp4",
        "-o", f"{output_dir}/video.%(ext)s",
        url
    ]
    subprocess.run(ytdlp_cmd, check=True)

# 오디오 추출
def extract_audio(video_path, audio_path):
    cmd = ["ffmpeg", "-y", "-i", video_path, "-vn", "-acodec", "mp3", audio_path]
    subprocess.run(cmd, check=True)

# 자막 생성 (Whisper)
def generate_subtitles(audio_path, subtitle_path, model_size='base'):
    model = whisper.load_model(model_size)
    result = model.transcribe(audio_path)
    with open(subtitle_path, 'w', encoding='utf-8') as f:
        for segment in result["segments"]:
            start = segment['start']
            end = segment['end']
            text = segment['text'].strip()
            f.write(f"{format_time(start)} --> {format_time(end)}\n{text}\n\n")

# 자막용 시간 포맷
def format_time(seconds):
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    ms = int((seconds - int(seconds)) * 1000)
    return f"{h:02}:{m:02}:{s:02},{ms:03}"

# Streamlit UI 구성
st.title("📽️ 영상 추출 + Whisper 자막 생성기")
st.write("유튜브 또는 틱톡 영상 URL을 입력하면, 자동으로 영상/오디오/자막을 추출합니다.")

url = st.text_input("🎞 영상 URL 입력")
resolution = st.selectbox("📐 해상도 선택", ["best", "720p", "360p"])
whisper_enabled = st.checkbox("📝 자막 생성 (Whisper 사용)", value=True)
whisper_model = st.selectbox("🧠 Whisper 모델 선택", ["tiny", "base", "small", "medium", "large"])

if st.button("▶ 자동 추출 시작"):
    if not url:
        st.error("URL을 입력해주세요!")
    else:
        with st.spinner("처리 중입니다... 최대 1~3분 소요"):
            today = datetime.now().strftime('%Y-%m-%d_%H%M%S')
            folder_name = f"extracted/{today}"
            Path(folder_name).mkdir(parents=True, exist_ok=True)

            video_path = os.path.join(folder_name, 'video.mp4')
            audio_path = os.path.join(folder_name, 'audio.mp3')
            subtitle_path = os.path.join(folder_name, 'subtitle.srt')

            try:
                download_video(url, folder_name, resolution)
                extract_audio(video_path, audio_path)

                if whisper_enabled:
                    generate_subtitles(audio_path, subtitle_path, model_size=whisper_model)

                st.session_state.extracted = True
                st.session_state.video_path = video_path
                st.session_state.audio_path = audio_path
                st.session_state.subtitle_path = subtitle_path

                st.success("✅ 처리 완료!")

            except Exception as e:
                st.error(f"에러 발생: {str(e)}")

# 추출이 완료된 경우 다운로드 버튼 표시
if st.session_state.extracted:
    if os.path.exists(st.session_state.video_path):
        st.video(st.session_state.video_path)
        with open(st.session_state.video_path, 'rb') as f:
            st.download_button("📥 영상 다운로드", f, file_name="video.mp4")

    if os.path.exists(st.session_state.audio_path):
        with open(st.session_state.audio_path, 'rb') as f:
            st.download_button("🎧 오디오 다운로드", f, file_name="audio.mp3")

    if whisper_enabled and os.path.exists(st.session_state.subtitle_path):
        with open(st.session_state.subtitle_path, 'rb') as f:
            st.download_button("📝 자막 다운로드 (.srt)", f, file_name="subtitle.srt")
