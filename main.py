import csv
import multiprocessing
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from concurrent.futures import ProcessPoolExecutor

from utils.choices import get_age_interval, get_totChol_interval, get_sysBP_interval, map_meds, map_smoker, map_diabete

URL = 'https://qxmd.com/calculate/calculator_252/framingham-risk-score-2008'

CSV_LOCK = None
OUTFILE = None

def fill_form_and_get_results(driver, gender, age_interval, totChol_interval, hdl_interval, sysBP_interval, medBP, smoker, diabetic):
    try:
        WebDriverWait(driver, 15).until(
            EC.element_to_be_clickable((By.NAME, gender))
        ).click()

        WebDriverWait(driver, 15).until(
            EC.element_to_be_clickable((By.NAME, age_interval))
        ).click()

        WebDriverWait(driver, 15).until(
            EC.element_to_be_clickable((By.NAME, totChol_interval))
        ).click()

        WebDriverWait(driver, 15).until(
            EC.element_to_be_clickable((By.NAME, hdl_interval))
        ).click()

        WebDriverWait(driver, 15).until(
            EC.element_to_be_clickable((By.NAME, sysBP_interval))
        ).click()

        WebDriverWait(driver, 15).until(
            EC.element_to_be_clickable((By.ID, medBP))
        ).click()

        WebDriverWait(driver, 15).until(
            EC.element_to_be_clickable((By.ID, smoker))
        ).click()

        WebDriverWait(driver, 15).until(
            EC.element_to_be_clickable((By.ID, diabetic))
        ).click()

        WebDriverWait(driver, 15).until(
            EC.element_to_be_clickable((By.ID, "input-choice-7245"))
        ).click()

        WebDriverWait(driver, 15).until(
            EC.element_to_be_clickable((By.ID, "button-3483"))
        ).click()

        calc_result = WebDriverWait(driver, 20).until(
            EC.visibility_of_all_elements_located((By.ID, "answer-1758"))
        )

        calc_result = calc_result[0].text

        risk_result = WebDriverWait(driver, 20).until(
            EC.visibility_of_all_elements_located((By.ID, "answer-1759"))
        )

        risk_result = risk_result[0].text

        return calc_result, risk_result
    
    except Exception as e:
        print(f"Erro ao preencher formulário: {e}")
        return None, None

def process_row(row):
    driver = None
    try:
        gender = "Male" if row["male"] == '1' else "Female"
        age = int(row["age"])
        totChol = float(row["totChol"])
        sysBP = float(row["sysBP"])

        medBP_value = map_meds(row["BPMeds"])
        smoker_value = map_smoker(row["currentSmoker"])
        isDiabetic = map_diabete(row["diabetes"])

        age_interval = get_age_interval(age)
        totChol_interval = get_totChol_interval(totChol)
        sysBP_interval = get_sysBP_interval(sysBP)
        
        hdl_interval_min = "&lt;0.9 mmol/L"

        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")

        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
        driver.get(URL)
        driver.maximize_window()


        try:
            cookie_button = WebDriverWait(driver, 5).until(
                EC.element_to_be_clickable((By.ID, "onetrust-accept-btn-handler"))
            )
            cookie_button.click()
        except:
            pass
        
        calc_hdl_min, risk_hdl_min = fill_form_and_get_results(
            driver, gender, age_interval, totChol_interval, hdl_interval_min,
            sysBP_interval, medBP_value, smoker_value, isDiabetic
        )

        if calc_hdl_min is None or risk_hdl_min is None:
            raise ValueError("Resultados não encontrados")

        row["calc_hdl_min"] = calc_hdl_min
        row["risk_hdl_min"] = risk_hdl_min

        print(f"Processado: Age {age}, totChol {totChol}, sysBP {sysBP}")


    except Exception as e:
        print(f"Erro ao processar a linha {row}: {e}")
    finally:
        if driver:
            driver.quit()
        

    try:
        with CSV_LOCK:
            with open(OUTFILE, "a", newline='', encoding="utf-8") as outfile:
                writer = csv.DictWriter(outfile, fieldnames=row.keys())
                writer.writerow(row)
    except Exception as e:
        print(f"Erro ao escrever a linha no arquivo: {e}")

    return row

def main():
    input_filename = "teste.csv"  
    output_filename = "results.csv"

    with open(input_filename, newline='', encoding="utf-8") as csvfile:
        reader = csv.DictReader(csvfile)
        linhas = [row for row in reader]

    fieldnames = list(linhas[0].keys())
    for col in ["calc_hdl_min", "risk_hdl_min"]:
        if col not in fieldnames:
            fieldnames.append(col)

    with open(output_filename, "w", newline='', encoding="utf-8") as outfile:
        writer = csv.DictWriter(outfile, fieldnames=fieldnames)
        writer.writeheader()

    lock = multiprocessing.Lock()
    
    global CSV_LOCK, OUTFILE
    CSV_LOCK = lock
    OUTFILE = output_filename
    
    with ProcessPoolExecutor(max_workers=4) as executor:
        results = list(executor.map(process_row, linhas))

    print("Processamento concluído. Resultados armazenados em", output_filename)

if __name__ == "__main__":
    main()
