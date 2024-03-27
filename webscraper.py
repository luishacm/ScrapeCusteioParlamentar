import time
from typing import List
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import pandas as pd


def obter_meses(driver: webdriver.Chrome) -> List[str]:
    """
    Obtém a lista de meses disponíveis no dropdown.

    :param driver: A instância do Selenium webdriver.
    :return: Uma lista com os valores dos meses.
    """
    meses_xpath = "//select[@id='data']"
    data = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, meses_xpath)))
    descendentes = data.find_elements(By.XPATH, ".//*")
    return [option.get_attribute("value") for option in descendentes]


def raspar_dados(driver: webdriver.Chrome, mes: str) -> pd.DataFrame:
    """
    Raspa os dados para um determinado mês.

    :param driver: A instância do Selenium webdriver.
    :param mes: O valor do mês.
    :return: Um DataFrame contendo os dados raspados.
    """
    select = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, "//select[@id='data']")))
    select.click()
    time.sleep(1)

    select = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, f"//option[@value='{mes}']")))
    select.click()
    time.sleep(1)

    filtrar = driver.find_element(By.ID, "pesquisar-custeio")
    filtrar.click()
    time.sleep(1)

    for _ in range(10):
        try:
            resultado = WebDriverWait(driver, 3).until(EC.presence_of_element_located((By.XPATH, "//div[@id='resultadoPesquisa_custeio']")))
            if "Não retornou resultados." in resultado.text:
                return
            else:
                WebDriverWait(driver, 3).until(EC.presence_of_all_elements_located((By.XPATH, "//h2[contains(text(),'Resultados da pesquisa')]")))
                break
        except:
            pass
        filtrar.click()
        time.sleep(2)
    
    html = driver.page_source
    soup = BeautifulSoup(html, "html.parser")
    table = soup.select_one("table")
    rows = table.find_all("tr")

    data = []
    for row in rows[1:]:
        cols = row.find_all("td")
        if len(cols) == 3:
            data.append({
                "Vereador": cols[0].text.strip(),
                "Detalhamento": cols[1].text.strip(),
                "Valor": cols[2].text.strip(),
                "Data": mes
            })
    return pd.DataFrame(data)


def main():
    """
    Função principal para executar o processo de web scraping.
    """
    chrome_driver_path = "chromedriver.exe"
    service = Service(chrome_driver_path)
    driver = webdriver.Chrome(service=service)
    
    # Definir um cabeçalho para a requisição
    driver.header = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.82 Safari/537.36"
    }
    
    driver.get("https://www.cmbh.mg.gov.br/transparencia/vereadores/custeio-parlamentar")

    # Aguarda até que a página seja completamente carregada
    WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "data")))

    # Encontra e clica no elemento após esperar que ele seja clicável
    WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.ID, "data")))
    meses = obter_meses(driver)
    print(meses)

    df_custeio_parlamentar = pd.DataFrame(columns=["Vereador", "Detalhamento", "Valor", "Data"])
    for mes in meses:
        df_mes = raspar_dados(driver, mes)
        if df_mes is None:
            continue

        df_custeio_parlamentar = pd.concat([df_custeio_parlamentar, df_mes], ignore_index=True)
        print(df_custeio_parlamentar)

    df_custeio_parlamentar.set_index("Data", inplace=True)
    df_custeio_parlamentar.to_csv("Custeio_Parlamentar.csv")
    print(df_custeio_parlamentar)

    driver.quit()


if __name__ == "__main__":
    main()