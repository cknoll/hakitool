import os
import sys
import logging

import deploymentutils as du
from ipydex import IPS, activate_ips_on_exception

from flask import Flask, render_template, request, redirect, url_for, abort
from .search_engine import TextFileIndexer
from . import util


# simple storage for global data
class Container:
    pass


APP_NAME = "hakitool"
c = Container()
c.LOGFILENAME = f"{APP_NAME}.log"


def init(confpath="config.toml", test_mode=False):
    """
    Initialize globally accessible variables
    """

    c.cfg = du.get_nearest_config(confpath)

    LOGLEVEL = c.cfg("dep::LOGLEVEL")
    assert LOGLEVEL in ("DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL")
    loglevel = getattr(logging, LOGLEVEL)

    c.logger = logging.getLogger(APP_NAME)

    # disable debug messages from other loggers
    for k, v in logging.Logger.manager.loggerDict.items():
        if not isinstance(v, logging.PlaceHolder) and not k.startswith(APP_NAME):
            v.setLevel("WARNING")

    stdout_handler = logging.StreamHandler(sys.stdout)
    stdout_handler.setLevel(loglevel)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    no_color_formatter = util.NoColorFormatter()
    stdout_handler.setFormatter(formatter)
    file_handler = logging.FileHandler(c.LOGFILENAME)
    file_handler.setFormatter(no_color_formatter)

    logging.basicConfig(level=loglevel, handlers=[
        file_handler,
        stdout_handler
    ])

    if os.getenv("USER") == c.cfg("dep::user"):
        c.HOSTTYPE = "SERVER"
    else:
        c.HOSTTYPE = "LOCAL"

    c.logger.info(f"{APP_NAME} started with {c.HOSTTYPE=} and loglevel {LOGLEVEL}")


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



def create_app(config=None):
    c.logger.debug(f"creating app object")

    app = Flask(__name__, instance_relative_config=True)

    # Register type filter function
    @app.template_filter('type')
    def format_type(obj) -> str:
        """Jinja2 template filter to get object type"""
        return str(type(obj).__name__)


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

    return app


def main():
    init()
    app = create_app()
    c.logger.info("start app in debug mode")
    app.run(host='0.0.0.0', port=8000, debug=True)


def uwsgi_entry(*args, **kwargs):
    init()
    app = create_app()
    c.logger.info("start flask app via uwsgi")
    c.logger.debug(f"{args=}")
    c.logger.debug(f"{kwargs=}")
    return app(*args, **kwargs)

if __name__ == "__main__":
    main()
