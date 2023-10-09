import os
import sys
import time

import numpy
import numpy as np
from cffi import FFI


class C_Code:
    """
    This class contains all wrapper functions to call C code.

    Attributes:
        c_code_loaded (bool): Indicates whether the C code could be imported. If not, this class cannot be used.
        ffibuilder (FFI): A FFI instance.
    """

    def __init__(self):
        """
        Standard constructor. Here the C code is compiled and imported.
        """
        self.c_code_loaded = False
        self.ffibuilder = FFI()

        # Here the headers of all C-functions must be specified
        self.ffibuilder.cdef("int find_trigger_position(double *data_array, int length, double threshold, int rising_edge);")
        self.ffibuilder.cdef("double* create_timing_data(double *data_array, int number_of_points, int sample_rate);")
        self.ffibuilder.cdef("double* create_pretrigger_timing_data(double *data_array, int number_of_points, int sample_rate);")
        self.ffibuilder.cdef("double* create_voltage_data(double *data_array, int length, double scale_factor, double offset);")

        c_code_path = os.path.abspath(os.path.dirname(__file__))
        sys.path.insert(0, c_code_path)
        global find_trigger_position, create_timing_data, create_pretrigger_timing_data, \
            create_voltage_data

        # if the C code is compiled, import it. Otherwise, compile and import it.
        try:
            from _triggering.lib import find_trigger_position, create_timing_data, create_pretrigger_timing_data, \
                create_voltage_data
            self.c_code_loaded = True
        except ModuleNotFoundError:
            print("building C code")
            self.ffibuilder.set_source("_triggering",  # name of the output C extension
                                       """ #include "triggering.h" """,
                                       sources=['triggering.c'],  # includes pi.c as additional sources
                                       libraries=[], )  # on Unix, link with the math library
            self.ffibuilder.compile(c_code_path, verbose=False)
            from _triggering.lib import find_trigger_position, create_timing_data, create_pretrigger_timing_data, \
                create_voltage_data
            self.c_code_loaded = True

    def _create_c_array(self, data_array, dtype=float):
        if dtype == float:
            if not isinstance(data_array, numpy.ndarray):
                data_array = np.array(data_array)
            data_array = data_array.astype(float, order='C')
            c_array = self.ffibuilder.from_buffer('double *', data_array)
            return c_array

    def _create_np_array_from_c_array(self, c_array, length):
        return np.frombuffer(self.ffibuilder.buffer(c_array, length * 8), dtype=float)

    def find_trigger_position(self, data_array, threshold, trigger_kind='RISING'):
        """
        Get the array position at which a threshold value is exceeded.

        Args:
            data_array (numpy.array or list): The array containing the measurement data.
            threshold (float): The threshold value at which the trigger should fire.
            trigger_kind (str): The type of trigger (currently 'RISING' and 'FALLING' are supported).

        Returns:
            The array position where the threshold is hit or crossed.

        """
        if not self.c_code_loaded:
            raise ImportError('Could not load C code.')
        else:
            c_array = self._create_c_array(data_array)
            if trigger_kind == 'RISING':
                return find_trigger_position(c_array, len(data_array), threshold, 1)
            else:
                return find_trigger_position(c_array, len(data_array), threshold, 0)

    def create_voltage_data(self, raw_data, scale_factor, offset):
        """
        Convenience function for converting data read from the scope to nicely scaled voltages.

        Args:
            raw_data  (numpy.array or list): The list of points returned from the read_data functions.
            scale_factor (float): A calculated scale factor.
            offset (float): A calculated offset.

        Returns:
            numpy.array: The voltage data for the given raw data.
        """
        if not self.c_code_loaded:
            raise ImportError('Could not load C code.')
        else:
            c_array = self._create_c_array(raw_data)
            create_voltage_data(c_array, len(raw_data), scale_factor, offset)
            np_array = self._create_np_array_from_c_array(c_array, len(raw_data))
            return np_array

    def create_timing_data(self, num_points, sample_rate):
        """
        Convenience method for creating a list of times from the read data.

        Args:
            num_points (int): The number of measured points.
            sample_rate (int): the sample rate of the oscilloscope.

        Returns:
            numpy.array: The timing data.
        """
        if not self.c_code_loaded:
            raise ImportError('Could not load C code.')
        else:
            raw_data = np.zeros(num_points)
            c_array = self._create_c_array(raw_data)
            create_timing_data(c_array, len(raw_data), sample_rate)
            np_array = self._create_np_array_from_c_array(c_array, len(raw_data))
            return np_array

    def create_pretrigger_timing_data(self, num_points, sample_rate):
        """
        Convenience method for creating a list of pre-trigger times from the read data.

        Args:
            num_points (int): The number of measured points.
            sample_rate (int): the sample rate of the oscilloscope.

        Returns:
            numpy.array: The timing data.
        """
        if not self.c_code_loaded:
            raise ImportError('Could not load C code.')
        else:
            raw_data = np.zeros(num_points)
            c_array = self._create_c_array(raw_data)
            create_pretrigger_timing_data(c_array, len(raw_data), sample_rate)
            np_array = self._create_np_array_from_c_array(c_array, len(raw_data))
            return np_array