# --- এই ফাংশনটি পরিবর্তন করতে হবে ---
@app.route('/', methods=['GET'])
def get_declension_api():
    user_word = request.args.get('word')
    if not user_word:
        return jsonify({'error': 'Please provide a word. Example: /?word=Auto'}), 400

    found_article, html_page = find_word_data(user_word)
    if html_page:
        table_data = scrape_declension_table(html_page)

        # --- নতুন কোড শুরু ---
        if table_data and len(table_data) > 0:
            # টেবিলের প্রথম আইটেম থেকে singular শব্দটি নেওয়া হচ্ছে
            main_singular_form = table_data[0].get("singular", "")

            # নতুন ফরম্যাটে আউটপুট তৈরি করা
            final_response = {
                "main_singular": main_singular_form,
                "declensions": table_data
            }
            return jsonify(final_response)
        # --- নতুন কোড শেষ ---
            
        else:
            return jsonify({'error': f"A data table could not be found for the word: '{user_word}'"}), 404
    else:
        return jsonify({'error': f"The word '{user_word}' could not be found."}), 404
