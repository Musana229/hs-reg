import tkinter as tk
from tkinter import messagebox, ttk
import json
import os
import time
import threading

# --- NEW: PILLOW FOR SMOOTH GIFS ---
from PIL import Image, ImageTk, ImageSequence

# --- UNDETECTED CHROMEDRIVER ---
import undetected_chromedriver as uc

# --- STANDARD SELENIUM HELPERS ---
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

CONFIG_FILE = "user_data.json"
GIF_FILE = os.path.join("img", "loading.gif")

# ==========================================
# TRANSLATIONS
# ==========================================
LANG = {
    "de": {
        "title": "FAU HSP BOT v0.6.5",
        "grp_scan": "1. Kurs Auswahl",
        "lbl_url": "URL:",
        "btn_load": "🔍 Kurse laden",
        "lbl_no_courses": "Keine Kurse gefunden!",
        "lbl_choose": "Wähle deine Kurse:",
        "grp_pers": "2. Persönliche Daten",
        "lbl_fname": "Vorname:",
        "lbl_lname": "Nachname:",
        "lbl_mail": "E-Mail:",
        "lbl_street": "Straße:",
        "lbl_city": "PLZ & Ort:",
        "lbl_sex": "Geschlecht:",
        "grp_bank": "3. Bank & Status",
        "lbl_iban": "IBAN:",
        "lbl_bic": "BIC:",
        "lbl_holder": "Inhaber:",
        "lbl_status": "Status:",
        "lbl_statnr": "Matr.Nr:",
        "btn_start": "🚀 BOTS STARTEN",
        "btn_stop": "🛑 ALLE STOPPEN",
        "msg_missing": "Bitte füllen Sie folgende Felder aus:",
        "msg_select": "Bitte mindestens einen Kurs auswählen!",
        "msg_started": "Bots warten auf Timer...",
        "msg_stopped": "Bots gestoppt.",
        "err_url": "Keine URL eingegeben!",
        "scan_load": "Lade...",
        "sex_values": ["M - Männlich", "W - Weiblich", "D - Divers", "X - Keine Angabe"],
        "status_values": [
            "S-UNIE : StudentIn der UNI Erlangen",
            "S-TH : StudentIn der TH-Nürnberg",
            "S-SPORT : SportstudentIn",
            "S-aH : StudentIn einer anderen Hochschule",
            "B-UNIE : Beschäftigte/r der UNI Erlangen",
            "Extern : Fördervereinsmitglied"
        ]
    },
    "en": {
        "title": "FAU HSP BOT v0.6.5",
        "grp_scan": "1. Course Selection",
        "lbl_url": "URL:",
        "btn_load": "🔍 Load Courses",
        "lbl_no_courses": "No courses found!",
        "lbl_choose": "Choose your courses:",
        "grp_pers": "2. Personal Data",
        "lbl_fname": "First Name:",
        "lbl_lname": "Last Name:",
        "lbl_mail": "E-Mail:",
        "lbl_street": "Street:",
        "lbl_city": "ZIP Code City:",
        "lbl_sex": "Gender:",
        "grp_bank": "3. Bank & Status",
        "lbl_iban": "IBAN:",
        "lbl_bic": "BIC:",
        "lbl_holder": "Acc. Holder:",
        "lbl_status": "Status:",
        "lbl_statnr": "Matriculation No:",
        "btn_start": "🚀 START BOTS",
        "btn_stop": "🛑 STOP ALL",
        "msg_missing": "Please fill in the following fields:",
        "msg_select": "Please select at least one course!",
        "msg_started": "Bots waiting for timer...",
        "msg_stopped": "Bots stopped.",
        "err_url": "No URL provided!",
        "scan_load": "Loading...",
        "sex_values": ["M - Male", "W - Female", "D - Diverse", "X - No Answer"],
        "status_values": [
            "S-UNIE : Student at FAU Erlangen",
            "S-TH : Student at TH Nuremberg",
            "S-SPORT : Sports Student",
            "S-aH : Student at other University",
            "B-UNIE : Employee at FAU",
            "Extern : Association Member/External"
        ]
    }
}

PLACEHOLDERS = {
    "vorname": "Max", "nachname": "Mustermann", "email": "max.mustermann@fau.de",
    "strasse": "Schlossplatz 4", "ort": "91054 Erlangen", "iban": "DE00 1234 5678 9000",
    "bic": "MARKDEF1XXX", "inhaber": "Max Mustermann", "status_nr": "12345678",
    "last_url": "https://..."
}

STOP_FLAG = False

# ==========================================
# BOT LOGIC
# ==========================================
def run_bot_thread(target_url, target_kurs_nr, user_data):
    global STOP_FLAG
    driver = None
    try:
        print(f"[{target_kurs_nr}] Initializing...")
        options = uc.ChromeOptions()
        options.add_argument("--start-maximized")
        options.add_argument("--disable-password-manager-reauth")
        options.add_argument("--disable-save-password-bubble")
        options.add_argument("--disable-popup-blocking")
        
        driver = uc.Chrome(options=options, use_subprocess=True, version_main=140)
        short_wait = WebDriverWait(driver, 0.5)
        wait = WebDriverWait(driver, 15)

        # --- PHASE 1: POLLING ---
        driver.get(target_url)
        main_window = driver.current_window_handle
        target_xpath = f"//*[contains(text(), '{target_kurs_nr}')]/ancestor::tr//input[@type='submit']"

        print(f"[{target_kurs_nr}] Scanning...")
        while not STOP_FLAG:
            try:
                btns = driver.find_elements(By.XPATH, target_xpath)
                if not btns: driver.refresh(); continue
                btn = btns[0]
                if "ausgebucht" in btn.get_attribute("value").lower() or "fully booked" in btn.get_attribute("value").lower():
                     driver.refresh(); continue
                
                driver.execute_script("arguments[0].click();", btn)
                wait.until(EC.number_of_windows_to_be(2))
                for w in driver.window_handles:
                    if w != main_window: driver.switch_to.window(w); break
                break
            except:
                if STOP_FLAG: return
                try: 
                    if len(driver.window_handles) > 1: driver.close()
                    driver.switch_to.window(main_window)
                except: pass
                driver.refresh()

        if STOP_FLAG: return

        # --- PHASE 2: FILLING (DURING TIMER) ---
        try: wait.until(EC.visibility_of_element_located((By.ID, "BS_F1100")))
        except: return

        # Silence Alerts
        driver.execute_script("window.alert = function() {};")
        driver.execute_script("window.confirm = function() { return true; };")

        print(f"[{target_kurs_nr}] Filling fields (Timer running)...")

        # Fill Data
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

        # --- SNIPER WAIT ---
        # We DO NOT kill the timer. We wait for the server to enable the button.
        print(f"[{target_kurs_nr}] Waiting for button activation...")
        
        # Wait until the "hidden" class is removed OR the button becomes clickable
        # The site usually swaps classes: class="hidden" -> class="sub"
        try:
            submit_btn = wait.until(EC.element_to_be_clickable((By.ID, "bs_submit")))
            
            # Double check visibility just to be safe
            if submit_btn.is_displayed():
                print(f"[{target_kurs_nr}] Button active! SNIPING NOW!")
                submit_btn.click()
            else:
                # Fallback if Selenium thinks it's hidden but it's ready
                driver.execute_script("arguments[0].click();", submit_btn)
                
        except Exception as e:
            print(f"[{target_kurs_nr}] Wait Error: {e}")

        # --- PHASE 3: THE RECOVERY LOOP ---
        print(f"[{target_kurs_nr}] Entering Trap Loop...")
        start_time = time.time()
        
        while time.time() - start_time < 60 and not STOP_FLAG:
            
            # 1. CHECK SUCCESS (Page 3)
            try:
                final_btn = driver.find_elements(By.XPATH, "//input[@value='verbindlich buchen']")
                if final_btn:
                    print(f"[{target_kurs_nr}] SUCCESS! Reached Page 3.")
                    time.sleep(1) 
                    final_btn[0].click()
                    print(f"[{target_kurs_nr}] 🏁 FINAL BOOKING CLICKED!")
                    break 
            except: pass

            # 2. CHECK FOR TRAP (Aggressive)
            try:
                all_inputs = driver.find_elements(By.TAG_NAME, "input")
                trap_found = False
                for inp in all_inputs:
                    if not inp.is_displayed(): continue
                    
                    name_attr = inp.get_attribute("name")
                    eid = inp.get_attribute("id")
                    val = inp.get_attribute("value")
                    
                    # Skip known standard fields
                    if eid in ["BS_F1100", "BS_F1200", "BS_F1300", "BS_F1400", "BS_F2000", "BS_F_iban", "BS_F_bic", "BS_F_kih", "BS_F1700"]:
                        continue
                    
                    # Skip Password Fields
                    if name_attr and ("pw" in name_attr or "pass" in name_attr or "newpw" in name_attr):
                        continue
                    
                    # Identify as Trap
                    if inp.get_attribute("type") in ["text", "email"] and val == "":
                        print(f"[{target_kurs_nr}] TRAP FOUND! Filling...")
                        inp.clear()
                        inp.send_keys(user_data["email"])
                        trap_found = True

                if trap_found:
                     # If we filled a trap, we must submit immediately
                     try:
                        driver.find_element(By.ID, "bs_submit").click()
                        print(f"[{target_kurs_nr}] Re-Submitted after trap fill.")
                     except: pass

            except: pass
            
            # 3. HANDLE ALERTS (Backup)
            try: driver.switch_to.alert.accept()
            except: pass
            
            time.sleep(0.5)

        while not STOP_FLAG: time.sleep(1)

    except Exception as e:
        print(f"[{target_kurs_nr}] CRASH: {e}")
    finally:
        if driver and STOP_FLAG: driver.quit()

# ==========================================
# GUI CLASS
# ==========================================
class SportBotGUI:
    def __init__(self, root):
        self.root = root
        self.running_threads = [] 
        self.current_lang = "de"
        self.saved = {}
        self.gif_frames = [] 
        self.gif_idx = 0     
        self.animating = False 

        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, 'r') as f: self.saved = json.load(f)
                if "language" in self.saved: self.current_lang = self.saved["language"]
            except: pass
        
        self.load_gif()
        self.build_gui()

    def load_gif(self):
        if not os.path.exists(GIF_FILE): return
        try:
            im = Image.open(GIF_FILE)
            self.gif_frames = []
            for frame in ImageSequence.Iterator(im):
                self.gif_frames.append(ImageTk.PhotoImage(frame))
            print(f"Loaded {len(self.gif_frames)} frames.")
        except Exception as e: print(f"GIF Error: {e}")

    def t(self, key): return LANG[self.current_lang].get(key, key)

    def change_language(self, event):
        new_lang = "de" if self.combo_lang.get() == "Deutsch" else "en"
        if new_lang != self.current_lang:
            self.current_lang = new_lang
            for widget in self.root.winfo_children(): widget.destroy()
            self.build_gui()

    def build_gui(self):
        self.root.title(self.t("title"))
        self.root.geometry("550x900")

        f_top = tk.Frame(self.root); f_top.pack(fill="x", padx=10, pady=5)
        tk.Label(f_top, text="Language:").pack(side="left")
        self.combo_lang = ttk.Combobox(f_top, values=["Deutsch", "English"], width=10, state="readonly")
        self.combo_lang.pack(side="left", padx=5)
        self.combo_lang.set("Deutsch" if self.current_lang == "de" else "English")
        self.combo_lang.bind("<<ComboboxSelected>>", self.change_language)

        lf_scan = tk.LabelFrame(self.root, text=self.t("grp_scan"), font=("Arial", 10, "bold"), fg="blue")
        lf_scan.pack(fill="x", padx=10, pady=5)
        f_u = tk.Frame(lf_scan); f_u.pack(fill="x", padx=5, pady=5)
        tk.Label(f_u, text=self.t("lbl_url")).pack(side="left")
        self.e_url = self.create_placeholder_entry(f_u, "last_url")
        self.e_url.pack(side="left", expand=True, fill="x", padx=5)
        tk.Button(f_u, text=self.t("btn_load"), bg="#dddddd", command=self.scan_courses).pack(side="right")

        f_list = tk.Frame(lf_scan); f_list.pack(fill="both", expand=True, padx=5, pady=5)
        self.canvas = tk.Canvas(f_list, height=150)
        scrollbar = ttk.Scrollbar(f_list, orient="vertical", command=self.canvas.yview)
        self.scrollable_frame = tk.Frame(self.canvas)
        self.scrollable_frame.bind("<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=scrollbar.set)
        self.canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        self.course_checkboxes = []

        lf_pers = tk.LabelFrame(self.root, text=self.t("grp_pers"), font=("Arial", 10, "bold"))
        lf_pers.pack(fill="x", padx=10, pady=5)
        self.e_vorname = self.entry(lf_pers, self.t("lbl_fname"), "vorname")
        self.e_nachname = self.entry(lf_pers, self.t("lbl_lname"), "nachname")
        self.e_email = self.entry(lf_pers, self.t("lbl_mail"), "email")
        self.e_strasse = self.entry(lf_pers, self.t("lbl_street"), "strasse")
        self.e_ort = self.entry(lf_pers, self.t("lbl_city"), "ort")
        
        f_sex = tk.Frame(lf_pers); f_sex.pack(fill="x", padx=10, pady=2)
        tk.Label(f_sex, text=self.t("lbl_sex"), width=15, anchor="w").pack(side="left")
        self.c_sex = ttk.Combobox(f_sex, values=self.t("sex_values"))
        self.c_sex.pack(side="right", expand=True, fill="x")
        self.set_combo(self.c_sex, "geschlecht", 0)

        lf_bank = tk.LabelFrame(self.root, text=self.t("grp_bank"), font=("Arial", 10, "bold"))
        lf_bank.pack(fill="x", padx=10, pady=5)
        self.e_iban = self.entry(lf_bank, self.t("lbl_iban"), "iban")
        self.e_bic = self.entry(lf_bank, self.t("lbl_bic"), "bic")
        self.e_inh = self.entry(lf_bank, self.t("lbl_holder"), "inhaber")
        f_st = tk.Frame(lf_bank); f_st.pack(fill="x", padx=10, pady=2)
        tk.Label(f_st, text=self.t("lbl_status"), width=15, anchor="w").pack(side="left")
        self.c_status = ttk.Combobox(f_st, values=self.t("status_values"))
        self.c_status.pack(side="right", expand=True, fill="x")
        self.set_combo(self.c_status, "status", 0)
        self.e_statnr = self.entry(lf_bank, self.t("lbl_statnr"), "status_nr")

        f_ctrl = tk.Frame(self.root); f_ctrl.pack(fill="x", padx=20, pady=10)
        # No Checkbox needed anymore

        self.btn_start = tk.Button(f_ctrl, text=self.t("btn_start"), bg="green", fg="white", font=("Arial", 12, "bold"), command=self.start_bots)
        self.btn_start.pack(side="left", fill="x", expand=True, padx=(0, 5))
        self.btn_stop = tk.Button(f_ctrl, text=self.t("btn_stop"), bg="red", fg="white", font=("Arial", 12, "bold"), command=self.stop_bots, state="disabled")
        self.btn_stop.pack(side="right", fill="x", expand=True, padx=(5, 0))

        self.f_anim = tk.Frame(self.root)
        self.lbl_gif = tk.Label(self.f_anim) 
        self.lbl_gif.pack()
        self.lbl_msg = tk.Label(self.f_anim, text=self.t("msg_started"), font=("Arial", 12, "bold"), fg="green")
        self.lbl_msg.pack()

    def start_animation(self):
        self.f_anim.pack(fill="x", pady=10) 
        self.animating = True
        self.animate_loop()

    def stop_animation(self):
        self.animating = False
        self.f_anim.pack_forget() 

    def animate_loop(self):
        if not self.animating or not self.gif_frames: return
        self.gif_idx = (self.gif_idx + 1) % len(self.gif_frames)
        self.lbl_gif.config(image=self.gif_frames[self.gif_idx])
        self.root.after(50, self.animate_loop)

    def create_placeholder_entry(self, parent, key):
        e = tk.Entry(parent, fg='grey')
        placeholder = PLACEHOLDERS.get(key, "")
        saved_val = self.saved.get(key, "")
        if saved_val: e.insert(0, saved_val); e['fg'] = 'black'
        else: e.insert(0, placeholder)
        def on_focus_in(event):
            if e['fg'] == 'grey': e.delete('0', 'end'); e['fg'] = 'black'
        def on_focus_out(event):
            if not e.get(): e.insert(0, placeholder); e['fg'] = 'grey'
        e.bind("<FocusIn>", on_focus_in); e.bind("<FocusOut>", on_focus_out)
        return e

    def entry(self, parent, lbl, key):
        f = tk.Frame(parent); f.pack(fill="x", padx=10, pady=2)
        tk.Label(f, text=lbl, width=15, anchor="w").pack(side="left")
        e = self.create_placeholder_entry(f, key)
        e.pack(side="right", expand=True, fill="x")
        return e

    def get_clean_value(self, entry_widget):
        if entry_widget['fg'] == 'grey': return ""
        return entry_widget.get()

    def set_combo(self, combo, key, default_idx):
        if key in self.saved:
            saved_prefix = self.saved[key].split(" ")[0]
            for v in combo['values']:
                if v.startswith(saved_prefix): combo.set(v); return
        combo.current(default_idx)

    def scan_courses(self):
        url = self.get_clean_value(self.e_url)
        if not url: return messagebox.showerror("Error", self.t("err_url"))
        for widget in self.scrollable_frame.winfo_children(): widget.destroy()
        self.course_checkboxes = []
        tk.Label(self.scrollable_frame, text=self.t("scan_load")).pack()
        threading.Thread(target=self._scan_thread, args=(url,), daemon=True).start()

    def _scan_thread(self, url):
        try:
            import selenium.webdriver as std_webdriver
            from webdriver_manager.chrome import ChromeDriverManager
            from selenium.webdriver.chrome.service import Service as StdService
            service = StdService(ChromeDriverManager().install())
            service.creation_flags = 0x08000000
            opts = std_webdriver.ChromeOptions(); opts.add_argument("--headless")
            driver = std_webdriver.Chrome(service=service, options=opts)
            driver.get(url)
            rows = driver.find_elements(By.CSS_SELECTOR, "table.bs_kurse tbody tr")
            found = []
            for row in rows:
                try:
                    nr = row.find_element(By.CLASS_NAME, "bs_sknr").text
                    tag = row.find_element(By.CLASS_NAME, "bs_stag").text
                    zeit = row.find_element(By.CLASS_NAME, "bs_szeit").text
                    det = row.find_element(By.CLASS_NAME, "bs_sdet").text
                    found.append((nr, f"{nr} | {tag} {zeit} | {det}"))
                except: continue
            driver.quit()
            self.root.after(0, lambda: self._update_list(found))
        except Exception as e: self.root.after(0, lambda: messagebox.showerror("Scan Error", str(e)))

    def _update_list(self, courses):
        for widget in self.scrollable_frame.winfo_children(): widget.destroy()
        if not courses: tk.Label(self.scrollable_frame, text=self.t("lbl_no_courses")).pack(); return
        tk.Label(self.scrollable_frame, text=self.t("lbl_choose"), font=("Arial", 10, "bold")).pack(anchor="w")
        for nr, text in courses:
            var = tk.BooleanVar(); cb = tk.Checkbutton(self.scrollable_frame, text=text, variable=var, anchor="w")
            cb.pack(fill="x", anchor="w"); self.course_checkboxes.append((nr, var))

    def start_bots(self):
        global STOP_FLAG
        missing = []
        val_vorname = self.get_clean_value(self.e_vorname)
        val_nachname = self.get_clean_value(self.e_nachname)
        val_email = self.get_clean_value(self.e_email)
        val_iban = self.get_clean_value(self.e_iban)

        if not val_vorname: missing.append(self.t("lbl_fname"))
        if not val_nachname: missing.append(self.t("lbl_lname"))
        if not val_email: missing.append(self.t("lbl_mail"))
        if not val_iban: missing.append(self.t("lbl_iban"))

        if missing: return messagebox.showwarning("Info", f"{self.t('msg_missing')}\n{', '.join(missing)}")

        selected_nrs = [nr for nr, var in self.course_checkboxes if var.get()]
        if not selected_nrs: return messagebox.showerror("Info", self.t("msg_select"))

        data = {
            "vorname": val_vorname, "nachname": val_nachname, "email": val_email,
            "strasse": self.get_clean_value(self.e_strasse), "ort": self.get_clean_value(self.e_ort),
            "iban": val_iban, "bic": self.get_clean_value(self.e_bic), "inhaber": self.get_clean_value(self.e_inh),
            "geschlecht": self.c_sex.get(), "status": self.c_status.get(),
            "status_nr": self.get_clean_value(self.e_statnr), "last_url": self.get_clean_value(self.e_url),
            "language": self.current_lang,
            # Hardcoded True because user wants to wait for timer always
            "wait_timer": True 
        }
        bot_data = data.copy()
        bot_data["geschlecht"] = data["geschlecht"].split(" ")[0]
        bot_data["status"] = data["status"].split(" : ")[0]

        with open(CONFIG_FILE, 'w') as f: json.dump(data, f)

        STOP_FLAG = False
        self.running_threads = []
        for nr in selected_nrs:
            t = threading.Thread(target=run_bot_thread, args=(data["last_url"], nr, bot_data))
            self.running_threads.append(t)
            t.start()
        
        self.btn_start.config(state="disabled", bg="gray")
        self.btn_stop.config(state="normal", bg="red")
        self.start_animation()

    def stop_bots(self):
        global STOP_FLAG
        STOP_FLAG = True
        self.btn_start.config(state="normal", bg="green")
        self.btn_stop.config(state="disabled", bg="red")
        self.stop_animation()
        messagebox.showinfo("Info", self.t('msg_stopped'))

if __name__ == '__main__':
    root = tk.Tk()
    app = SportBotGUI(root)
    root.mainloop()