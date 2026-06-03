import os
import time
import tkinter as tk
from tkinter import simpledialog, messagebox
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager


BILL_DATABASE_MAP = {
    "R26041": "81870595-L6099492",
    "R26042": "81927053-R5279646",
    # You can keep adding your 150+ lines here as a permanent reference masterlist
}

def run_shortcode_downloader():
    root = tk.Tk()
    root.withdraw() 
    
    user_input = simpledialog.askstring(
        "SAJ Intern Rebuilder", 
        "Enter PDF Bill Codes (separated by spaces or commas):\nExample: R26041, R26042"
    )
    
    if not user_input:
        print("No codes typed. Exiting script.")
        return

    requested_codes = [c.strip().upper() for c in user_input.replace(",", " ").split() if c.strip()]
    total_requested = len(requested_codes)
    print(f"User requested {total_requested} files from terminal entry box.")

    download_folder = os.path.abspath("rapid_saj_downloads")
    if not os.path.exists(download_folder):
        os.makedirs(download_folder)

    options = webdriver.ChromeOptions()
    settings = {
        "recentDestinations": [{"id": "Save as PDF", "origin": "local", "account": ""}],
        "selectedDestinationId": "Save as PDF",
        "version": 2
    }
    prefs = {
        "printing.print_preview_repository_path": download_folder,
        "savefile.default_directory": download_folder,
        "download.default_directory": download_folder,
        "download.prompt_for_download": False,
        "profile.default_content_setting_values.automatic_downloads": 1,
        "appState": settings
    }
    options.add_experimental_option("prefs", prefs)
    options.add_argument("--kiosk-printing") 

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    
    try:
        # 3. One-Time Manual Login Screen Context Link 
        login_url = "https://www.ranhillsaj.com.my/customer/account/login/"
        driver.get(login_url)
        print("\n[ACTION]: Please complete system sign-in verification inside Chrome window...")
        time.sleep(15) 

        main_window_handle = driver.current_window_handle
        start_time = time.time()

        for index, code in enumerate(requested_codes):
            if code not in BILL_DATABASE_MAP:
                print(f"[{index+1}/{total_requested}] ❌ Warning: Code '{code}' missing from internal mapping layout dictionary database matrix. Skipping.")
                continue
            
            db_id = BILL_DATABASE_MAP[code]
            print(f"[{index+1}/{total_requested}] Matching '{code}' -> Routing directly to target ID: {db_id}...")

            direct_url = f"https://www.ranhillsaj.com.my/customer/account/?billingId={db_id}"
            driver.get(direct_url)
            time.sleep(2)

            try:
                update_btn = driver.find_elements(By.CSS_SELECTOR, "a.action.secondary.btn-payment-history")
                if len(update_btn) > 0 and update_btn[0].is_displayed():
                    driver.execute_script("arguments[0].click();", update_btn[0])
                    time.sleep(4)
            except:
                pass

            view_bill_xpath = "//input[@type='submit' and (@value='View Bill' or @name='View Bill')]"
            try:
                view_bill_btn = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.XPATH, view_bill_xpath))
                )
                driver.execute_script("arguments[0].click();", view_bill_btn)
                time.sleep(2)
                
                all_windows = driver.window_handles
                if len(all_windows) > 1:
                    driver.switch_to.window(all_windows[1])
                    driver.execute_script("window.print();")
                    time.sleep(1)
                    driver.close()
            except Exception as loop_fault:
                print(f"Failed to extract document target array for code {code}: {loop_fault}")

            driver.switch_to.window(main_window_handle)

        end_time = time.time()
        round_duration = round(end_time - start_time, 2)
        print(f"\n🚀 Execution complete! Processed batch queue records in {round_duration} seconds.")
        messagebox.showinfo("Success", f"Batch sequence completed across parsed codes!")

    except Exception as general_fault:
        print(f"System sequence halted unexpectedly: {general_fault}")
    finally:
        driver.quit()

if __name__ == "__main__":
    run_shortcode_downloader()
