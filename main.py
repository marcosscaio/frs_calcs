import csv
import time
import multiprocessing
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

from utils.choices import get_age_interval, get_totChol_interval, get_sysBP_interval, map_binary

URL = 'https://qxmd.com/calculate/calculator_253/framingham-risk-score-atp-iii#'

CSV_LOCK = None
OUTFILE = None

def init_worker(lock, out_file):
    global CSV_LOCK, OUTFILE
    CSV_LOCK = lock
    OUTFILE = out_file

def fill_form_and_get_results(driver, gender, age_interval, totChol_interval, hdl_interval, sysBP_interval, medBP, smoker, diabetic, stroke):

    gender_button = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.NAME, gender))
    )
    gender_button.click()

    age_button = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.NAME, age_interval))
    )
    age_button.click()

    totChol_button = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.NAME, totChol_interval))
    )
    totChol_button.click()

    hdl_button = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.NAME, hdl_interval))
    )
    hdl_button.click()

    sysBP_button = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.NAME, sysBP_interval))
    )
    sysBP_button.click()

    medBP_button = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.NAME, medBP))
    )
    medBP_button.click()

    smoker_button = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.NAME, smoker))
    )
    smoker_button.click()

    diabetic_button = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.NAME, diabetic))
    )

    stroke_button = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.NAME, stroke))
    )

    results_button = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.ID, "button-3483"))
    )
    results_button.click()

    time.sleep(2)

    calc_elements = WebDriverWait(driver, 10).until(
        EC.presence_of_all_elements_located((By.ID, "answer-1758"))
    )
    risk_elements = WebDriverWait(driver, 10).until(
        EC.presence_of_all_elements_located((By.ID, "answer-1759"))
    )

    calc_result = calc_elements[0].text
    risk_result = risk_elements[0].text

    return calc_result, risk_result

def process_row(row):
    try:
        gender = "Male" if int(row["male"]) == '1' else "Female"
        age = int(row["age"])
        smoker_value = map_binary(row["currentSmoker"])
        medBP_value = map_binary(row["BPMeds"])
        totChol = float(row["totChol"])
        sysBP = float(row["sysBP"])
        isDiabetic = map_binary(row["diabetes"])
        stroke_disease = map_binary(row["prevalentStroke"]) 

        age_interval = get_age_interval(age)
        totChol_interval = get_totChol_interval(totChol)
        sysBP_interval = get_sysBP_interval(sysBP)
        
        hdl_interval_min = "&lt;0.9 mmol/L"
        hdl_interval_max = "&ge;1.56 mmol/L"

        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--disable-gpu")

        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
        driver.maximize_window()
        driver.get(URL)
        time.sleep(2)

        try:
            cookie_button = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.ID, "onetrust-accept-btn-handler"))
            )
            cookie_button.click()
        except Exception:
            pass
        
        calc_hdl_min, risk_hdl_min = fill_form_and_get_results(
            driver, gender, age_interval, totChol_interval, hdl_interval_min,
            sysBP_interval, medBP_value, smoker_value, isDiabetic, stroke_disease
        )

        driver.quit()
        time.sleep(2)

        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
        driver.maximize_window()
        driver.get(URL)
        time.sleep(2)
        try:
            cookie_button = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.ID, "onetrust-accept-btn-handler"))
            )
            cookie_button.click()
        except Exception:
            pass

        calc_hdl_max, risk_hdl_max = fill_form_and_get_results(
            driver, gender, age_interval, totChol_interval, hdl_interval_max,
            sysBP_interval, medBP_value, smoker_value, isDiabetic, stroke_disease
        )
        driver.quit()
        time.sleep(2)

        row["calc_hdl_min"] = calc_hdl_min
        row["calc_hdl_max"] = calc_hdl_max
        row["risk_hdl_min"] = risk_hdl_min
        row["risk_hdl_max"] = risk_hdl_max

        print(f"Processado: Age {age}, totChol {totChol}, sysBP {sysBP}")
    except Exception as e:
        print(f"Erro ao processar a linha {row}: {e}")

    try:
        with CSV_LOCK:
            with open(OUTFILE, "a", newline='', encoding="utf-8") as outfile:
                writer = csv.DictWriter(outfile, fieldnames=row.keys())
                writer.writerow(row)
    except Exception as e:
        print(f"Erro ao escrever a linha no arquivo: {e}")

    return row

def main():
    input_filename = "arquivo.csv"  
    output_filename = ""

    with open(input_filename, newline='', encoding="utf-8") as csvfile:
        reader = csv.DictReader(csvfile)
        linhas = [row for row in reader]

    fieldnames = list(linhas[0].keys())
    for col in ["risk_hdl_min_chol_min"]:
        if col not in fieldnames:
            fieldnames.append(col)

    with open(output_filename, "w", newline='', encoding="utf-8") as outfile:
        writer = csv.DictWriter(outfile, fieldnames=fieldnames)
        writer.writeheader()

    lock = multiprocessing.Lock()
    pool = multiprocessing.Pool(processes=6, initializer=init_worker, initargs=(lock, output_filename))

    pool.map(process_row, linhas)
    pool.close()
    pool.join()

    print("Processamento concluído. Resultados armazenados em", output_filename)

if __name__ == "__main__":
    main()
