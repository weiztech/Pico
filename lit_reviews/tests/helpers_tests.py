import fitz
from django.test import TestCase
#from myapp.models import MyModel
from lit_reviews.helpers.articles import get_ai_search_texts
from unittest.mock import MagicMock, patch
import os

class HelpersTest(TestCase):
    # @classmethod
    # def setUpTestData(cls):
    #     # Data created here will be available to all test methods
    #
    #     #cls.my_model = MyModel.objects.create(name="Test")

    @classmethod
    def setUpClass(cls):
        super(HelpersTest, cls).setUpClass()  # Initialize parts of the testing framework
        # ... your setup logic ...
        print("opening test pdf file..")
        print("Current directory:", os.getcwd())
        os.environ['AI_API_URL'] = "http://citemed.ethandrower.com/extract_ft"
        cls.doc = fitz.open('test_files/test_ft.pdf')
        print("...done!")


    @classmethod
    def tearDownClass(cls):
        # ... your teardown logic ...
        cls.doc.close()  # Close the document

        super(HelpersTest, cls).tearDownClass()


    def test_method_with_api(self):
                # Mock a successful API response
        # Call the function with the mocked document object
        print("running get ai search texts function...")

        result = get_ai_search_texts(self.doc)

        self.assertEqual(result, [
                [
                    "#d5cad0",
                    "event-free survival from AF after three years"
                ],
                [
                    "#d5cad0",
                    "original draft preparation"
                ],
                [
                    "#d5cad0",
                    "."
                ],
                [
                    "#d5cad0",
                    "Written\ninformed consent was obtained from all participants"
                ]
        ])

            # Additional tests...


    @patch('lit_reviews.helpers.articles.requests.post')
    def test_method1(self, mock_post):
                # Mock a successful API response
        mock_post.return_value.status_code = 200
        mock_post.return_value.json.return_value = ["text1", "text2"]

                # Create a mock document with a get_text method
        mock_doc = self.doc
        #mock_doc.get_text.side_effect = ["page 1 text", "page 2 text"]

        # Call the function with the mocked document object
        result = get_ai_search_texts(mock_doc)
        print(str(result))

        self.assertEqual(result, ["text1", "text2"])

            # Additional tests...


