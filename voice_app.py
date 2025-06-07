# importing necessary libraries
import streamlit as st
import speech_recognition as sr
from gtts import gTTS
import os
import uuid
import webbrowser
import schedule
import requests
import tempfile
import datetime
from googlesearch import search
from plyer import notification

# Initialize Streamlit
st.title("Voice Assistant with Web Search & Reminders")

# Detect if running in cloud or locally (Optional)
IS_CLOUD = True

# Speak function using gTTS (Streamlit compatible)
def speak(text):
    tts = gTTS(text)
    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as fp:
        tts.save(fp.name)
        st.audio(fp.name, format="audio/mp3")

# Function to recognize speech
def recognize_speech():
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        st.write("Listening...")
        recognizer.adjust_for_ambient_noise(source)
        audio = recognizer.listen(source)
        try:
            text = recognizer.recognize_google(audio)
            return text.lower()
        except sr.UnknownValueError:
            st.write("Could not understand. Try again.")
            return None
        except sr.RequestError:
            st.write("Network error.")
            return None

# Function to search the web
def search_web(query):
    st.write(f"Searching for: {query}")
    if query:
        query = query.strip()
        search_url = f"https://www.google.com/search?q={query.replace(' ', '+')}"
        webbrowser.open(search_url)
        speak(f"Searching Google for {query}.")
        st.success("Opened the search results in your browser.")

# Resend Email Function
def send_email(subject, body, recipient_email):
    headers = {
        "Authorization": f"Bearer {st.secrets['resend']['api_key']}",
        "Content-Type": "application/json"
    }

    data = {
        "from": "Voice Assistant <onboarding@resend.dev>",
        "to": [recipient_email],
        "subject": subject,
        "text": body
    }

    response = requests.post("https://api.resend.com/emails", headers=headers, json=data)

    if response.status_code in [200, 202]:
        st.success("Email sent successfully!")
    else:
        st.error(f"Failed to send email: {response.text}")

# Function to schedule a reminder
def schedule_reminder(event, event_datetime, recipient_email, meeting_location):
    now = datetime.datetime.now()
    reminder_time = event_datetime - datetime.timedelta(minutes=30)

    if reminder_time <= now:
        st.error("Cannot set a reminder for a past time.")
        return

    def notify():
        notification.notify(
            title="Reminder!",
            message=f"{event} at {event_datetime.strftime('%I:%M %p on %B %d, %Y')} at {meeting_location}",
            timeout=10
        )
        speak(f"Reminder! {event} is in 30 minutes. Meeting Location: {meeting_location}")
        email_body = f"""
        Hello,

        Just a reminder that you have "{event}" scheduled for {event_datetime.strftime('%I:%M %p on %B %d, %Y')}.

        Location / Link: {meeting_location}

        This is an automated reminder 30 minutes before your event.

        - Voice Assistant
        """
        send_email("Reminder Notification", email_body, recipient_email)

    schedule.every().day.at(reminder_time.strftime("%H:%M")).do(notify)
    st.success(f"Reminder set: {event} at {event_datetime.strftime('%I:%M %p on %B %d, %Y')}. You will be notified 30 minutes before at {meeting_location}.")
    send_email("Reminder Notification", f"Upcoming event: {event} at {event_datetime}", recipient_email)

# Session state initialization
if "reminder_list" not in st.session_state:
    st.session_state.reminder_list = []

# Streamlit UI
st.subheader("Web Search with Voice Command")
if st.button("Start Voice Search"):
    query = recognize_speech()
    if query:
        search_web(query)

# Reminder UI
st.subheader("Schedule a Meeting / Reminder")
event = st.text_input("Event Name")
event_date = st.date_input("Event Date")  # Returns a datetime.date
event_time_obj = st.time_input("Event Time (e.g., 09:00 AM or 03:45 PM)")  # Now using time picker
recipient_email = st.text_input("Recipient Email")
meeting_location = st.text_input("Meeting Link or Place (e.g., Zoom/Meet URL or Office Room)")

# Set reminder button logic
if st.button("Set Reminder"):
    if event and recipient_email:
        event_datetime = datetime.datetime.combine(event_date, event_time_obj)
        st.session_state.reminder_list.append((event, event_datetime, recipient_email))
        schedule_reminder(event, event_datetime, recipient_email, meeting_location)
    else:
        st.error("Please enter all the details.")
