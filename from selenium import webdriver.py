import os
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

def download_all_saj_bills():
    # 1. Setup download directory
    download_folder = os.path.abspath("all_saj_bills")
    if not os.path.exists(download_folder):
        os.makedirs(download_folder)

    # 2. Configure Chrome to silently "Print to PDF" without showing print dialogs
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
        # Note: Make sure this is your primary dashboard URL
        dashboard_url = "https://www.ranhillsaj.com.my/customer/account/" 
        
        driver.get(dashboard_url)
        print("Please log in manually on the browser window. Waiting 15 seconds...")
        time.sleep(15) 

        # Arrow dropdown selector
        arrow_selector = "#maincontent > div.columns.columns-flex > div.column.main > div.account-dashboard-info > div.group-bill-account > div > div.control-list-account > span"

        # Open the dropdown arrow once just to get the total count
        arrow_btn = WebDriverWait(driver, 15).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, arrow_selector))
        )
        arrow_btn.click()
        time.sleep(2)

        account_radios = driver.find_elements(By.NAME, "bill_account_id")
        total_accounts = len(account_radios)
        print(f"Successfully connected! Found {total_accounts} total accounts to process.")

        # 3. Main Automation Loop Through All Accounts
        for i in range(total_accounts):
            print(f"\nProcessing bill [{i+1}/{total_accounts}]...")
            
            # Re-navigate to clean dashboard screen to reset DOM memory
            driver.get(dashboard_url)
            time.sleep(4)

            # Click the dropdown arrow
            arrow_btn = WebDriverWait(driver, 8).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, arrow_selector))
            )
            arrow_btn.click()
            time.sleep(2)

            # Re-fetch the live radio button elements and isolate the row
            account_radios = driver.find_elements(By.NAME, "bill_account_id")
            current_radio = account_radios[i]
            account_value = current_radio.get_attribute("value")
            print(f"Selecting account value: {account_value}")
            
            current_radio.click()
            time.sleep(2)

            # Click 'View Bill Account' using verified CSS layout classes
            view_account_btn = WebDriverWait(driver, 6).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "a.action.secondary.manage"))
            )
            view_account_btn.click()
            print("Swapping account layout view... Waiting for page layer.")
            time.sleep(6) 

            # --- SMART CONDITIONAL CHECK FOR 'UPDATE PAYMENT HISTORY' ---
            try:
                # Look for the Update button using its unique class layout
                update_history_btn = driver.find_elements(By.CSS_SELECTOR, "a.action.secondary.btn-payment-history")
                
                if len(update_history_btn) > 0 and update_history_btn[0].is_displayed():
                    print("⚠️ 'Update Payment History' button detected! Refreshing account data...")
                    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", update_history_btn[0])
                    time.sleep(1)
                    update_history_btn[0].click()
                    
                    # Give the server plenty of time to process the system refresh update
                    print("Waiting 8 seconds for history update to finish...")
                    time.sleep(4)
                else:
                    print("✅ Account already up to date. Proceeding directly to bill download.")
            except Exception as update_err:
                print(f"Skipped update check step due to layout variance: {update_err}")

            # --- DYNAMIC LOOKUP FOR 'VIEW BILL' BUTTON ---
            print("Locating final 'View Bill' trigger...")
            view_bill_xpath = "//input[@type='submit' and (@value='View Bill' or @name='View Bill')]"
            
            try:
                view_bill_btn = WebDriverWait(driver, 6).until(
                    EC.presence_of_element_located((By.開(By.XPATH, view_bill_xpath)))
                )
            except Exception:
                # Fallback check: sometimes updating the payment history redirects the browser or alters the DOM slightly
                view_bill_btn = WebDriverWait(driver, 6).until(
                    EC.presence_of_element_located((By.XPATH, "//input[contains(@class, 'btn_bill_pdf')]"))
                )

            # Execution step
            if view_bill_btn is not None:
                original_window = driver.current_window_handle
                try:
                    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", view_bill_btn)
                    time.sleep(1.5)
                    view_bill_btn.click()
                    print("View Bill clicked successfully!")
                    time.sleep(4)
                except Exception:
                    # Powerful background script click if anything blocks it visually
                    driver.execute_script("arguments[0].click();", view_bill_btn)
                    print("View Bill triggered via JS engine script fallback!")
                    time.sleep(4)
            else:
                print("Could not find print trigger element for this loop.")
                continue

            # Evaluate context if a secondary window or print canvas tab opened up
            all_windows = driver.window_handles
            if len(all_windows) > 1:
                for window in all_windows:
                    if window != original_window:
                        driver.switch_to.window(window)
                        break
            
            # Silent print instruction outputs the PDF layout directly into the project directory
            print("Saving PDF statement to file...")
            driver.execute_script("window.print();")
            time.sleep(2.5)

            # Tidy up child windows and loop context tracking focus back to base dashboard
            if len(driver.window_handles) > 1:
                driver.close()
                driver.switch_to.window(original_window)
                time.sleep(1)

        print(f"\nFinished! All available bills successfully downloaded to: '{download_folder}'")

    except Exception as e:
        print(f"An error occurred during automation: {e}")
    finally:
        driver.quit()

if __name__ == "__main__":
    download_all_saj_bills()