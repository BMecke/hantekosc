import threading
import numpy as np


class Channel:
    """
    Class for an oscilloscope channel.

    Attributes:
        id (str): The channel id.
        ch_number (int): The channel number. Starts with 0.
        osc: The device that owns the channel.


    """
    def __init__(self, osc, channel_number):
        """
        Class constructor.

        Args:
            osc: The device that owns the channel.
            channel_number: The number of the channel.
        """
        self._trigger_kind = 'RISING'
        self._trigger_level = 1

        self.data_mutex = threading.Lock()

        self.voltage_index = 1
        self.id = 'CH' + str(channel_number + 1)
        self.ch_number = channel_number
        self.osc = osc
        self.retrieved_data = np.empty((2, 1), float)
        self.new_data_ready = False
        self.voltage_range = 5

        # ToDo: Add "enabled" variable to improve performance by calculating data only for enabled channels
        # ToDo: Add "probe gain" and "probe offset" variables

    @property
    def measured_data(self):
        """
        Get the measurement data of the x and y coordinates in seconds and volts.

        Returns:
            numpy.array: The measurement data of the x and y coordinates in seconds and volts.
        """
        self.data_mutex.acquire()
        data = np.array(self.retrieved_data, copy=True)
        self.new_data_ready = False
        self.data_mutex.release()
        return data

    @property
    def voltage_ranges_available(self):
        """
        Get available voltage ranges

        Returns:
            list: The available voltage ranges as list.
        """
        return [0.5, 1, 2.5, 5]

    @property
    def voltage_range(self):
        """
        Get the voltage range.

        Returns:
            int: The voltage range.
        """
        return self._voltage_range

    @voltage_range.setter
    def voltage_range(self, voltage_range):
        """
        Set the voltage range.

        Args:
            voltage_range (int): The voltage range.
        """
        self.osc.settings_mutex.acquire()

        was_running = False
        if self.osc.running:
            self.osc.stop()
            was_running = True

        # ToDo: raise value modified error?
        match voltage_range:
            case num if num < 0.75:
                index = 10
            case num if 0.75 <= num < 1.75:
                index = 5
            case num if 1.75 <= num < 3.75:
                index = 2
            case num if 3.75 <= num:
                index = 1
            case _:
                index = 1

        if self.id == 'CH1':
            pass
            self.osc.scope.set_ch1_voltage_range(index)
        elif self.id == 'CH2':
            pass
            self.osc.scope.set_ch2_voltage_range(index)
        self._voltage_range = 5/index
        self.voltage_index = index

        # device must be started and stopped for some reason (Otherwise an SIGSEGV error is thrown)
        if was_running:
            self.osc.start()

        self.osc.settings_mutex.release()

    @property
    def trigger_kinds_available(self):
        """
        Get available trigger kinds

        Returns:
            list: The available trigger kinds as list.
        """
        return ['RISING', 'FALLING']

    @property
    def trigger_kind(self):
        """
        Get the trigger kind ('RISING', 'FALLING').

        Returns:
            str: The trigger kind.

        """
        return self._trigger_kind

    @trigger_kind.setter
    def trigger_kind(self, trigger_kind):
        """
        Set the trigger kind ('RISING', 'FALLING').

        Args:
            trigger_kind (str):  The trigger kind.
        """
        self.osc.settings_mutex.acquire()
        self._trigger_kind = trigger_kind
        self.osc.settings_mutex.release()

    @property
    def trigger_level(self):
        """
        Get the trigger level.

        Returns:
            float: The trigger level.
        """
        return self._trigger_level

    @trigger_level.setter
    def trigger_level(self, trigger_level):
        """
        Set the trigger level
        Args:
            trigger_level (float): The trigger level.
        """
        self.osc.settings_mutex.acquire()
        self._trigger_level = trigger_level
        self.osc.settings_mutex.release()
