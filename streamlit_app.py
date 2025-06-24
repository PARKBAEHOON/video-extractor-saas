# streamlit_app.py - SaaS용 영상 자동 추출 앱 (서버 호환 버전)

import streamlit as st
import os
from datetime import datetime
from pathlib import Path
import whisper
from yt_dlp import YoutubeDL

# 영상 다운로드 함수 (yt_dlp API 사용)
def download_video(url, output_dir, resolution='best'):
    ydl_opts = {
        'format': resolution,
        'outtmpl': f'{output_dir}/video.%(ext)s',
        'merge_output_format': 'mp4',
        'quiet': True
    }
    with YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])

# 자막 생성 (Whisper)
def generate_subtitles(video_path, subtitle_path, model_size='base'):
    model = whisper.load_model(model_size)
    result = model.transcribe(video_path)
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
st.title("📽️ 영상 + Whisper 자막 생성기")
st.write("유튜브 또는 틱톡 영상 URL을 입력하면 자동으로 영상과 자막을 생성합니다.")

url = st.text_input("🎞 영상 URL 입력")
resolution = st.selectbox("📐 해상도 선택", ["best", "720p", "360p"])
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
            subtitle_path = os.path.join(folder_name, 'subtitle.srt')

            try:
                download_video(url, folder_name, resolution)
                generate_subtitles(video_path, subtitle_path, model_size=whisper_model)

                st.success("✅ 처리 완료!")

                if os.path.exists(video_path):
                    st.video(video_path)
                    with open(video_path, 'rb') as f:
                        st.download_button("📥 영상 다운로드", f, file_name="video.mp4")

                if os.path.exists(subtitle_path):
                    with open(subtitle_path, 'rb') as f:
                        st.download_button("📝 자막 다운로드 (.srt)", f, file_name="subtitle.srt")

            except Exception as e:
                st.error(f"에러 발생: {str(e)}")
