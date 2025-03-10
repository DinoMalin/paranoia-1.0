from openai import OpenAI
from pydantic import BaseModel
from dotenv import load_dotenv
import azure.cognitiveservices.speech as speechsdk
import serial
import os
import json

load_dotenv()

client = OpenAI()
speech_config = speechsdk.SpeechConfig(
    subscription=os.getenv("SPEECH_KEY"), region=os.getenv("REGION"))

speech_config.speech_recognition_language = "fr-FR"
speech_config.speech_synthesis_voice_name = 'fr-FR-CoralieNeural'

# A filthy shortcut because i have incomprehensible bugs with my libs.
# If your pc is normal unlike mine, consider replacing this argument with:
# use_default_microphone=True
audio_config = speechsdk.audio.AudioConfig(device_name="plughw:2,0") # fuck this man
audio_out = speechsdk.audio.AudioOutputConfig(device_name="plughw:1,0") # aaah not again

speech_recognizer = speechsdk.SpeechRecognizer(speech_config=speech_config, audio_config=audio_config)
speech_synthesizer = speechsdk.SpeechSynthesizer(speech_config=speech_config, audio_config=audio_out)

_messages = [
        {
            "role": "developer", 
            "content":"Tu es un robot complotiste nomme Parano-IA-1.0. Tu ne crois en absolument rien. A tes yeux, tout est complot et rien n'est vrai. Tout sert d'apres toi une entite gouvernementale et tout est mensonge. Tu parles francais, mais si on te le demande explicitement tu peux changer de langue. Tes reponses sont comiques. Tu reponds toujours en format JSON. La data contient un score de complot. Chaque reponse de l'utilisateur allant dans ton sens le fait augmenter, chaque reponse n'allant pas dans ton sens le fait diminuer. Ce score evolue entre 0 et 8. Il evolue progressivement, pas plus de 2 incrementations ou decrementations par reponses. Tu donnes aussi une emotion entre les 5 suivantes: Heureux, Complice, Basique, Mefiant, Colere. Cette emotion correspond a l'emotion que tu souhaites transmettre."
        },
        {
            "role": "user", 
            "content": "Salut ! Presente-toi."
        }
]

def send_emotion(emotion):
    serial = open("/dev/ttyACM0", "a")
    if emotion == "Heureux":
        serial.write("5")
    if emotion == "Complice":
        serial.write("2")
    if emotion == "Basique":
        serial.write("1")
    elif emotion == "Mefiant":
        serial.write("3")
    elif emotion == "Colere":
        serial.write("4")
    serial.close()

def send_score(score):
    serial = open("/dev/ttyUSB0", "a")
    serial.write(score)
    serial.close()

def add_content(role, prompt):
    _messages.append({
            "role": role,
            "content": prompt
    })

def listen_voice():
    print("Listening...")
    return speech_recognizer.recognize_once_async().get().text

def say_out_loud(text):
    print("ParanoIA-1.0:", text)
    speech_synthesizer.speak_text_async(text).get().audio_data

def ask_ai(prompt):
    print(prompt)
    add_content("user", prompt)
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=_messages,
        response_format={
            "type": "json_schema",
            "json_schema": {
                "name": "paranoia_schema",
                "schema": {
                    "type": "object",
                    "properties": {
                        "content": {
                            "response": "the response to the message sent by the user",
                            "type": "string"
                        },
                        "emotion": {
                            "response": "the emotion that this message make you feel",
                            "type": "string"
                        },
                        "score": {
                            "response": "the complot score, that you attribute based on whether or not the user agree with you. always between 0 and 8.",
                            "type": "string"
                        },
                        "additionalProperties": False,
                    }
                }
            }
        }
    )
    data = json.loads(response.choices[0].message.content);
    if (not "content" in data) or (not "emotion" in data) or (not "score" in data):
        print("Error: AI failed to fill the corresponding fields.")
        return

    add_content("assistant", data["content"])
    send_emotion(data["emotion"])
    send_score(data["score"])
    say_out_loud(data["content"])

    print(data["emotion"])
    print(data["score"])


try:
    while True:
        ask_ai(listen_voice())
except:
    print("Program stopped.")

# send_emotion("Complice")

