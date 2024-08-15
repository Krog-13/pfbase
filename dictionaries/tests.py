import unittest

from django.test import TestCase

# Create your tests here.
from dictionaries.models import ABCDictionary


class ABCDictionaryTestCase(TestCase):
    def setUp(self):
        ABCDictionary.objects.create(
            naming={"full_name": "Тестовый справочник", "short_name": "Тест"},
            description="Тестовое описание",
            abc_code="TST",
            author_id=1
        )

    def test_abc_dictionary_str(self):
        abc_dictionary = ABCDictionary.objects.get(abc_code="TST")
        self.assertEqual(abc_dictionary.__str__(), "Тест")

    def test_abc_dictionary_naming(self):
        abc_dictionary = ABCDictionary.objects.get(abc_code="TST")
        self.assertEqual(abc_dictionary.naming, {"full_name": "Тестовый справочник", "short_name": "Тест"})





if __name__ == '__main__':
    unittest.main()