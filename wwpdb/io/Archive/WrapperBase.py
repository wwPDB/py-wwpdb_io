##
# File: WrapperBase.py
# Date: 12-Dec-2016
#
##
"""
Base class implementing a function/method wrapper with abstract pre- and post- operation methods.

"""
import sys
import wrapt
import time
import abc
import inspect
import logging

ENABLED = True


class WrapperBase(object):
    def __init__(self, *dArgs, **dKw):
        """
        Base class implementation of function/method wrapper (decorator).

        Abstract methods are provided to be run before and after the wrapped method or function.

        The subclass must also impliment a callable method such as the following -

        @wrapt.decorator(enabled=ENABLED)
        def __call__(self, wrapped, instance, args, kwargs):
            return super(SubClassName, self)._callable(wrapped, instance, args, kwargs)


        :param string stderr: (Optional) redefinition of sys.stderr file handle
        :param string stdout: (Optional) redefinition of sys.stdout file handle
        :param string logname: (Optional) logging unit name.
        :param string loglevel: (Optional) logging level.

        """
        self.dArgs = dArgs
        self.dKw = dKw
        self.__stderr = sys.stderr
        self.__stdout = sys.stdout
        #
        sys.stderr = dKw.get("stderr", sys.stderr)
        sys.stdout = dKw.get("stdout", sys.stdout)
        #
        logName = dKw.get("logname", None)
        if logName:
            self._log = logging.getLogger(logName)
        else:
            self._log = logging.getLogger()
        #
        logLevel = dKw.get("loglevel", logging.ERROR)
        self._log.setLevel(logLevel)
        #

    @abc.abstractmethod
    def preOperation(self, *args, **kwargs):
        return

    @abc.abstractmethod
    def postOperation(self, *args, **kwargs):
        return

    def __getInfo(self, wrapped, instance):
        fName = ""
        cName = ""
        try:
            if instance is None:
                if inspect.isclass(wrapped):
                    # Decorator was applied to a class.
                    cName = wrapped.__class__.__name__
                    fName = ""
                else:
                    # Decorator was applied to a function or staticmethod.
                    cName = ""
                    fName = wrapped.__name__
            else:
                if inspect.isclass(instance):
                    # Decorator was applied to a classmethod.
                    cName = instance.__class__.__name__
                    fName = wrapped.__name__
                else:
                    # Decorator was applied to an instance method.
                    cName = instance.__class__.__name__
                    fName = wrapped.__name__
        except:
            self._log.execption("Unable to determine class/method or function details")

        return fName, cName

    def _callable(self, wrapped, instance, args, kwargs):
        fName, cName = self.__getInfo(wrapped, instance)
        try:
            self._log.debug("Invoking pre-operation method for %s %s" % (fName, cName))
            self.preOperation()
        except:
            self._log.execption("Pre-operation method failing")

        try:
            startTime = time.time()
            msg = "Starting %s.%s %s at %s\n" % (cName, fName, sys._getframe().f_code.co_name, time.strftime("%Y %m %d %H:%M:%S", time.localtime()))
            self._log.info(msg)
            self.preOperation(*args, **kwargs)
            return wrapped(*args, **kwargs)
        finally:
            endTime = time.time()
            msg = "Completed %s.%s %s at %s (%.4f seconds)\n" % (
                cName,
                fName,
                sys._getframe().f_code.co_name,
                time.strftime("%Y %m %d %H:%M:%S", time.localtime()),
                endTime - startTime,
            )
            self._log.info(msg)
            try:
                self._log.debug("Invoking post-operation method for %s %s" % (fName, cName))
                self.postOperation(*args, **kwargs)
            except:
                self._log.execption("Post-operation method failing")
            sys.stderr = self.__stderr
            sys.stdout = self.__stdout


class WrapperExample(WrapperBase):
    def __init__(self, *dArgs, **dKw):
        super(WrapperExample, self).__init__(*dArgs, **dKw)

    def preOperation(self, *args, **kwargs):
        self._log.info("Inside pre-operation method")
        return True

    def postOperation(self, *args, **kwargs):
        self._log.info("Inside post-operation method")
        return True

    @wrapt.decorator(enabled=ENABLED)
    def __call__(self, wrapped, instance, args, kwargs):
        return super(WrapperExample, self)._callable(wrapped, instance, args, kwargs)
