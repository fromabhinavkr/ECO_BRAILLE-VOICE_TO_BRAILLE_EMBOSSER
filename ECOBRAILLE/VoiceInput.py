import os
import speech_recognition as sr
import pyttsx3

def main():
    r = sr.Recognizer()
    engine = pyttsx3.init()

    # Adjusting for ambient noise
    with sr.Microphone() as source:
        print("Adjusting for ambient noise. Please wait...")
        r.adjust_for_ambient_noise(source)  # Adjusting for 5 seconds
        
    # Listening for input
    with sr.Microphone() as source:
        print("Please say something")
        engine.say("Please say something")
        engine.runAndWait()
        audio = r.listen(source)

    # Attempting to recognize speech
    try:
        print("Recognizing Now .... ")
        engine.say("Recognizing Now .... ")
        engine.runAndWait()
        
        recognized_text = r.recognize_google(audio)
        print("You have said:\n", recognized_text)
        engine.say("You have said:\n" + recognized_text)
        engine.runAndWait()
        
        # Specifying the directory where you want to save the file
        directory = "/home/nappu"
        filename = "voice_input.txt"
        filepath = os.path.join(directory, filename)
        
        # Writing recognized text to file
        with open(filepath, "w") as text_file:
            text_file.write(recognized_text)
        print("Recognized text saved to:", filepath)
        # engine.say("Recognized text saved to " + filepath)
        # engine.runAndWait()

    except sr.UnknownValueError:
        print("Google Speech Recognition could not understand audio")
        engine.say("Sorry, I could not understand what you said.")
        engine.runAndWait()
    except sr.RequestError as e:
        print("Could not request results from Google Speech Recognition service; {0}".format(e))
        engine.say("Sorry, I could not process your request.")
        engine.runAndWait()

if __name__ == "__main__":
    main()
