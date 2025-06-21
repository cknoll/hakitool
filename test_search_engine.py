import unittest
import os
import tempfile
from search_engine import TextFileIndexer

class TestTextFileIndexer(unittest.TestCase):
    def setUp(self):
        """Set up a temporary directory with test files"""
        self.test_dir = tempfile.mkdtemp()
        # Create test files
        self.file1 = os.path.join(self.test_dir, "test1.txt")
        self.file2 = os.path.join(self.test_dir, "test2.txt")
        
        with open(self.file1, 'w') as f:
            f.write("""This is test file one.
It contains the word apple.
And also the word banana.
Plus some other words.""")

        with open(self.file2, 'w') as f:
            f.write("""This is test file two.
It has a banana.
And some different words.""")

        self.indexer = TextFileIndexer(self.test_dir)
        self.indexer.build_index()

    def tearDown(self):
        """Clean up the temporary directory"""
        for f in [self.file1, self.file2]:
            if os.path.exists(f):
                os.remove(f)
        os.rmdir(self.test_dir)
        if os.path.exists("file_index.pkl"):
            os.remove("file_index.pkl")

    def test_search_in_files_with_match(self):
        """Test finding matching terms"""
        # Test exact match
        results = self.indexer.search_in_files("banana")
        self.assertEqual(len(results), 2)  # Should find in both files
        
        # Check each result has filename and list of contexts
        for filename, contexts in results:
            self.assertTrue(isinstance(contexts, list))
            self.assertTrue(len(contexts) >= 1)
            self.assertTrue(any("banana" in ctx.lower() for ctx in contexts))

    def test_search_in_files_no_match(self):
        """Test searching for non-existent term"""
        results = self.indexer.search_in_files("nonexistentword") 
        self.assertEqual(len(results), 0)

    def test_search_in_files_case_insensitive(self):
        """Test that search is case insensitive"""
        results = self.indexer.search_in_files("BANANA")
        self.assertEqual(len(results), 2)
        for _, contexts in results:
            self.assertTrue(any("banana" in ctx.lower() for ctx in contexts))

    def test_result_structure(self):
        """Test that results have correct structure (filename, list of contexts)"""
        results = self.indexer.search_in_files("apple")
        self.assertEqual(len(results), 1)  # Only in file1
        filename, contexts = results[0]
        self.assertEqual(filename, self.file1)
        self.assertTrue(isinstance(contexts, list))
        self.assertTrue(all(isinstance(ctx, str) for ctx in contexts))

if __name__ == '__main__':
    unittest.main()
