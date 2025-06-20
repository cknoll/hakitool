import os
import re
import pickle
from pathlib import Path

class TextFileIndexer:
    def __init__(self, directory):
        self.directory = directory
        self.index_file = "file_index.pkl"
        self.index = {}

    def build_index(self):
        """Build an index of all words in all text files"""
        print("Building index... (This may take a while for many files)")
        self.index = {}

        txt_files = list(Path(self.directory).glob("*.txt"))
        total_files = len(txt_files)

        for i, filepath in enumerate(txt_files, 1):
            if i % 100 == 0 or i == total_files:
                print(f"Indexing... {i}/{total_files} files processed", end='\r')

            try:
                with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read().lower()
                    words = set(re.findall(r'\w+', content))
                    for word in words:
                        if word not in self.index:
                            self.index[word] = []
                        self.index[word].append(str(filepath))
            except Exception as e:
                print(f"\nError processing {filepath}: {e}")

        # Save index to file
        with open(self.index_file, 'wb') as f:
            pickle.dump(self.index, f)
        print("\nIndex built and saved successfully.")

    def load_index(self):
        """Load existing index from file"""
        if os.path.exists(self.index_file):
            with open(self.index_file, 'rb') as f:
                self.index = pickle.load(f)
            return True
        return False

    def search_in_index(self, search_term):
        """Search for term in the index"""
        search_term = search_term.lower()
        if search_term in self.index:
            return self.index[search_term]
        return []

    def search_in_files(self, search_term, context_lines=3):
        """Search for term in files, showing context"""
        # First try to use the index
        possible_files = self.search_in_index(search_term)
        if not possible_files:
            print(f"No files in index contain '{search_term}'. Performing full search...")
            possible_files = [str(f) for f in Path(self.directory).glob("*.txt")]

        results = []
        search_re = re.compile(re.escape(search_term), re.IGNORECASE)

        for filepath in possible_files:
            try:
                with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                    lines = f.readlines()
                    for i, line in enumerate(lines):
                        if search_re.search(line):
                            # Get context lines
                            start = max(0, i - context_lines)
                            end = min(len(lines), i + context_lines + 1)
                            context = ''.join(lines[start:end])
                            results.append((filepath, context))
                            break  # Only show first match per file
            except Exception as e:
                print(f"Error searching {filepath}: {e}")

        return results

def main():
    # directory = input("Enter the directory containing text files (default: current directory): ") or "."
    directory = "output/fulltext"

    indexer = TextFileIndexer(directory)

    # Try to load existing index or build new one
    if not indexer.load_index():
        print("No existing index found.")
        if input("Build a new index? (y/n): ").lower() == 'y':
            indexer.build_index()
        else:
            print("Searching without index will be slower.")

    while True:
        search_term = input("\nEnter search term (or 'quit' to exit): ").strip()
        if search_term.lower() == 'quit':
            break
        if not search_term:
            continue

        results = indexer.search_in_files(search_term)

        if not results:
            print(f"No matches found for '{search_term}'")
            continue

        print(f"\nFound {len(results)} files containing '{search_term}':")
        for i, (filename, context) in enumerate(results, 1):
            print(f"\n{'='*50}\nMatch {i}: {filename}\n{'='*50}")
            print(context)

if __name__ == "__main__":
    main()
