import os
import re
import pickle
from pathlib import Path

class TextFileIndexer:
    def __init__(self, directory: str) -> None:
        """Initialize the TextFileIndexer with a directory to search.
        
        Args:
            directory: Path to the directory containing text files to index
        """
        self.directory = directory
        self.index_file = "file_index.pkl"
        self.index = {}

    def build_index(self) -> None:
        """Build an index of all words in all text files.
        
        Creates an inverted index mapping words to files containing them.
        The index is saved to disk as a pickle file for future use.
        
        Returns:
            None
        """
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

    def load_index(self) -> bool:
        """Load existing index from file.
        
        Returns:
            bool: True if index was loaded successfully, False otherwise
        """
        if os.path.exists(self.index_file):
            with open(self.index_file, 'rb') as f:
                self.index = pickle.load(f)
            return True
        return False

    def search_in_index(self, search_term: str) -> list[str]:
        """Search for term in the pre-built index.
        
        Args:
            search_term: Word to search for in the index
            
        Returns:
            list[str]: List of filepaths containing the term
        """
        search_term = search_term.lower()
        if search_term in self.index:
            return self.index[search_term]
        return []

    def search_in_files(self, search_term: str, context_lines: int = 3) -> list[tuple[str, str]]:
        """Search for term in files, showing surrounding context.
        
        Args:
            search_term: Text string to search for
            context_lines: Number of lines to show around each match
            
        Returns:
            list[tuple[str, str]]: List of tuples containing:
                - filename (str)
                - matched content with context (str)
        """
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
                    file_matches = []
                    for i, line in enumerate(lines):
                        if search_re.search(line):
                            # Get context lines
                            start = max(0, i - context_lines)
                            end = min(len(lines), i + context_lines + 1)
                            context = ''.join(lines[start:end])
                            file_matches.append(context)
                    
                    if file_matches:
                        results.append((filepath, file_matches))
            except Exception as e:
                print(f"Error searching {filepath}: {e}")

        results.sort(key=lambda x: x[0])  # Sort by filename
        return results

def main() -> None:
    """Command line interface for the text search engine.
    
    Allows interactive searching through text files in a directory.
    Handles building and loading search indexes.
    """
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
