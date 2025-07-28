# main.py

import requests
import json
from bs4 import BeautifulSoup
from flask import Flask, request, Response
import translators as ts # নতুন লাইব্রেরি ইম্পোর্ট করা হয়েছে

app = Flask(__name__)
app.config['JSON_SORT_KEYS'] = False

# --- আগের ফাংশনগুলো অপরিবর্তিত থাকবে ---
def find_word_data(word):
    formatted_word = word.strip().capitalize()
    articles = ['der', 'die', 'das']
    for article in articles:
        url = f"https://der-artikel.de/{article}/{formatted_word}.html"
        try:
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                response.encoding = 'utf-8'
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
                row_data = { "singular": singular, "plural": plural, "case": case }
                declension_data.append(row_data)
    except Exception: return None
    return declension_data

# --- আগের '/ ' রুটটি অপরিবর্তিত থাকবে ---
@app.route('/', methods=['GET'])
def get_declension_api():
    user_word = request.args.get('word')
    if not user_word:
        error_json = json.dumps({'error': 'Please provide a word. Example: /?word=Auto'})
        return Response(error_json, status=400, mimetype='application/json')
    
    found_article, html_page = find_word_data(user_word)
    if html_page:
        table_data = scrape_declension_table(html_page)
        if table_data:
            main_singular_form = table_data[0].get("singular", "")
            final_response_dict = { "main_singular": main_singular_form, "declensions": table_data }
            json_string = json.dumps(final_response_dict, indent=2, ensure_ascii=False)
            return Response(json_string, mimetype='application/json')
        else:
            error_json = json.dumps({'error': f"A data table could not be found for the word: '{user_word}'"})
            return Response(error_json, status=404, mimetype='application/json')
    else:
        error_json = json.dumps({'error': f"The word '{user_word}' could not be found."})
        return Response(error_json, status=404, mimetype='application/json')


# --- 'translators' লাইব্রেরি দিয়ে এই ফাংশনটি নতুন করে লেখা হয়েছে ---
@app.route('/translate', methods=['GET'])
def translate_and_get_declension():
    bengali_word = request.args.get('bengali_word')
    if not bengali_word:
        error_json = json.dumps({'error': 'Please provide a Bengali word. Example: /translate?bengali_word=আপেল'})
        return Response(error_json, status=400, mimetype='application/json')

    try:
        # translators লাইব্রেরি ব্যবহার করে অনুবাদ করা হচ্ছে
        german_word = ts.translate_text(bengali_word, translator='google', from_language='bn', to_language='de')

        if not german_word:
            error_json = json.dumps({'error': 'Could not get German translation.'})
            return Response(error_json, status=500, mimetype='application/json')

        # অনুবাদ করা জার্মান শব্দটি দিয়ে মূল লজিকটি আবার চালানো হচ্ছে
        found_article, html_page = find_word_data(german_word)
        if html_page:
            table_data = scrape_declension_table(html_page)
            if table_data:
                main_singular_form = table_data[0].get("singular", "")
                final_response_dict = { "main_singular": main_singular_form, "declensions": table_data }
                json_string = json.dumps(final_response_dict, indent=2, ensure_ascii=False)
                return Response(json_string, mimetype='application/json')
            else:
                error_json = json.dumps({'error': f"Data table not found for the translated word: '{german_word}'"})
                return Response(error_json, status=404, mimetype='application/json')
        else:
            error_json = json.dumps({'error': f"The translated word '{german_word}' could not be found."})
            return Response(error_json, status=404, mimetype='application/json')

    except Exception as e:
        error_json = json.dumps({'error': 'An unexpected error occurred during translation.', 'details': str(e)})
        return Response(error_json, status=500, mimetype='application/json')

