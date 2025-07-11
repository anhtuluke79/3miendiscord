import discord
from discord.ext import commands, tasks
from discord import app_commands
import os
from dotenv import load_dotenv
import requests
from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime, timedelta

# === Crawl từ xosoketqua.com ===
def crawl_xsmb_xosoketqua(date_dt):
    date_str_url = date_dt.strftime("%d-%m-%Y")
    url = f"https://xosoketqua.com/xsmb-{date_str_url}.html"
    try:
        resp = requests.get(url, timeout=10)
        soup = BeautifulSoup(resp.text, "html.parser")
        table = soup.find("table", {"id": "result_tab_mb"})
        if not table:
            return None
        result = {'date': date_dt.strftime("%Y-%m-%d")}
        trs = table.find_all("tr")
        for tr in trs:
            tds = tr.find_all("td")
            if not tds: continue
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
        return result
    except Exception as e:
        print(f"[xosoketqua] Lỗi: {e}")
        return None

# === Crawl từ xosomn.mobi (dự phòng) ===
def crawl_xsmb_xosomn(date_dt):
    date_str_url = date_dt.strftime("%d-%m-%Y")
    url = f"https://xosomn.mobi/ket-qua-xo-so-mien-bac/ngay-{date_str_url}"
    try:
        resp = requests.get(url, timeout=10)
        soup = BeautifulSoup(resp.text, "html.parser")
        table = soup.find("table", {"class": "bkqmienbac"})
        if not table:
            return None
        result = {'date': date_dt.strftime("%Y-%m-%d")}
        trs = table.find_all("tr")
        for tr in trs:
            tds =
