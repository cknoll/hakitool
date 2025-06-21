from flask import Flask, render_template, request, redirect, url_for, abort
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

            # TODO-AIDER: the object `results` has the wrong structure.
            # I think it should be a list of 2-tuples where the first entry is a string and the second entry is a list of strings.
            # However it is a list of 2-tuples where the first entry is a string and the second entry is also a string (and not a list of strings as it should be).
            # Please figure out the reason and correct it. If you think my observation is wrong please report.
            results = indexer.search_in_files(search_term)
            return render_template('results.html',
                                search_term=search_term,
                                results=results)
        return redirect(url_for('home'))

    return render_template('index.html')

@app.route('/file/<path:filename>')
def show_file(filename: str) -> str:
    """Show full file content with all matches highlighted.

    Args:
        filename: Path to the file to display

    Returns:
        str: Rendered template with file content
    """
    try:
        with open(filename, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        return render_template('file_view.html', filename=filename, content=content)
    except Exception as e:
        abort(404)

if __name__ == '__main__':
    app.run(debug=True)
