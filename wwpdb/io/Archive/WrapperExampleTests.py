##
# File: WrapperExampleTests.py
# Date: 12-Dec-2016  Jdw --
#
# Selected examples of decorators implimenting the WrapperBase.py
##
from WrapperBase import WrapperExample

import sys
import time
import traceback
import unittest
import logging

logging.basicConfig(level=logging.DEBUG, format='\n[%(levelname)s]-%(module)s.%(funcName)s: %(message)s')
logging.getLogger('wrapper')


@WrapperExample("hello", "world", 42, logname="wrapper", loglevel=logging.DEBUG)
def sayHello3(*args, **kw):
    print 'sayHello arguments:', args, kw
    time.sleep(2.2)


class MyClass(object):
    'Simple class.'

    def __init__(self, id):
        self.id = id

    def __str__(self):
        return str(self.id)

    def __repr__(self):
        return 'MyClass'

    @WrapperExample("hello", "world", 42, logname="wrapper", loglevel=logging.DEBUG)
    def mymethod(self, *args, **kwargs):
        'Simple method using decorator with arguments.'
        print "Method arguments ", args, kwargs
        time.sleep(3)
        return args, kwargs
        #


class ExampleUnitTests(unittest.TestCase):

    def setUp(self):
        self.__lfh = sys.stdout
        self.__verbose = True
        self.__debug = True
        #

    def tearDown(self):
        pass

    @WrapperExample("hello", "world", 42, logname="wrapper", loglevel=logging.DEBUG)
    def testExample1(self, my="aaa", me="bbbb"):
        """Test case -  create search index from persistent store

        """
        startTime = time.time()
        self.__lfh.write("\nStarting %s %s at %s\n" % (self.__class__.__name__,
                                                       sys._getframe().f_code.co_name,
                                                       time.strftime("%Y %m %d %H:%M:%S", time.localtime())))
        try:
            print "INSIDE TEST EXAMPLE 1", my, me
            time.sleep(1)
        except:
            traceback.print_exc(file=self.__lfh)
            self.fail()

        endTime = time.time()
        self.__lfh.write("\nCompleted %s %s at %s (%d seconds)\n" % (self.__class__.__name__,
                                                                     sys._getframe().f_code.co_name,
                                                                     time.strftime("%Y %m %d %H:%M:%S", time.localtime()),
                                                                     endTime - startTime))

    @WrapperExample("hello", "world", 42, logname="wrapper", loglevel=logging.DEBUG)
    def testExample2(self, my="aaaaa", me="bbbbb"):
        """Test case -  create search index from persistent store

        """
        startTime = time.time()
        self.__lfh.write("\nStarting %s %s at %s\n" % (self.__class__.__name__,
                                                       sys._getframe().f_code.co_name,
                                                       time.strftime("%Y %m %d %H:%M:%S", time.localtime())))
        try:
            print "INSIDE TEST EXAMPLE 2", my, me
            time.sleep(1)
        except:
            traceback.print_exc(file=self.__lfh)
            self.fail()

        endTime = time.time()
        self.__lfh.write("\nCompleted %s %s at %s (%d seconds)\n" % (self.__class__.__name__,
                                                                     sys._getframe().f_code.co_name,
                                                                     time.strftime("%Y %m %d %H:%M:%S", time.localtime()),
                                                                     endTime - startTime))


def suiteExamples():
    suiteSelect = unittest.TestSuite()
    suiteSelect.addTest(ExampleUnitTests("testExample1"))
    suiteSelect.addTest(ExampleUnitTests("testExample2"))
    return suiteSelect


#
sayHello3(1, 2, 3, my="aaaa")
#
my = MyClass(1)
print my.mymethod(1, 2, 3, my="aaaa")
print my.mymethod(3, 4, 5, my="aaaa", me="bbbbbbbb")


mySuite1 = suiteExamples()
unittest.TextTestRunner(verbosity=2).run(mySuite1)
