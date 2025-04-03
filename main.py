# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "azure-cognitiveservices-speech",
#     "python-dotenv",
#     "sounddevice",
#     "soundfile",
#     "pydub",
# ]
# ///

import os
import sys
import uuid
import tempfile
import sounddevice as sd
import soundfile as sf
from pydub import AudioSegment
from dotenv import load_dotenv
import azure.cognitiveservices.speech as speechsdk

load_dotenv()

MICROSOFT_TOKEN = os.getenv("MICROSOFT_TOKEN")
MICROSOFT_REGION = os.getenv("MICROSOFT_REGION")


def record_audio(filename, samplerate=16000, channels=1):
    print("Press Enter to start recording...")
    input()
    print("Recording... Press Enter to stop.")
    recording = []

    def callback(indata, frames, time_info, status):
        recording.append(indata.copy())

    with sd.InputStream(samplerate=samplerate, channels=channels, callback=callback):
        input()
    print("Recording stopped.")

    with sf.SoundFile(filename, mode="w", samplerate=samplerate, channels=channels, subtype="PCM_16") as f:
        for chunk in recording:
            f.write(chunk)
    return filename


def convert_mp3_to_wav(mp3_path):
    print(f"Converting MP3 to WAV: {mp3_path}")
    sound = AudioSegment.from_mp3(mp3_path)
    temp_wav = os.path.join(tempfile.gettempdir(), f"{uuid.uuid4().hex}.wav")
    sound.export(temp_wav, format="wav")
    return temp_wav


def transcribe_from_file(filename):
    speech_config = speechsdk.SpeechConfig(subscription=MICROSOFT_TOKEN, region=MICROSOFT_REGION)
    audio_config = speechsdk.audio.AudioConfig(filename=filename)

    speech_recognizer = speechsdk.SpeechRecognizer(speech_config=speech_config, audio_config=audio_config)
    print("Transcribing...")
    result = speech_recognizer.recognize_once()
    if result.reason == speechsdk.ResultReason.RecognizedSpeech:
        print(f"Recognized: {result.text}")
        return result.text
    elif result.reason == speechsdk.ResultReason.NoMatch:
        print("No speech could be recognized.")
    elif result.reason == speechsdk.ResultReason.Canceled:
        cancellation = result.cancellation_details
        print(f"Canceled: {cancellation.reason}")
    return None


def synthesize_speech(text):
    speech_config = speechsdk.SpeechConfig(subscription=MICROSOFT_TOKEN, region=MICROSOFT_REGION)
    audio_config = speechsdk.audio.AudioOutputConfig(use_default_speaker=True)
    synthesizer = speechsdk.SpeechSynthesizer(speech_config=speech_config, audio_config=audio_config)

    print(f"Synthesizing: {text}")
    result = synthesizer.speak_text_async(text).get()
    if result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
        print("Speech synthesis completed.")
    else:
        print(f"Speech synthesis failed: {result.reason}")


def main():
    temp_wav = None

    if len(sys.argv) > 1:
        input_file = sys.argv[1]
        if input_file.lower().endswith(".mp3"):
            temp_wav = convert_mp3_to_wav(input_file)
            wav_file = temp_wav
        elif input_file.lower().endswith(".wav"):
            wav_file = input_file
        else:
            print("Unsupported file type. Please provide an MP3 or WAV file.")
            return
    else:
        wav_file = os.path.join(tempfile.gettempdir(), f"recording_{uuid.uuid4().hex}.wav")
        record_audio(wav_file)

    try:
        transcription = transcribe_from_file(wav_file)
        if transcription:
            synthesize_speech(transcription)
    finally:
        if temp_wav and os.path.exists(temp_wav):
            os.remove(temp_wav)
        elif not len(sys.argv) > 1 and os.path.exists(wav_file):
            os.remove(wav_file)


if __name__ == "__main__":
    main()