from test import *
from cli import *
import unittest

class CLITest(unittest.TestCase):

    def test_it_should_configure_all_options(self):
        cli = CLI()
        parser = cli.get_parser()
        
        self.assertTrue(parser.has_option("-h"))
        self.assertTrue(parser.has_option("--help"))
        
        self.assertTrue(parser.has_option("-c"))
        self.assertTrue(parser.has_option("--config"))
        
        self.assertTrue(parser.has_option("-d"))
        self.assertTrue(parser.has_option("--dir"))
        
        self.assertTrue(parser.has_option("-v"))
        self.assertTrue(parser.has_option("--version"))
        
        self.assertTrue(parser.has_option("--showsql"))
        
        self.assertTrue(parser.has_option("--create"))
        
    def test_it_should_show_error_message_and_exit(self):
        cli = CLI()
        try:
            cli.error_and_exit("test message")
            self.fail("it should not get here")
        except:
            pass

    def test_it_should_show_info_message_and_exit(self):
        cli = CLI()
        try:
            cli.info_and_exit("test message")
            self.fail("it should not get here")
        except:
            pass

if __name__ == "__main__":
    unittest.main()