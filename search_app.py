from flask import Flask, render_template, request, redirect, url_for
from search_engine import TextFileIndexer

app = Flask(__name__)

app.config['SEARCH_DIRECTORY'] = "output/fulltext"
indexer = TextFileIndexer(app.config['SEARCH_DIRECTORY'])

@app.route('/', methods=['GET', 'POST'])
def home() -> str:
    """Handle the main search page and form submission.

    GET requests show the search form.
    POST requests process searches and show results.

    Returns:
        str: Rendered HTML template
    """
    # Try to load index on first request
    if not hasattr(indexer, 'index') or not indexer.index:
        indexer.load_index()

    if request.method == 'POST':
        search_term = request.form.get('search_term', '').strip()
        if search_term:
            results = indexer.search_in_files(search_term)
            return render_template('results.html',
                                search_term=search_term,
                                results=results)
        return redirect(url_for('home'))

    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True)
