# main.py

import requests
import json
from bs4 import BeautifulSoup
from flask import Flask, request, Response

# Flask অ্যাপ অবজেক্ট তৈরি করা
app = Flask(__name__)
# JSON কী-গুলোকে (keys) বর্ণানুক্রমে সাজানো বন্ধ করা হয়েছে
app.config['JSON_SORT_KEYS'] = False


def find_word_data(word):
    """
    এই ফাংশনটি একটি জার্মান শব্দের জন্য সঠিক আর্টিকেল ও পেজের HTML কন্টেন্ট খুঁজে বের করে।
    """
    formatted_word = word.strip().capitalize()
    articles = ['der', 'die', 'das']
    for article in articles:
        url = f"https://der-artikel.de/{article}/{formatted_word}.html"
        try:
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                # উমলাউট সমস্যার সমাধানের জন্য এনকোডিং স্পষ্টভাবে সেট করা হয়েছে
                response.encoding = 'utf-8'
                return article, response.text
        except requests.exceptions.RequestException:
            continue
    return None, None


def scrape_declension_table(html_content):
    """
    এই ফাংশনটি HTML কন্টেন্ট থেকে ডিক্লেনশন টেবিল স্ক্র্যাপ করে।
    """
    soup = BeautifulSoup(html_content, 'html.parser')
    declension_data = []
    table = soup.find('table', class_='table')
    if not table:
        return None
    try:
        rows = table.find('tbody').find_all('tr')
        for row in rows:
            cells = row.find_all('td')
            if len(cells) == 3:
                case = cells[0].get_text(strip=True)
                singular = " ".join(cells[1].stripped_strings)
                plural = " ".join(cells[2].stripped_strings)
                # আপনার অনুরোধ অনুযায়ী ডিকশনারির ক্রম ঠিক করা হয়েছে
                row_data = {
                    "singular": singular,
                    "plural": plural,
                    "case": case
                }
                declension_data.append(row_data)
    except Exception:
        return None
    return declension_data


@app.route('/', methods=['GET'])
def get_declension_api():
    """
    এই ফাংশনটি API রিকোয়েস্ট হ্যান্ডেল করে এবং চূড়ান্ত ফলাফল পাঠায়।
    """
    user_word = request.args.get('word')
    if not user_word:
        error_json = json.dumps({'error': 'Please provide a word. Example: /?word=Auto'})
        return Response(error_json, status=400, mimetype='application/json')

    found_article, html_page = find_word_data(user_word)
    if html_page:
        table_data = scrape_declension_table(html_page)
        if table_data:
            main_singular_form = table_data[0].get("singular", "")
            
            # আপনার অনুরোধ অনুযায়ী চূড়ান্ত JSON অবজেক্ট তৈরি করা
            final_response_dict = {
                "main_singular": main_singular_form,
                "declensions": table_data
            }
            # JSON স্ট্রিং তৈরি এবং Response হিসেবে পাঠানো
            json_string = json.dumps(final_response_dict, indent=2, ensure_ascii=False)
            return Response(json_string, mimetype='application/json')
        else:
            error_json = json.dumps({'error': f"A data table could not be found for the word: '{user_word}'"})
            return Response(error_json, status=404, mimetype='application/json')
    else:
        error_json = json.dumps({'error': f"The word '{user_word}' could not be found."})
        return Response(error_json, status=404, mimetype='application/json')

