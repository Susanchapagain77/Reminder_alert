import tkinter as tk
from tkinter import messagebox, ttk, simpledialog
import datetime
import webbrowser
import pygame
import json

# Constants
MEETING_DATA_FILE = "meeting_data.json"
ALERT_SOUND = "alert_sound.mp3"
CHECK_INTERVAL = 1000  # 1 second

# Initialize pygame mixer for audio
pygame.mixer.init()

# File to store meeting data
meeting_data_file = "meeting_data.json"


# Function to handle adding hyperlinks and meeting reminders
def add_hyperlink_with_reminder():
    link_name = link_name_entry.get()
    link_url = link_url_entry.get()

    if link_name and link_url:
        hyperlink_listbox.insert(tk.END, f"{link_name}: {link_url}")
        link_name_entry.delete(0, tk.END)
        link_url_entry.delete(0, tk.END)

        meeting_date = simpledialog.askstring("Meeting Date", f"Enter meeting date for '{link_name}' (YYYY-MM-DD):")
        if meeting_date:
            try:
                meeting_date = datetime.datetime.strptime(meeting_date, "%Y-%m-%d")
                meeting_time = simpledialog.askstring("Meeting Time", f"Enter meeting time for '{link_name}' (HH:MM):")
                if meeting_time:
                    try:
                        meeting_datetime = datetime.datetime.strptime(meeting_time, "%H:%M")
                        meeting_datetime = meeting_datetime.replace(year=meeting_date.year, month=meeting_date.month,
                                                                    day=meeting_date.day)
                        now = datetime.datetime.now()
                        time_difference = meeting_datetime - now
                        if time_difference.total_seconds() > 0:
                            meeting_reminder = f"Meeting for '{link_name}' at {meeting_datetime.strftime('%Y-%m-%d %H:%M')}"
                            meeting_reminders.append((meeting_datetime, meeting_reminder, link_url))
                            # Save meeting data to the JSON file
                            save_meeting_data()
                            check_meeting_reminders()

                    except ValueError:
                        messagebox.showwarning("Warning", "Invalid time format. Please use HH:MM.")
                else:
                    messagebox.showwarning("Warning", "Meeting time not provided.")
            except ValueError:
                messagebox.showwarning("Warning", "Invalid date format. Please use YYYY-MM-DD.")
    else:
        messagebox.showwarning("Warning", "Please enter both a name and a hyperlink URL.")


# Function to handle opening selected hyperlink
def open_hyperlink():
    selected_index = hyperlink_listbox.curselection()
    if selected_index:
        selected_link = hyperlink_listbox.get(selected_index)
        webbrowser.open(selected_link.split(': ')[1])
    else:
        messagebox.showwarning("Warning", "Please select a hyperlink.")


# Function to update the opacity based on the slider value
def update_opacity(value):
    opacity = float(value) / 100.0
    app.attributes('-alpha', opacity)


# Function to check for meeting reminders
def check_meeting_reminders():
    now = datetime.datetime.now()
    #print("Checking reminders...")

    reminders_to_keep = []

    for meeting_datetime, meeting_reminder, link_url in meeting_reminders:
        time_difference = meeting_datetime - now
        #print(f"Time difference for {meeting_reminder} is {time_difference.total_seconds()} seconds.")
        if 0 <= time_difference.total_seconds() < 600:
            show_reminder_notification(meeting_reminder, link_url)
        else:
            reminders_to_keep.append((meeting_datetime, meeting_reminder, link_url))

    # Update the meeting_reminders with only those reminders we want to keep
    meeting_reminders.clear()
    meeting_reminders.extend(reminders_to_keep)

    app.after(CHECK_INTERVAL, check_meeting_reminders)

def show_reminder_notification(reminder, link):
    play_alert_sound()
    result = messagebox.askquestion("Meeting Reminder", reminder, icon='warning')
    if result == 'yes':
        webbrowser.open(link)
        
# Function to play an alert sound
def play_alert_sound():
    pygame.mixer.music.load(ALERT_SOUND)
    pygame.mixer.music.play()


# Function to save meeting data to a JSON file
def save_meeting_data():
    with open(MEETING_DATA_FILE, "w") as file:
        serialized_data = [(dt.strftime('%Y-%m-%d %H:%M'), reminder, link) for dt, reminder, link in meeting_reminders]
        json.dump(serialized_data, file)

# Function to load meeting data from a JSON file
def load_meeting_data():
    try:
        with open(MEETING_DATA_FILE, "r") as file:
            loaded_data = json.load(file)
            loaded_reminders = [(datetime.datetime.strptime(dt, '%Y-%m-%d %H:%M'), reminder, link) for dt, reminder, link in loaded_data]
            meeting_reminders.extend(loaded_reminders)
    except FileNotFoundError:
        messagebox.showinfo("Info", "No meeting data found.")
    except json.JSONDecodeError:
        messagebox.showwarning("Warning", "Error reading meeting data. The file may be corrupted.")

# Function to open the settings dialog
def open_settings_dialog():
    settings_dialog = tk.Toplevel(app)
    settings_dialog.title("Settings")

    # Create a button to save meeting data to a JSON file
    save_button = tk.Button(settings_dialog, text="Save Meeting Data", command=save_meeting_data)
    save_button.pack()

    # Create a button to load meeting data from a JSON file
    load_button = tk.Button(settings_dialog, text="Load Meeting Data", command=load_meeting_data)
    load_button.pack()

    # Create a label and slider for opacity control in the dialog
    opacity_label = tk.Label(settings_dialog, text="Opacity:")
    opacity_label.pack()
    opacity_slider = ttk.Scale(settings_dialog, from_=0, to=100, orient="horizontal", command=update_opacity)
    opacity_slider.set(100)  # Initialize opacity to 100%
    opacity_slider.pack()

    # Create a button to mute/unmute in the dialog
    mute_unmute_button = tk.Button(settings_dialog, text="Mute", command=lambda: on_settings_selected("Mute"))
    mute_unmute_button.pack()


# Function to open the day view calendar
def display_day_view_calendar():
    day_view_window = tk.Toplevel(app)
    day_view_window.title("Day View Calendar")

    # Create a label to display the current date
    current_date_label = tk.Label(day_view_window, text=datetime.date.today().strftime("%Y-%m-%d"))
    current_date_label.pack()

    # Create a frame to display events for the day
    day_view_frame = ttk.Frame(day_view_window)
    day_view_frame.pack()

    # Get the schedule for the current day
    schedule = get_day_schedule()

    for event_name, start_time, end_time in schedule:
        event_label = tk.Label(day_view_frame,
                               text=f"{event_name}: {start_time.strftime('%I:%M %p')} - {end_time.strftime('%I:%M %p')}")
        event_label.pack()


# Function to get the schedule for the current day from the stored meeting data
def get_day_schedule():
    today = datetime.date.today()
    schedule = []
    for meeting_datetime, meeting_reminder, link_url in meeting_reminders:
        if meeting_datetime.date() == today:
            event_name = meeting_reminder.split(" for ")[1].split(" at ")[0]
            start_time = meeting_datetime
            end_time = start_time + datetime.timedelta(minutes=60)  # Assuming meetings are 1 hour long
            schedule.append((event_name, start_time, end_time))
    return schedule

# Function to play a notification sound
def play_notification_sound():
    pygame.mixer.music.load("notification_sound.mp3")
    pygame.mixer.music.play()

# Function to show a system notification using plyer
def show_notification():
    play_notification_sound()
    notification.notify(
        title="Meeting Alert",
        message="Your meeting is starting soon",
        timeout=10,
        actions=[
            {"title": "Snooze", "callback": snooze_notification},
            {"title": "Stop", "callback": stop_notification},
        ],
    )

# Function to snooze notifications for 1 day
def snooze_notification():
    # stoping the notification sound
    pygame.mixer.music.stop()

    # Schedule to play the notification sound again after 10 minutes
    app.after(10 * 60 * 1000, show_notification())


#stopping notification
def stop_notification(notification_frame):
    pygame.mixer.music.stop()


# Function to view the list of meetings
def view_meeting_list():
    meeting_list_window = tk.Toplevel(app)
    meeting_list_window.title("Meeting List")

    # Create a frame to display the list of meetings
    meeting_list_frame = ttk.Frame(meeting_list_window)
    meeting_list_frame.pack()

    # Display meeting details in the frame
    for meeting_datetime, meeting_reminder, link_url in meeting_reminders:
        meeting_label = tk.Label(meeting_list_frame,
                                 text=f"{meeting_reminder} - {meeting_datetime.strftime('%Y-%m-%d %H:%M')}")
        meeting_label.pack()





# Create the main application window
app = tk.Tk()
app.title("Zinks")


# Create a frame for the toolbar
toolbar_frame = ttk.Frame(app)
toolbar_frame.pack(side=tk.TOP, fill=tk.X)

# Create a "File" button on the toolbar
file_button = ttk.Button(toolbar_frame, text="File", command=open_settings_dialog)
file_button.pack(side=tk.LEFT)

# Create a label and entries for adding hyperlinks
link_name_label = tk.Label(app, text="Link Name:")
link_name_label.pack()
link_name_entry = tk.Entry(app, width=40)
link_name_entry.pack()

link_url_label = tk.Label(app, text="Hyperlink URL:")
link_url_label.pack()
link_url_entry = tk.Entry(app, width=40)
link_url_entry.pack()

# Create a button to add hyperlinks and meeting reminders
add_button = tk.Button(app, text="Add Hyperlink with Reminder", command=add_hyperlink_with_reminder)
add_button.pack()

# Create a listbox to display added hyperlinks
hyperlink_listbox = tk.Listbox(app, width=40)
hyperlink_listbox.pack()

# Create a button to open selected hyperlink
open_button = tk.Button(app, text="Open Hyperlink", command=open_hyperlink)
open_button.pack()

# Create a list to store meeting reminders (datetime, reminder_message, link_url)
meeting_reminders = []

# Load meeting data on startup
load_meeting_data()

# Check for meeting reminders periodically
app.after(1000, check_meeting_reminders)

# Create a button to open the day view calendar
day_view_button = tk.Button(app, text="Day View Calendar", command=display_day_view_calendar)
day_view_button.pack()

# Create a button to view the list of meetings
view_meeting_list_button = tk.Button(app, text="View Meeting List", command=view_meeting_list)
view_meeting_list_button.pack()

# Start the application main loop
meeting_reminders = []
load_meeting_data()
app.after(CHECK_INTERVAL, check_meeting_reminders)
app.mainloop()
