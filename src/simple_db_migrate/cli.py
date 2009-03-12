from optparse import OptionParser
import sys

class CLI(object):

    def __init__(self):
        self.__config_parser()

    def __config_parser(self):
        self.__parser = OptionParser()

        self.__parser.add_option("-v", "--version", 
                dest="schema_version", 
                default=None, 
                help="Schema version to migrate to. If not provided will migrate to the last version available.")
                
        self.__parser.add_option("-c", "--config", 
                dest="db_config_file", 
                default="simple-db-migrate.conf", 
                help="Use specific config file. If not provided, will use simple-db-migrate.conf that is located in the current directory.")
                
        self.__parser.add_option("-d", "--dir", 
                dest="migrations_dir", 
                default=".", 
                help="Find migration files in a specific directory. If not provided will search for files in the current directory.")
                
        self.__parser.add_option("--showsql", 
                action="store_true", 
                dest="show_sql", 
                default=False, 
                help="Show all SQL statements executed.")

        self.__parser.add_option("--create", 
                dest="create_migration", 
                default=None, 
                help="Create migration file with given nickname.")

    def get_parser(self):
        return self.__parser

    def parse(self):
        return self.__parser.parse_args()
        
    def error_and_exit(self, msg):
        print "[ERROR] %s\n" % (msg)
        sys.exit(1)
        
    def info_and_exit(self, msg):
        print "%s\n" % (msg)
        sys.exit(0)
        
    def msg(self, msg):
        print msg