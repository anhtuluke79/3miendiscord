import requests
from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime, timedelta

def crawl_xsmb_to_csv(csv_path='xs_mienbac_full.csv', days=30):
    """
    Crawl XSMB trong N ngày gần nhất từ xosoketqua.com, ghi ra file CSV.
    """
    base_url = "https://xosoketqua.com/xo-so-mien-bac-ngay-{}.html"  # VD: https://xosoketqua.com/xo-so-mien-bac-ngay-2024-07-15.html
    data = []
    for i in range(days):
        date_dt = datetime.today() - timedelta(days=i)
        date_str = date_dt.strftime("%Y-%m-%d")
        url = base_url.format(date_str)
        resp = requests.get(url)
        soup = BeautifulSoup(resp.text, "html.parser")
        table = soup.find("table", {"id": "result_tab_mb"})
        if not table:
            continue
        result = {'date': date_str}
        trs = table.find_all("tr")
        for tr in trs:
            tds = tr.find_all("td")
            if not tds:
                continue
            label = tds[0].text.strip()
            numbers = tds[1].text.strip().split('-')
            numbers = [x.strip() for x in numbers if x.strip()]
            if label.startswith("ĐB"):
                result['DB'] = numbers[0] if numbers else ""
            elif label.startswith("Nhất"):
                result['G1'] = numbers[0] if numbers else ""
            elif label.startswith("Nhì"):
                for j, num in enumerate(numbers):
                    result[f'G2_{j+1}'] = num
            elif label.startswith("Ba"):
                for j, num in enumerate(numbers):
                    result[f'G3_{j+1}'] = num
            elif label.startswith("Tư"):
                for j, num in enumerate(numbers):
                    result[f'G4_{j+1}'] = num
            elif label.startswith("Năm"):
                for j, num in enumerate(numbers):
                    result[f'G5_{j+1}'] = num
            elif label.startswith("Sáu"):
                for j, num in enumerate(numbers):
                    result[f'G6_{j+1}'] = num
            elif label.startswith("Bảy"):
                for j, num in enumerate(numbers):
                    result[f'G7_{j+1}'] = num
        data.append(result)
    df = pd.DataFrame(data)
    df.to_csv(csv_path, index=False, encoding='utf-8-sig')
    return csv_path
