from flask import Flask, render_template, request, redirect, url_for, abort
from search_engine import TextFileIndexer

app = Flask(__name__)

# Register type filter function
@app.template_filter('type')
def format_type(obj) -> str:
    """Jinja2 template filter to get object type"""
    return str(type(obj).__name__)

def nested_to_html(data, indent=0):
    result = ""
    if isinstance(data, (list, tuple)):
        result += "<li>{} of length {}<ul>\n".format(type(data).__name__, len(data))
        for item in data:
            result += nested_to_html(item, indent + 1)
        result += "</ul></li>\n"
    else:
        result += "<li>{}: {}</li>\n".format(type(data).__name__, repr(data))
    return result


@app.template_filter('get_html_overview')
def get_html_overview(data):
    html = '<ul>\n' + nested_to_html(data) + '</ul>'
    return html


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

# HINT-FOR-AIDER: the following function has to be adapted (route, code and docstring)
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
            search_term = request.args.get('search_term', '')
            content = f.read()
        return render_template('file_view.html',
                            filename=filename,
                            content=content,
                            search_term=search_term)
    except Exception as e:
        abort(404)

if __name__ == '__main__':
    app.run(debug=True)
