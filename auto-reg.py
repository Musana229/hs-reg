import customtkinter as ctk
from tkinter import messagebox
import json
import os
import time
import threading
import shutil
import winreg

# --- PILLOW ---
from PIL import Image

# --- UNDETECTED CHROMEDRIVER ---
import undetected_chromedriver as uc

# --- SELENIUM ---
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

# --- CONFIGURATION ---
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

CONFIG_FILE = "user_data.json"
GIF_LOADING = os.path.join("img", "loading.gif")
GIF_SUCCESS = os.path.join("img", "success.gif")

STOP_FLAG = False

# ==========================================
# TRANSLATIONS
# ==========================================
LANG = {
    "de": {
        "title": "FAU HSP BOT v38.0 (Fixes)",
        "tab_run": "🚀 Dashboard",
        "tab_data": "👤 Meine Daten",
        "tab_urls": "🔗 Kurs URLs",
        "lbl_scan_area": "Kurs Auswahl",
        "btn_scan": "🔍 Kurse Scannen",
        "lbl_no_courses": "Keine Kurse gefunden.",
        "lbl_choose": "Verfügbare Kurse:",
        "btn_start": "BOTS STARTEN",
        "btn_stop": "STOPP",
        "status_ready": "Bereit.",
        "status_running": "Bots laufen...",
        "status_stopped": "Abgebrochen.",
        "msg_missing": "Bitte alle Felder im 'Meine Daten' Tab ausfüllen!",
        "msg_select": "Bitte mindestens einen Kurs im Dashboard auswählen!",
        "msg_success_title": "ERFOLG!",
        "msg_success_body": "Kurs {} gebucht!",
        "sec_pers": "Persönliche Daten",
        "sec_bank": "Bankverbindung",
        "sec_stat": "Status & Uni",
        "lbl_fname": "Vorname", "lbl_lname": "Nachname", "lbl_mail": "E-Mail",
        "lbl_street": "Straße & Nr", "lbl_city": "PLZ & Ort", "lbl_sex": "Geschlecht",
        "lbl_iban": "IBAN", "lbl_bic": "BIC", "lbl_holder": "Kontoinhaber",
        "lbl_status": "Status", "lbl_statnr": "Matrikelnummer",
        "sex_values": ["M - Männlich", "W - Weiblich", "D - Divers", "X - Keine Angabe"],
        "status_values": ["S-UNIE : StudentIn der UNI Erlangen", "S-TH : StudentIn der TH-Nürnberg", "S-SPORT : SportstudentIn", "B-UNIE : Beschäftigte/r der UNI Erlangen", "Extern : Fördervereinsmitglied"]
    },
    "en": {
        "title": "FAU HSP BOT v38.0 (Fixes)",
        "tab_run": "🚀 Dashboard",
        "tab_data": "👤 My Profile",
        "tab_urls": "🔗 Course URLs",
        "lbl_scan_area": "Course Selection",
        "btn_scan": "🔍 Scan Courses",
        "lbl_no_courses": "No courses found.",
        "lbl_choose": "Available Courses:",
        "btn_start": "START BOTS",
        "btn_stop": "STOP",
        "status_ready": "Ready.",
        "status_running": "Bots running...",
        "status_stopped": "Stopped.",
        "msg_missing": "Please fill all fields in 'My Profile' tab!",
        "msg_select": "Please select at least one course in Dashboard!",
        "msg_success_title": "SUCCESS!",
        "msg_success_body": "Course {} booked!",
        "sec_pers": "Personal Data",
        "sec_bank": "Bank Details",
        "sec_stat": "Status & Uni",
        "lbl_fname": "First Name", "lbl_lname": "Last Name", "lbl_mail": "E-Mail",
        "lbl_street": "Street & No", "lbl_city": "Zip & City", "lbl_sex": "Gender",
        "lbl_iban": "IBAN", "lbl_bic": "BIC", "lbl_holder": "Account Holder",
        "lbl_status": "Status", "lbl_statnr": "Matriculation No",
        "sex_values": ["M - Male", "W - Female", "D - Diverse", "X - No Answer"],
        "status_values": ["S-UNIE : Student at FAU Erlangen", "S-TH : Student at TH Nuremberg", "S-SPORT : Sports Student", "B-UNIE : Employee at FAU", "Extern : Association Member"]
    }
}

# ==========================================
# SYSTEM HELPERS
# ==========================================
def force_nuke_cache():
    try:
        patcher_path = os.path.join(os.environ.get('APPDATA'), 'undetected_chromedriver')
        if os.path.exists(patcher_path): shutil.rmtree(patcher_path)
    except: pass

def get_chrome_major_version():
    try:
        key_path = r"SOFTWARE\Google\Chrome\BLBeacon"
        try:
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_READ)
            version, _ = winreg.QueryValueEx(key, "version")
            return int(version.split('.')[0])
        except: pass
        try:
            key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, key_path, 0, winreg.KEY_READ | winreg.KEY_WOW64_64KEY)
            version, _ = winreg.QueryValueEx(key, "version")
            return int(version.split('.')[0])
        except: return None
    except: return None

# ==========================================
# BOT LOGIC
# ==========================================
def run_bot_thread(target_url, target_kurs_nr, user_data, success_callback, log_callback):
    global STOP_FLAG
    driver = None
    try:
        log_callback(f"[{target_kurs_nr}] Init...")
        force_nuke_cache()
        
        options = uc.ChromeOptions()
        options.add_argument("--start-maximized")
        options.add_argument("--disable-popup-blocking")
        # options.add_experimental_option("detach", True) # REMOVED to prevent crash on v142
        
        detected_ver = get_chrome_major_version()
        if detected_ver:
            driver = uc.Chrome(options=options, use_subprocess=True, version_main=detected_ver)
        else:
            driver = uc.Chrome(options=options, use_subprocess=True)

        short_wait = WebDriverWait(driver, 0.5)
        wait = WebDriverWait(driver, 15)

        # 1. POLLING
        driver.get(target_url)
        main_window = driver.current_window_handle
        target_xpath = f"//*[contains(text(), '{target_kurs_nr}')]/ancestor::tr//input[@type='submit']"

        log_callback(f"[{target_kurs_nr}] Scanning...")
        while not STOP_FLAG:
            try:
                btns = driver.find_elements(By.XPATH, target_xpath)
                if not btns: driver.refresh(); continue
                btn = btns[0]
                if "ausgebucht" in btn.get_attribute("value").lower(): driver.refresh(); continue
                
                # CLICK AND SWITCH
                driver.execute_script("arguments[0].click();", btn)
                
                # Wait for new tab
                wait.until(EC.number_of_windows_to_be(2))
                
                # Switch to new tab
                for w in driver.window_handles:
                    if w != main_window: 
                        driver.switch_to.window(w)
                        break
                
                # --- FIX: WAKE UP THE TAB ---
                # Immediately interact with the page to force the timer to run
                driver.execute_script("window.focus();")
                try: driver.find_element(By.TAG_NAME, "body").click()
                except: pass
                
                break
            except:
                if STOP_FLAG: return
                try: 
                    if len(driver.window_handles) > 1: driver.close()
                    driver.switch_to.window(main_window)
                except: pass
                driver.refresh()

        if STOP_FLAG: return

        # 2. FORM FILL (DURING TIMER)
        try: wait.until(EC.visibility_of_element_located((By.ID, "BS_F1100")))
        except: return

        driver.execute_script("window.alert = function() {};")
        driver.execute_script("window.confirm = function() { return true; };")

        def safe_send(eid, val):
            try: driver.find_element(By.ID, eid).send_keys(val)
            except: pass

        safe_send("BS_F1100", user_data["vorname"])
        safe_send("BS_F1200", user_data["nachname"])
        safe_send("BS_F1300", user_data["strasse"])
        safe_send("BS_F1400", user_data["ort"])
        safe_send("BS_F2000", user_data["email"])
        safe_send("BS_F_iban", user_data["iban"])
        safe_send("BS_F_bic", user_data["bic"])
        
        try:
            driver.find_element(By.ID, "BS_F_kih").clear()
            driver.find_element(By.ID, "BS_F_kih").send_keys(user_data["inhaber"])
        except: pass

        try: driver.find_element(By.CSS_SELECTOR, f"input[name='sex'][value='{user_data['geschlecht']}']").click()
        except: pass

        try:
            raw_status = user_data["status"].split(" : ")[0]
            Select(driver.find_element(By.ID, "BS_F1600")).select_by_value(raw_status)
            if user_data["status_nr"]:
                try:
                    h = short_wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "div[style='display: block;'] input.bs_form_field")))
                    h.send_keys(user_data["status_nr"])
                except: pass
        except: pass

        try: driver.find_element(By.NAME, "tnbed").click()
        except: pass

        # WAIT FOR TIMER (NATURAL)
        log_callback(f"[{target_kurs_nr}] Waiting Timer...")
        try:
            # Wait until the button is visible/clickable naturally
            submit_btn = WebDriverWait(driver, 20).until(EC.visibility_of_element_located((By.ID, "bs_submit")))
            if submit_btn.is_displayed(): 
                submit_btn.click()
        except: pass

        # 3. TRAP LOOP
        log_callback(f"[{target_kurs_nr}] Fight Loop...")
        start_time = time.time()
        
        while time.time() - start_time < 120 and not STOP_FLAG:
            # Success? (Button disappear or Page 3 element)
            try:
                final_btn = driver.find_elements(By.XPATH, "//input[@value='verbindlich buchen']")
                if final_btn:
                    log_callback(f"[{target_kurs_nr}] SUCCESS (Page 3)!")
                    time.sleep(1) 
                    final_btn[0].click()
                    
                    # Check if final button gone
                    time.sleep(2)
                    if not final_btn[0].is_displayed():
                        if success_callback: success_callback(target_kurs_nr)
                        break
            except: pass

            # Trap?
            try:
                trap_inputs = driver.find_elements(By.XPATH, "//input[contains(@name, 'email_check')] | //div[contains(., 'Wiederhol') or contains(., 'Repeat')]//input")
                for inp in trap_inputs:
                    if inp.is_displayed() and inp.get_attribute("value") == "":
                        name = inp.get_attribute("name")
                        if name and ("pw" in name or "pass" in name): continue
                        inp.clear()
                        inp.send_keys(user_data["email"])
                        try: driver.find_element(By.ID, "bs_submit").click()
                        except: pass
            except: pass

            try: driver.switch_to.alert.accept() 
            except: pass
            time.sleep(0.05) # Super fast loop

        while not STOP_FLAG: time.sleep(1)

    except Exception as e:
        print(f"CRASH: {e}")
    finally:
        if driver and STOP_FLAG: driver.quit()

# ==========================================
# MODERN GUI CLASS
# ==========================================
class ModernApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.running_threads = []
        self.current_lang = "de"
        self.saved = {}
        self.url_entries = [] 
        self.course_map = {}

        self.title(LANG[self.current_lang]["title"])
        self.geometry("600x750")
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, 'r') as f: self.saved = json.load(f)
                if "language" in self.saved: self.current_lang = self.saved["language"]
                if "last_urls" in self.saved and "url_list" not in self.saved:
                    raw = self.saved["last_urls"]
                    self.saved["url_list"] = [u.strip() for u in raw.split('\n') if u.strip()]
            except: pass

        self.tabview = ctk.CTkTabview(self)
        self.tabview.pack(fill="both", expand=True, padx=10, pady=10)
        
        self.tab_run = self.tabview.add(LANG[self.current_lang]["tab_run"])
        self.tab_data = self.tabview.add(LANG[self.current_lang]["tab_data"])
        self.tab_urls = self.tabview.add(LANG[self.current_lang]["tab_urls"])

        self.setup_tab_urls()
        self.setup_tab_data()
        self.setup_tab_run()

    def t(self, key): return LANG[self.current_lang].get(key, key)

    # --- TAB 3: URL MANAGER ---
    def setup_tab_urls(self):
        self.scroll_urls = ctk.CTkScrollableFrame(self.tab_urls, label_text="Kurs URLs")
        self.scroll_urls.pack(fill="both", expand=True, padx=10, pady=10)
        
        saved_urls = self.saved.get("url_list", [])
        if not saved_urls: self.add_url_row("") 
        else:
            for url in saved_urls: self.add_url_row(url)
            
        btn_add = ctk.CTkButton(self.tab_urls, text="+ URL", command=lambda: self.add_url_row(""))
        btn_add.pack(pady=10)

    def add_url_row(self, text):
        row = ctk.CTkFrame(self.scroll_urls)
        row.pack(fill="x", pady=2)
        e = ctk.CTkEntry(row, placeholder_text="https://...")
        e.pack(side="left", fill="x", expand=True, padx=5, pady=5)
        e.insert(0, text)
        btn = ctk.CTkButton(row, text="X", width=30, fg_color="red", hover_color="darkred",
                            command=lambda: self.remove_url_row(row, e))
        btn.pack(side="right", padx=5)
        self.url_entries.append(e)

    def remove_url_row(self, frame, entry):
        if entry in self.url_entries: self.url_entries.remove(entry)
        frame.destroy()

    # --- TAB 2: DATA ---
    def setup_tab_data(self):
        scroll = ctk.CTkScrollableFrame(self.tab_data)
        scroll.pack(fill="both", expand=True)

        def add_sec(txt): ctk.CTkLabel(scroll, text=txt, font=("Arial", 16, "bold"), anchor="w").pack(fill="x", pady=(20, 5))

        def add_field(key, label):
            f = ctk.CTkFrame(scroll, fg_color="transparent"); f.pack(fill="x", pady=2)
            ctk.CTkLabel(f, text=label, width=100, anchor="w").pack(side="left")
            e = ctk.CTkEntry(f)
            e.pack(side="right", expand=True, fill="x")
            if key in self.saved: e.insert(0, self.saved[key])
            setattr(self, f"e_{key}", e)

        add_sec(self.t("sec_pers"))
        add_field("vorname", self.t("lbl_fname"))
        add_field("nachname", self.t("lbl_lname"))
        add_field("email", self.t("lbl_mail"))
        add_field("strasse", self.t("lbl_street"))
        add_field("ort", self.t("lbl_city"))
        
        f = ctk.CTkFrame(scroll, fg_color="transparent"); f.pack(fill="x", pady=2)
        ctk.CTkLabel(f, text=self.t("lbl_sex"), width=100, anchor="w").pack(side="left")
        self.c_sex = ctk.CTkComboBox(f, values=self.t("sex_values"))
        self.c_sex.pack(side="right", expand=True, fill="x")
        self.set_combo(self.c_sex, "geschlecht")

        add_sec(self.t("sec_bank"))
        add_field("iban", self.t("lbl_iban"))
        add_field("bic", self.t("lbl_bic"))
        f = ctk.CTkFrame(scroll, fg_color="transparent"); f.pack(fill="x", pady=2)
        ctk.CTkLabel(f, text=self.t("lbl_holder"), width=100, anchor="w").pack(side="left")
        self.e_inhaber = ctk.CTkEntry(f)
        self.e_inhaber.pack(side="right", expand=True, fill="x")
        if "inhaber" in self.saved: self.e_inhaber.insert(0, self.saved["inhaber"])

        add_sec(self.t("sec_stat"))
        f = ctk.CTkFrame(scroll, fg_color="transparent"); f.pack(fill="x", pady=2)
        ctk.CTkLabel(f, text=self.t("lbl_status"), width=100, anchor="w").pack(side="left")
        self.c_status = ctk.CTkComboBox(f, values=self.t("status_values"))
        self.c_status.pack(side="right", expand=True, fill="x")
        self.set_combo(self.c_status, "status")
        
        f = ctk.CTkFrame(scroll, fg_color="transparent"); f.pack(fill="x", pady=2)
        ctk.CTkLabel(f, text=self.t("lbl_statnr"), width=100, anchor="w").pack(side="left")
        self.e_statnr = ctk.CTkEntry(f)
        self.e_statnr.pack(side="right", expand=True, fill="x")
        if "status_nr" in self.saved: self.e_statnr.insert(0, self.saved["status_nr"])

        ctk.CTkButton(scroll, text="SAVE DATA", command=self.save_data, fg_color="green").pack(pady=20)

    def set_combo(self, combo, key):
        if key in self.saved:
            prefix = self.saved[key].split(" ")[0]
            vals = combo.cget("values") 
            for v in vals:
                if v.startswith(prefix): combo.set(v); return

    # --- TAB 1: RUN ---
    def setup_tab_run(self):
        f_scan = ctk.CTkFrame(self.tab_run)
        f_scan.pack(fill="x", padx=10, pady=10)
        
        ctk.CTkLabel(f_scan, text="1. Update:").pack(side="left", padx=10)
        ctk.CTkButton(f_scan, text=self.t("btn_scan"), command=self.scan_courses).pack(side="right", padx=10)

        self.scroll_courses = ctk.CTkScrollableFrame(self.tab_run, label_text="Available Courses")
        self.scroll_courses.pack(fill="both", expand=True, padx=10, pady=5)
        self.course_checkboxes = []

        self.lbl_status = ctk.CTkLabel(self.tab_run, text=self.t("status_ready"), font=("Arial", 14))
        self.lbl_status.pack(pady=5)

        f_btn = ctk.CTkFrame(self.tab_run, fg_color="transparent")
        f_btn.pack(fill="x", padx=10, pady=20)
        
        self.btn_start = ctk.CTkButton(f_btn, text=self.t("btn_start"), command=self.start_bots, 
                                     font=("Arial", 16, "bold"), height=50, fg_color="green", hover_color="darkgreen")
        self.btn_start.pack(side="left", fill="x", expand=True, padx=5)
        
        self.btn_stop = ctk.CTkButton(f_btn, text=self.t("btn_stop"), command=self.stop_bots,
                                    font=("Arial", 16, "bold"), height=50, fg_color="darkred", hover_color="red", state="disabled")
        self.btn_stop.pack(side="right", fill="x", expand=True, padx=5)

    # --- LOGIC ---
    def save_data(self):
        url_list = [e.get() for e in self.url_entries if e.get().strip()]
        data = {
            "vorname": self.e_vorname.get(), "nachname": self.e_nachname.get(),
            "email": self.e_email.get(), "strasse": self.e_strasse.get(),
            "ort": self.e_ort.get(), "iban": self.e_iban.get(),
            "bic": self.e_bic.get(), "inhaber": self.e_inhaber.get(),
            "geschlecht": self.c_sex.get(), "status": self.c_status.get(),
            "status_nr": self.e_statnr.get(), "url_list": url_list,
            "language": self.current_lang
        }
        with open(CONFIG_FILE, 'w') as f: json.dump(data, f)
        self.saved = data
        print("Data saved.")

    def scan_courses(self):
        self.save_data()
        urls = self.saved.get("url_list", [])
        if not urls: return messagebox.showerror("Error", "No URLs in 'URLs' tab!")
        
        for w in self.scroll_courses.winfo_children(): w.destroy()
        self.course_checkboxes = []
        self.lbl_status.configure(text="Scanning...")
        
        threading.Thread(target=self._scan_thread, args=(urls,), daemon=True).start()

    def _scan_thread(self, urls):
        try:
            import selenium.webdriver as std_webdriver
            from webdriver_manager.chrome import ChromeDriverManager
            from selenium.webdriver.chrome.service import Service as StdService
            service = StdService(ChromeDriverManager().install())
            service.creation_flags = 0x08000000
            opts = std_webdriver.ChromeOptions(); opts.add_argument("--headless")
            driver = std_webdriver.Chrome(service=service, options=opts)
            
            found = []
            for url in urls:
                try:
                    driver.get(url)
                    rows = driver.find_elements(By.CSS_SELECTOR, "table.bs_kurse tbody tr")
                    for row in rows:
                        try:
                            nr = row.find_element(By.CLASS_NAME, "bs_sknr").text
                            tag = row.find_element(By.CLASS_NAME, "bs_stag").text
                            zeit = row.find_element(By.CLASS_NAME, "bs_szeit").text
                            det = row.find_element(By.CLASS_NAME, "bs_sdet").text
                            found.append((nr, f"{nr} | {tag} {zeit} | {det}", url))
                        except: continue
                except: pass
            driver.quit()
            self.after(0, lambda: self._update_list(found))
        except Exception as e: print(e)

    def _update_list(self, courses):
        self.lbl_status.configure(text=self.t("status_ready"))
        if not courses: 
            ctk.CTkLabel(self.scroll_courses, text="No courses found.").pack()
            return

        for nr, text, url in courses:
            self.course_map[nr] = url
            var = ctk.StringVar(value="off")
            cb = ctk.CTkCheckBox(self.scroll_courses, text=text, variable=var, onvalue="on", offvalue="off")
            cb.pack(fill="x", pady=2, anchor="w")
            self.course_checkboxes.append((nr, var))

    def start_bots(self):
        self.save_data()
        global STOP_FLAG
        
        selected = [nr for nr, var in self.course_checkboxes if var.get() == "on"]
        if not selected: return messagebox.showerror("Error", "Select a course!")

        bot_data = self.saved.copy()
        bot_data["geschlecht"] = bot_data["geschlecht"].split(" ")[0]
        bot_data["status"] = bot_data["status"].split(" : ")[0]
        bot_data["wait_timer"] = True

        STOP_FLAG = False
        self.running_threads = []
        
        for i, nr in enumerate(selected):
            url = self.course_map.get(nr)
            if url:
                if i > 0: time.sleep(2)
                t = threading.Thread(target=run_bot_thread, args=(url, nr, bot_data, self.on_success, self.update_log))
                self.running_threads.append(t)
                t.start()

        self.btn_start.configure(state="disabled")
        self.btn_stop.configure(state="normal")
        self.lbl_status.configure(text=self.t("status_running"), text_color="green")

    def stop_bots(self):
        global STOP_FLAG
        STOP_FLAG = True
        self.btn_start.configure(state="normal")
        self.btn_stop.configure(state="disabled")
        self.lbl_status.configure(text=self.t("status_stopped"), text_color="red")

    def update_log(self, msg):
        print(msg)

    def on_success(self, nr):
        self.after(0, lambda: messagebox.showinfo("SUCCESS", f"Course {nr} Booked!"))

if __name__ == "__main__":
    app = ModernApp()
    app.mainloop()