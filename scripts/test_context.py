import sys
import os
import unittest
import tempfile
import shutil

# Add parent directory to path to import app
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.context import ContextIngestor

class TestContextIngestor(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        
    def tearDown(self):
        shutil.rmtree(self.test_dir)
        
    def test_parse_requirements(self):
        req_path = os.path.join(self.test_dir, "requirements.txt")
        with open(req_path, "w") as f:
            f.write("flask==2.0.1\nrequests>=2.25.1\nnumpy\n")
            
        ingestor = ContextIngestor()
        items = ingestor.ingest_directory(self.test_dir)
        
        python_item = next((i for i in items if i["source"] == "requirements.txt"), None)
        self.assertIsNotNone(python_item)
        self.assertEqual(python_item["dependencies"]["flask"], "==2.0.1")
        self.assertEqual(python_item["dependencies"]["requests"], ">=2.25.1")
        
    def test_parse_package_json(self):
        pkg_path = os.path.join(self.test_dir, "package.json")
        with open(pkg_path, "w") as f:
            f.write('{"dependencies": {"react": "^17.0.2"}, "devDependencies": {"jest": "^27.0.0"}}')
            
        ingestor = ContextIngestor()
        items = ingestor.ingest_directory(self.test_dir)
        
        node_item = next((i for i in items if i["source"] == "package.json"), None)
        self.assertIsNotNone(node_item)
        self.assertEqual(node_item["dependencies"]["react"], "^17.0.2")
        self.assertEqual(node_item["dependencies"]["jest"], "^27.0.0")

if __name__ == "__main__":
    unittest.main()
