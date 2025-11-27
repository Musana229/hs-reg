# FAU Hochschulsport Bot (v0.10 Beta)

Automation tool to register for FAU Hochschulsport courses. Handles registration for multiple Courses, form filling, wait out server timer, manage anit-bot "trap".

**⚠️ DISCLAIMER:**

Software is inteded to for private use. Use responsibly. Do not distribute. Use at own Risk.
---

### 📋 Prerequisites

1.  **Operating System:** Windows 10 or 11.
2.  **Browser:** You **MUST** have the standard **Google Chrome** installed.
    * *Note:* The bot uses your installed Chrome browser. Please ensure it is up to date.

---

### 🚀 How to Install

1.  **Download:** Download latest Version
2.  **Unzip the folder:** Right-click the `.zip` file and select "Extract All...".
    * *Important:* Do **NOT** run the `.exe` directly from inside the zip file. It will crash. You must extract the folder first.
3.  **Keep the folder structure:** Do not move the `.exe` file out of its folder. It needs the internal files to run.

---

### ⚙️ How to Use

**Step 1: Setup Your Data**
1.  Open `FAU_Bot.exe`.
2.  Go to the **"⚙️ Settings"** tab.
3.  Fill in **ALL** fields (Name, Address, IBAN, Matriculation Number).
4.  Click **"SAVE DATA"**.
    * *Note:* Your data is saved locally on your PC (in your AppData folder). You won't need to re-enter it next time.

**Step 2: Add Courses**
1.  Go to the **"Courses"** tab.
2.  Paste the URL of the Hochschulsport Course (the page with the booking table) into the text field.
3.  Click **"+ Add URL"**. You can add multiple URLs if you want to register for multiple courses.
4.  Click the **"Update / Scan"** button.
    * The bot will briefly check the page to find the course names and times (may take longer depending on amount of URLs).
5.  **Check the boxes** for the specific time slots you want to book.

**Step 3: Run the Bot**
1.  When the booking time is close (e.g., 2 minutes before), click **"START BOTS"**.
2.  A Chrome window will open for each course you selected.
3.  **DO NOT INTERACT WITH THE CHROME WINDOWS.** It is a **HANDS FREE** programm and any interaction may result in the programm not working properly.
    * The bot will refresh the page until the booking button appears.
    * It will fill the form.
    * **It will wait for the 7-second timer** (don't panic if it sits still for a moment).
    * It will detect hidden "Email Traps" and re-submit if necessary.
4.  Once successfully booked, you will see a **"SUCCESS!"** popup.

---

### ❓ Troubleshooting

**The bot crashes immediately:**
* Make sure you extracted the zip file.
* Make sure you have Google Chrome installed.

**The bot is doing nothing on the form page:**
* It is likely waiting for the red "Submit" button to become active. The server forces a 7-second wait time. The bot knows this and will click it the moment it is safe.

**Something went wrong?**
1.  Go to the **"⚙️ Settings"** tab.
2.  Click **"📜 Show Logs"**.
3.  Contact me and send me the Logs

---

**Good luck! 🏐**