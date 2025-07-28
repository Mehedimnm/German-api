# main.py

import requests
from bs4 import BeautifulSoup
from flask import Flask, request, jsonify

app = Flask(__name__)
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
                row_data = {
                    "singular": singular,
                    "plural": plural,
                    "case": case
                }
                declension_data.append(row_data)
    except Exception: return None
    
    # যদি টেবিল পাওয়া যায় কিন্তু কোনো ডেটা না থাকে, তাহলে খালি লিস্ট রিটার্ন করবে
    return declension_data

# --- এই ফাংশনটি সম্পূর্ণ ঠিক করা হয়েছে ---
@app.route('/', methods=['GET'])
def get_declension_api():
    user_word = request.args.get('word')
    if not user_word:
        return jsonify({'error': 'Please provide a word. Example: /?word=Auto'}), 400

    found_article, html_page = find_word_data(user_word)
    if html_page:
        table_data = scrape_declension_table(html_page)

        # table_data তে কিছু থাকলে (খালি লিস্ট না হলে) এই কোড চলবে
        if table_data:
            main_singular_form = table_data[0].get("singular", "")
            final_response = {
                "main_singular": main_singular_form,
                "declensions": table_data
            }
            return jsonify(final_response)
        # যদি table_data তে কিছু না থাকে (None বা খালি লিস্ট)
        else:
            return jsonify({'error': f"A data table could not be found for the word: '{user_word}'"}), 404
    # যদি html_page খুঁজে না পাওয়া যায়
    else:
        return jsonify({'error': f"The word '{user_word}' could not be found."}), 404
