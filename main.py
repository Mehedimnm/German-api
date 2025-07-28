# main.py

import requests
from bs4 import BeautifulSoup
from flask import Flask, request, Response # jsonify এর বদলে Response ইম্পোর্ট করা হয়েছে
import json # json লাইব্রেরি ইম্পোর্ট করা হয়েছে

app = Flask(__name__)
# Flask-কে কী (key) সর্ট না করার জন্য এই লাইনটি থাকবে
app.config['JSON_SORT_KEYS'] = False

def find_word_data(word):
    formatted_word = word.strip().capitalize()
    articles = ['der', 'die', 'das']
    for article in articles:
        url = f"https://der-artikel.de/{article}/{formatted_word}.html"
        try:
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                return article, response.text
        except requests.exceptions.RequestException:
            continue
    return None, None

def scrape_declension_table(html_content):
    soup = BeautifulSoup(html_content, 'html.parser')
    declension_data = []
    table = soup.find('table', class_='table')
    if not table: return None
    try:
        rows = table.find('tbody').find_all('tr')
        for row in rows:
            cells = row.find_all('td')
            if len(cells) == 3:
                case = cells[0].get_text(strip=True)
                singular = " ".join(cells[1].stripped_strings)
                plural = " ".join(cells[2].stripped_strings)
                # ডিকশনারির ক্রম এখানে ঠিক করা আছে
                row_data = {
                    "singular": singular,
                    "plural": plural,
                    "case": case
                }
                declension_data.append(row_data)
    except Exception: return None
    return declension_data

@app.route('/', methods=['GET'])
def get_declension_api():
    user_word = request.args.get('word')
    if not user_word:
        # এখানেও ম্যানুয়াল রেসপন্স ব্যবহার করা হলো
        error_json = json.dumps({'error': 'Please provide a word. Example: /?word=Auto'})
        return Response(error_json, status=400, mimetype='application/json')

    found_article, html_page = find_word_data(user_word)
    if html_page:
        table_data = scrape_declension_table(html_page)
        if table_data:
            main_singular_form = table_data[0].get("singular", "")
            
            # --- এই অংশে মূল পরিবর্তন আনা হয়েছে ---
            # ম্যানুয়ালি ডিকশনারির ক্রম তৈরি করা
            final_response_dict = {
                "main_singular": main_singular_form,
                "declensions": table_data
            }
            # ডিকশনারিকে JSON স্ট্রিং-এ পরিণত করা (indent=2 দিয়ে সুন্দরভাবে সাজানো হলো)
            json_string = json.dumps(final_response_dict, indent=2, ensure_ascii=False)
            # ম্যানুয়ালি একটি Response অবজেক্ট তৈরি করে রিটার্ন করা
            return Response(json_string, mimetype='application/json')
            # --- পরিবর্তন শেষ ---

        else:
            error_json = json.dumps({'error': f"A data table could not be found for the word: '{user_word}'"})
            return Response(error_json, status=404, mimetype='application/json')
    else:
        error_json = json.dumps({'error': f"The word '{user_word}' could not be found."})
        return Response(error_json, status=404, mimetype='application/json')

