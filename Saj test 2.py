import os
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

def download_all_saj_bills(username, password):
    download_folder = os.path.abspath("all_saj_bills")
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
        login_url = "https://www.ranhillsaj.com.my/customer/account/login/"
        dashboard_url = "https://www.ranhillsaj.com.my/customer/account/" 
        
        print("Opening login page...")
        driver.get(login_url)
        
        print("Typing login credentials automatically...")
        username_field = WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.ID, "email"))
        )
        username_field.send_keys(username)
        
        password_field = driver.find_element(By.ID, "pass")
        password_field.send_keys(password)
        
        login_button = driver.find_element(By.ID, "send2")
        login_button.click()
        
        print("Waiting for dashboard authentication to clear...")
        time.sleep(10) 

        driver.get(dashboard_url)
        time.sleep(3)

        arrow_selector = "#maincontent > div.columns.columns-flex > div.column.main > div.account-dashboard-info > div.group-bill-account > div > div.control-list-account > span"

        arrow_btn = WebDriverWait(driver, 15).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, arrow_selector))
        )
        arrow_btn.click()
        time.sleep(1.5)

        account_radios = driver.find_elements(By.NAME, "bill_account_id")
        total_accounts = len(account_radios)
        print(f"Successfully connected! Found {total_accounts} total bills to process.")

        main_window_handle = driver.current_window_handle

        # 3. Main Automation Loop
        for i in range(total_accounts):
            print(f"\nProcessing bill [{i+1}/{total_accounts}]...")
            
            # Reset window focus at start of iteration
            try:
                driver.switch_to.window(main_window_handle)
            except Exception:
                if len(driver.window_handles) > 0:
                    driver.switch_to.window(driver.window_handles[0])
                    main_window_handle = driver.current_window_handle

            # Ensure dropdown menu is expanded and visible
            account_radios = driver.find_elements(By.NAME, "bill_account_id")
            if len(account_radios) == 0 or not account_radios[0].is_displayed():
                try:
                    arrow_btn = WebDriverWait(driver, 5).until(
                        EC.element_to_be_clickable((By.CSS_SELECTOR, arrow_selector))
                    )
                    arrow_btn.click()
                    time.sleep(0.5)
                    account_radios = driver.find_elements(By.NAME, "bill_account_id")
                except Exception:
                    pass 

            current_radio = account_radios[i]
            account_value = current_radio.get_attribute("value")
            print(f"Selecting account value: {account_value}")
            
            # --- ARMORED RADIO SELECTION FIX ---
            try:
                # Force choice injection into the DOM layer bypassing layout elements blocking click
                driver.execute_script("arguments[0].click();", current_radio)
            except Exception as radio_err:
                print(f"JS Selection override applied due to layout friction: {radio_err}")
                current_radio.click() # Native fallback if script click behaves unexpectedly
            time.sleep(0.5)

            view_account_btn = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "a.action.secondary.manage"))
            )
            view_account_btn.click()
            
            print("Waiting for page container data to refresh...")
            time.sleep(3) 

            # Check for history update requirements
            did_update = False
            try:
                update_history_btn = driver.find_elements(By.CSS_SELECTOR, "a.action.secondary.btn-payment-history")
                if len(update_history_btn) > 0 and update_history_btn[0].is_displayed():
                    print("⚠️ 'Update Payment History' button detected! Refreshing account data...")
                    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", update_history_btn[0])
                    time.sleep(0.5)
                    update_history_btn[0].click()
                    did_update = True
                    
                    print("Waiting for history update to finish natively (allowing up to 30s)...")
                    WebDriverWait(driver, 30).until(
                        EC.invisibility_of_element_located((By.CSS_SELECTOR, "a.action.secondary.btn-payment-history"))
                    )
                    time.sleep(3) 
                else:
                    print("✅ Account up to date. Proceeding directly.")
            except Exception as update_err:
                print(f"Note: Update check step bypassed or completed with warning: {update_err}")

            # Lookup for final print trigger
            print("Locating final 'View Bill' trigger...")
            view_bill_xpath = "//input[@type='submit' and (@value='View Bill' or @name='View Bill')]"
            
            try:
                view_bill_btn = WebDriverWait(driver, 15).until(
                    EC.presence_of_element_located((By.XPATH, view_bill_xpath))
                )
            except Exception:
                if did_update:
                    print("Button hidden after update sequence. Attempting layout refresh fallback...")
                    driver.refresh()
                    time.sleep(4)
                try:
                    view_bill_btn = WebDriverWait(driver, 15).until(
                        EC.presence_of_element_located((By.XPATH, view_bill_xpath))
                    )
                except Exception:
                    print("Could not find print trigger element after refresh fallback. Skipping this account.")
                    continue

            if view_bill_btn is not None:
                try:
                    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", view_bill_btn)
                    time.sleep(0.5)
                    view_bill_btn.click()
                except Exception:
                    try:
                        driver.execute_script("arguments[0].click();", view_bill_btn)
                    except Exception as click_err:
                        print(f"Click completely blocked: {click_err}. Skipping.")
                        continue
                print("View Bill triggered successfully!")
                time.sleep(3)
            else:
                print("Trigger button returned null reference layout. Skipping.")
                continue

            # --- PRINT HANDLING SECTION ---
            try:
                all_windows = driver.window_handles
                if len(all_windows) > 1:
                    for window in all_windows:
                        if window != main_window_handle:
                            driver.switch_to.window(window)
                            break
                
                print("Saving PDF statement...")
                driver.execute_script("window.print();")
                time.sleep(2) 

                all_windows = driver.window_handles
                if len(all_windows) > 1:
                    if driver.current_window_handle != main_window_handle:
                        driver.close()
            
            except Exception as print_error:
                print(f"⚠️ Notice: Print window frame state fluctuated on this item ({print_error}).")
                time.sleep(2)
            
            finally:
                try:
                    all_windows = driver.window_handles
                    if main_window_handle in all_windows:
                        driver.switch_to.window(main_window_handle)
                    else:
                        driver.switch_to.window(all_windows[0])
                        main_window_handle = driver.current_window_handle
                except Exception:
                    pass
                time.sleep(0.5)

        print(f"\nFinished! Processed accounts complete. Check outputs in: '{download_folder}'")

    except Exception as e:
        print(f"An error occurred during automation: {e}")
    finally:
        try:
            driver.quit()
        except:
            pass

if __name__ == "__main__":
    MY_USER = "ac_ap@westlite.com.my"
    MY_PASS = "Westlite123"
    
    download_all_saj_bills(MY_USER, MY_PASS)