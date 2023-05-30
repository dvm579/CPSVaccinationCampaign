import os
from phl_tools import phlwebdriver
from datetime import date, datetime
import time
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException, ElementNotInteractableException
from selenium.webdriver.common.keys import Keys
import pandas as pd
import warnings

from aspen import standardize_cols

icare_user = 'Zul.kapadia'
icare_pass = 'HXntDDn9'

warnings.simplefilter('ignore')


def manifest_to_icare(clean_manifest_csv: str):
    patient_list = pd.read_csv(clean_manifest_csv)
    patient_list['DOB'] = pd.to_datetime(patient_list['DOB']).dt.date

    return standardize_cols(patient_list)[['LastName', 'FirstName', 'DOB']].drop_duplicates()


def get_patient(fname: str, lname: str, dob: date = None, driver=phlwebdriver.seleniumWebdriver()):
    df = pd.DataFrame(columns=['FirstName', 'LastName', 'DOB', 'icare_status', 'vaccine',
                               'overdue date (via i-care)'])
    empty = {'FirstName': fname, 'LastName': lname, 'DOB': dob}

    driver.get('https://icare.dph.illinois.gov/icare2/Patient/Search')
    time.sleep(0.7)
    if driver.current_url == 'https://dph.partner.illinois.gov/my.policy':
        time.sleep(1.0)
        driver.find_element(By.XPATH, "/html/body/table[2]/tbody/tr/td[1]/table/tbody/tr[2]/td/a").click()

        time.sleep(1.0)
        driver.find_element(By.XPATH, "/html/body/table[2]/tbody/tr/td[1]/form/table/tbody/tr[3]/td/input").send_keys(icare_user)
        driver.find_element(By.XPATH, "/html/body/table[2]/tbody/tr/td[1]/form/table/tbody/tr[4]/td/input").send_keys(icare_pass)
        driver.find_element(By.XPATH, "/html/body/table[2]/tbody/tr/td[1]/form/table/tbody/tr[6]/td/input").click()
        time.sleep(1.0)
        try:
            driver.find_element(By.ID, "AgreeButton").click()
            time.sleep(1.0)
        except NoSuchElementException:
            pass
        print('Page Initialized')

    driver.find_element(By.ID, 'FN').send_keys(fname.upper())
    driver.find_element(By.ID, 'LN').send_keys(lname.upper())
    if dob:
        driver.find_element(By.ID, 'DB').send_keys(dob.strftime('%m%d%Y'))
    driver.find_element(By.ID, 'SearchPatientButton').send_keys(Keys.ENTER)

    time.sleep(1.0)
    results_table = driver.find_element(By.ID, 'SearchResultTable')
    rows = results_table.find_element(By.TAG_NAME, 'tbody').find_elements(By.TAG_NAME, 'tr')
    if len(rows) >= 2:
        new_row = empty.copy()
        new_row.setdefault('icare_status', 'ERROR: Multiple I-CARE Matches Found.')
        df = df.append(new_row, ignore_index=True)
        print("ERROR - Multiple matches found for {fname} {lname}.".format(fname=fname, lname=lname))
        return df
    else:
        try:
            rows[0].find_elements(By.TAG_NAME, 'td')[0].find_element(By.TAG_NAME, 'a').click()
        except NoSuchElementException:
            new_row = empty.copy()
            new_row['icare_status'] = 'ERROR: No I-CARE Matches Found.'
            df = df.append(new_row, ignore_index=True)
            print("ERROR - No matches found for {fname} {lname}.".format(fname=fname, lname=lname))
            return df

    time.sleep(1.0)
    driver.get('https://icare.dph.illinois.gov/icare2/Report/Patient/shot/' + driver.current_url.split('/')[-2])

    time.sleep(2.0)
    try:
        overdue_rows = driver.find_element(By.ID, "ValidOverdueDataTable").find_element(By.TAG_NAME, 'table')\
                             .find_element(By.TAG_NAME, 'tbody').find_elements(By.TAG_NAME, 'tr')
        for row in overdue_rows:
            data = row.find_elements(By.TAG_NAME, 'td')
            new_row = empty.copy()
            new_row.setdefault('icare_status', 'overdue')
            new_row.setdefault('vaccine', data[1].text)
            new_row.setdefault('overdue date (via i-care)', datetime.strptime(data[0].text, '%m/%d/%Y').date())
            df = df.append(new_row, ignore_index=True)
            del data, new_row
    except NoSuchElementException:
        pass

    # try:
    #     invalid_rows = driver.find_element(By.ID, "InvalidDataTable")\
    #                          .find_element(By.TAG_NAME, 'tbody').find_elements(By.TAG_NAME, 'tr')
    #     for row in invalid_rows:
    #         data = row.find_elements(By.TAG_NAME, 'td')
    #         new_row = empty.copy()
    #         new_row.setdefault('icare_status', 'invalid')
    #         new_row.setdefault('vaccine', data[0].text)
    #         new_row.setdefault('overdue_date (via i-care)', datetime.strptime(data[3].text, '%m/%d/%Y').date())
    #         df = df.append(new_row, ignore_index=True)
    #         del data, new_row
    # except NoSuchElementException:
    #     pass

    print("{fname} {lname} history retrieved.".format(fname=fname, lname=lname))
    return df


def generate_icare_history(patient_df: pd.DataFrame):
    patient_df['DOB'] = pd.to_datetime(patient_df['DOB']).dt.date
    df = pd.DataFrame(columns=['FirstName', 'LastName', 'DOB', 'icare_status', 'vaccine', 'overdue date (via i-care)'])
    driver = phlwebdriver.seleniumWebdriver(headless=True)
    for index, row in patient_df.iterrows():
        fname = row['FirstName']
        lname = row['LastName']
        try:
            dob = date(row['DOB'].year, row['DOB'].month, row['DOB'].day)
        except TypeError:
            dob = None
        try:
            patient_data = get_patient(fname, lname, dob, driver)
        except:
            print('\nWebdriver Error - restarting ...\n')
            driver.quit()
            driver = phlwebdriver.seleniumWebdriver(headless=True)
            patient_data = get_patient(fname, lname, dob, driver)
        df = pd.concat([df, patient_data], ignore_index=True)
    return df


if __name__ == '__main__':
    for input_file in ['cicslongwood1']:
        patients = manifest_to_icare(f"input/{input_file}.csv")
        output = generate_icare_history(patients)
        output.to_csv(path_or_buf=f'output/scraper-out/{input_file}-out.csv')
        os.remove(f"input/{input_file}.csv")
