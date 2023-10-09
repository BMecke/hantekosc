import threading
import time
import numpy as np
from hantekosc.py_ht6022 import LibUsbScope

from threading import Thread
from queue import Queue

from hantekosc.c_code import C_Code

from hantekosc.channel import Channel


class Oscilloscope:
    """
    Interface for hantek usb oscilloscopes.

    Attributes:
        c_code (C_Code): This object is used to call functions programmed in C language.
        scope (Oscilloscope): A oscilloscope object from Hantek6022API (https://github.com/Ho-Ro/Hantek6022API).
        running (bool): Indicates whether the device is currently running.
        channels (list): A list containing objects for each channel of the device.
        settings_mutex (threading.lock): A mutex ensuring that only one setting can be made at a time.
    """

    def __init__(self, serial_number=None):
        """
        Class constructor. Open the connection to the instrument using the Hantek6022API
        (https://github.com/Ho-Ro/Hantek6022API).
        """
        # ToDo: initialize device with serial number
        self.running = False

        self.c_code = C_Code()

        self.scope = LibUsbScope.Oscilloscope()
        # connect to device
        if not self.scope.setup() or not self.scope.open_handle():
            raise RuntimeError("Could not find any hantek devices")

        # upload correct firmware into device's RAM
        if not self.scope.is_device_firmware_present:
            self.scope.flash_firmware() #firmware=PyHT6022.Firmware.mod_firmware_01)
        self.scope.set_num_channels(2)

        self._blockslope = 0.00000207

        # event to stop async data reading thread
        self._shutdown_event = None
        # calculated when setting presample ratio
        self._number_of_presample_points = 0
        # Size of a block read from the device via USB (calculated when setting sample rate)
        self._blocksize = 0
        self._record_length = 0
        self._sample_rate = 0
        self._sample_id = 0
        self._pre_sample_ratio = 0
        self._trigger_mode = ''
        self._selected_channel = 0

        self._raw_data = Queue(maxsize=50)
        self._previous_voltage_data = [np.zeros(self._record_length), np.zeros(self._record_length)]

        self.settings_mutex = threading.Lock()

        # initial oscilloscope settings
        self.sample_rate = 20 * 1e3
        self.record_length = 5000
        self.pre_sample_ratio = 0.5
        self.trigger_mode = 'REPEAT'  # SINGLE, AUTO, REPEAT
        self.selected_channel = 0
        self.channels = [Channel(self, 0), Channel(self, 1)]

    def __del__(self):
        """
        Class destructor. Stop the device when the program is closed.
        """
        if self.running:
            self.stop()
            self.scope.close_handle()

    def retrieve_callback(self, ch1_data, ch2_data):
        """
        This callback is called whenever new measurement data is available.
        The data is then putted into a queue to be processed in another thread.

        Args:
            ch1_data (list): Measurement data of the first channel.
            ch2_data (list): Measurement data of the second channel.
        """
        # append data to queue
        if len(ch1_data) == self._blocksize and len(ch2_data) == self._blocksize:
            self._raw_data.put((ch1_data, ch2_data))

    def retrieve(self):
        """
        Here data is permanently requested in a separate thread as long as the device is running.
        """
        while self.running:
            self.scope.poll()

    def start(self):
        """
        Start the measurement.
        """
        self._previous_voltage_data = [np.zeros(self._record_length), np.zeros(self._record_length)]
        self.running = True

        process_data_thread = Thread(target=self._process_data)
        process_data_thread.start()

        self.scope.start_capture()
        self._shutdown_event = self.scope.read_async(self.retrieve_callback, 2 * self._blocksize,
                                                     outstanding_transfers=10)

        retriever_thread = Thread(target=self.retrieve)
        retriever_thread.start()

    def stop(self):
        """
        Stop the measurement.
        """
        self.running = False
        self._shutdown_event.set()
        time.sleep(1)
        self._raw_data.queue.clear()

    def _process_data(self):
        """
        Here the measurement data are processed in a separate thread.
        An array with the time units and an array with the measurement data starting from the trigger point are created.
        In addition, an array is created in which the measurement data is stored that is temporally located before the
        trigger.
        This function is time critical. If the function takes too long, the queue fills up and measurement data is lost.
        """
        while self.running:
            # Although this function is time-critical, a short time can be waited to avoid overloading the processor.
            # This time might depend on the hardware of the user device.
            time.sleep(0.01)
            self.settings_mutex.acquire()
            loop_is_to_slow = False
            if self.running:
                voltage_data = self._get_voltage_data_block()
                if self.trigger_mode == 'SINGLE' or self.trigger_mode == 'REPEAT':
                    trigger_position = self._find_trigger_position(voltage_data)
                    end_position = self.record_length - self._number_of_presample_points
                    # system triggered
                    if trigger_position >= 0:
                        # add points before trigger event to _previous_raw_data array
                        for i in range(self.number_of_channels):
                            prev_data = self._previous_voltage_data[i]
                            prev_data = np.hstack((prev_data, voltage_data[i][:trigger_position]))
                            self._previous_voltage_data[i] = prev_data[len(prev_data) - self.record_length:]
                            voltage_data[i] = voltage_data[i][trigger_position:]
                        # More data is needed than available in one block --> More blocks must be loaded
                        if trigger_position + end_position > self._blocksize:
                            # Points that do not fit into the first block
                            remaining_points = ((self.record_length - self._number_of_presample_points) -
                                                (self._blocksize - trigger_position))
                            # Number of blocks that still need to be loaded
                            number_of_blocks = int(np.ceil(remaining_points / self._blocksize))
                            # get needed blocks
                            for i in range(number_of_blocks):
                                voltage_data_block = self._get_voltage_data_block()
                                for j in range(self.number_of_channels):
                                    voltage_data[j] = np.hstack((voltage_data[j], voltage_data_block[j]))

                    # Calculate the array with the timing points
                    presample_timing_data = self._create_presample_timing_data(self._number_of_presample_points)
                    timing_data_ = self._create_timing_data(self.record_length - self._number_of_presample_points)
                    timing_data = np.hstack((presample_timing_data, timing_data_))

                    # Merge the array containing the measurement data from pre-trigger data
                    # and the data starting from the trigger event
                    for i in range(self.number_of_channels):
                        previous_data_start_pos = len(self._previous_voltage_data[i]) - self._number_of_presample_points
                        voltage_data[i] = np.hstack(
                            (self._previous_voltage_data[i][previous_data_start_pos:], voltage_data[i]))
                        if trigger_position >= 0:
                            self.channels[i].retrieved_data = np.vstack(
                                (timing_data, voltage_data[i][:self.record_length]))
                        self._previous_voltage_data[i] = voltage_data[i]
                        self._previous_voltage_data[i] = self._previous_voltage_data[i][
                                                         len(self._previous_voltage_data[i]) - self.record_length:]
                        self.channels[i].new_data_ready = True
                    # If the trigger mode is "SINGLE", stop after a trigger event
                    if self.trigger_mode == 'SINGLE' and trigger_position >= 0:
                        self.stop()
                # No trigger, just get data blocks
                else:
                    timing_data = self._create_timing_data(self.record_length)
                    # More data is needed than available in one block --> More blocks must be loaded
                    if self.record_length > self._blocksize:
                        number_of_blocks = int(np.ceil((self.record_length - self._blocksize) / self._blocksize))
                        for i in range(number_of_blocks):
                            voltage_data_block = self._get_voltage_data_block()
                            for j in range(self.number_of_channels):
                                voltage_data[j] = np.hstack((voltage_data[j], voltage_data_block[j]))

                    for i in range(self.number_of_channels):
                        self.channels[i].data_mutex.acquire()
                        self.channels[i].retrieved_data = np.vstack((timing_data, voltage_data[i][:self.record_length]))
                        self.channels[i].new_data_ready = True
                        self.channels[i].data_mutex.release()

                # clear queue if the program is too slow
                if self._raw_data.qsize() > 48:
                    print('Data processing is too slow.')
                    for i in range(48):
                        self._raw_data.get()
                    loop_is_to_slow = True

            self.settings_mutex.release()
            if loop_is_to_slow:
                self.pre_sample_ratio = 0

    def _find_trigger_position(self, voltage_data):
        """
        Get the array position at which the trigger level value is exceeded.

        Args:
            voltage_data (list): The array containing the measurement data for both channels.
        Returns:
            The array position of the selected channel where the trigger level value is hit or crossed.
        """

        # find rising or falling edge
        # https://stackoverflow.com/questions/50365310/python-rising-falling-edge-oscilloscope-like-trigger
        selected_channel = self.channels[self.selected_channel]

        if self.c_code.c_code_loaded:
            trigger_pos = self.c_code.find_trigger_position(voltage_data[self.selected_channel],
                                                            selected_channel.trigger_level,
                                                            selected_channel.trigger_kind)
            return trigger_pos
        else:
            # find rising or falling edge
            # https://stackoverflow.com/questions/50365310/python-rising-falling-edge-oscilloscope-like-trigger
            thresholded_array = np.where(voltage_data[self.selected_channel] > selected_channel.trigger_level, 1, -1)
            convolution_array = [1, -1]
            convolution = np.convolve(thresholded_array, convolution_array, mode='same')
            if self.channels[self.selected_channel].trigger_kind == 'RISING':
                argmax = np.argmax(convolution)
                if convolution[argmax] == len(convolution_array):
                    trigger_pos = argmax
                else:
                    trigger_pos = -1
            else:
                argmin = np.argmin(convolution)
                if convolution[argmin] == -1 * len(convolution_array):
                    trigger_pos = argmin
                else:
                    trigger_pos = -1
            return trigger_pos

    def _get_voltage_data_block(self):
        """
        Here a data block is fetched from the queue and the measurement data is converted into volts.

        Returns:
            list: The measurement data in volts.
        """
        raw_data = self._raw_data.get()
        voltage_data = []
        for i in range(self.number_of_channels):
            voltage_data.append(np.array(self._create_voltage_data(raw_data[i], self.channels[i].voltage_index,
                                self.selected_channel)))
        return voltage_data

    def _create_voltage_data(self, raw_data, voltage_range=1, channel=0, probe=1, offset=0):
        """
        Convenience function for converting data read from the scope to nicely scaled voltages.
        Apply the calibration values that are stored in EEPROM (call "get_calibration_values()" before)

        Args:
            raw_data (list): The list of points returned from the read_data functions.
            voltage_range (int): The voltage range current set for the channel.
            channel (int): The voltage range current set for the channel. 0 = CH1, 1 = CH2.
            probe (int): An additonal multiplictive factor for changing the probe gain.
            offset (float): An additional additive value to compensate the ADC offset

        Returns:
            numpy.array: A list of correctly scaled voltages for the data.
        """
        if channel == 0:
                mul = probe * self.scope.gain1[voltage_range]
                off = offset + self.scope.offset1[voltage_range]
        else:
                mul = probe * self.scope.gain2[voltage_range]
                off = offset + self.scope.offset2[voltage_range]

        scale_factor = (5.12 * mul) / (voltage_range << 7)

        if self.c_code.c_code_loaded:
            return self.c_code.create_voltage_data(raw_data, scale_factor, off)
        else:
            data = np.array(raw_data, dtype=float)
            data = (data - 128 - off) * scale_factor
            return data

    def _create_timing_data(self, num_points):
        """
        Convenience method for creating a list of times from the read data.

        Args:
            num_points (int): The number of measured points.

        Returns:
            numpy.array: The timing data.
        """
        if self.c_code.c_code_loaded:
            timing_data = self.c_code.create_timing_data(num_points, self.sample_rate)
            return timing_data
        else:
            timing_data, _ = self.scope.convert_sampling_rate_to_measurement_times(num_points, self._sample_id)
            return np.array(timing_data)

    def _create_presample_timing_data(self, num_points):
        """
        Convenience method for creating a list of pre-trigger times from the read data.

        Args:
            num_points (int): The number of measured points.

        Returns:
            numpy.array: The timing data.
        """
        if num_points > 0:
            if self.c_code.c_code_loaded:
                return self.c_code.create_pretrigger_timing_data(num_points, self.sample_rate)
            else:
                timing_data = np.arange(-num_points, 0)
                timing_data = (timing_data / self.sample_rate)
                return timing_data
        else:
            return np.array([])

    @property
    def max_sample_rate(self):
        """
        Get the maximum sample rate in Hz.

        Returns:
            int: The maximum sample rate in Hz.
        """
        return 48 * 1e6

    @property
    def sample_rate(self):
        """
        Get the current sample rate in Hz.

        Returns:
            float: The sample rate in Hz.
        """
        return self._sample_rate

    @sample_rate.setter
    def sample_rate(self, sample_rate):
        """
        Set the current sample rate in Hz.

        Args:
            sample_rate(int): The sample rate in Hz.
        """
        self.settings_mutex.acquire()
        was_running = False
        if self.running:
            self.stop()
            was_running = True
        # ToDo: rase value modified error?
        match sample_rate:
            case num if num in range(0, 30000):
                sample_id = 102
            case num if num in range(30000, 45000):
                sample_id = 104
            case num if num in range(45000, 57000):
                sample_id = 105
            case num if num in range(57000, 82000):
                sample_id = 106
            case num if num in range(82000, 150000):
                sample_id = 110
            case num if num in range(150000, 300000):
                sample_id = 120
            case num if num in range(300000, 450000):
                sample_id = 140
            case num if num in range(450000, 750000):
                sample_id = 150
            case num if num in range(750000, 1500000):
                sample_id = 1
            case num if num in range(1500000, 2500000):
                sample_id = 2
            case num if num in range(2500000, 3500000):
                sample_id = 3
            case num if num in range(3500000, 4500000):
                sample_id = 4
            case num if num in range(3500000, 4500000):
                sample_id = 4
            case num if num in range(4500000, 5500000):
                sample_id = 5
            case num if num in range(5500000, 6500000):
                sample_id = 6
            case num if num in range(6500000, 9500000):
                sample_id = 8
            case num if num in range(9500000, 11000000):
                sample_id = 10
            case num if num in range(11000000, 13500000):
                sample_id = 12
            case num if num in range(13500000, 15500000):
                sample_id = 15
            case num if num in range(15500000, 20000000):
                sample_id = 16
            case num if num in range(20000000, 27000000):
                sample_id = 24
            case num if num in range(27000000, 39000000):
                sample_id = 30
            case num if num > 39000000:
                sample_id = 48
            case _:
                # ToDo: raise error?
                sample_id = 0
        self.scope.set_sample_rate(sample_id)
        if sample_id >= 100:
            self._sample_rate = int((sample_id - 100) * 10e3)
        else:
            self._sample_rate = int(sample_id * 1000000)
        self._sample_id = sample_id

        self._blocksize = int(self._blockslope * self.sample_rate + 1) * (6 * 1024)  # (should be divisible by 6*1024)

        if was_running:
            self.start()
        self.settings_mutex.release()

    @property
    def number_of_channels(self):
        """
        Get the number of available channels.

        Returns:
            int: The number of channels.
        """
        return len(self.channels)

    @property
    def pre_sample_ratio(self):
        """
        Get the pre sample ratio.

        The pre sample ratio is a float between 0 and 1 and defines how many
        samples should be recorded before the trigger point.

        Returns:
            float: The pre sample ratio.

        """
        return self._pre_sample_ratio

    @pre_sample_ratio.setter
    def pre_sample_ratio(self, ratio):
        """
        Set the pre sample ratio.

        The pre sample ratio is a float between 0 and 1 and defines how many
        samples should be recorded before the trigger point.

        Args:
            ratio (float): The pre sample ratio.

        """
        self.settings_mutex.acquire()
        self._pre_sample_ratio = ratio
        self._number_of_presample_points = int(self.record_length * self._pre_sample_ratio)
        self.settings_mutex.release()

    @property
    def max_record_length(self):
        """
        Get the maximum record length.

        Returns:
            int: The maximum record length.
        """
        return 100000

    @property
    def record_length(self):
        """
        Get the current record length (number of samples).

        Returns:
            int: The current record length.

        """
        return self._record_length

    @record_length.setter
    def record_length(self, record_length):
        """
        Set the current record length (number of samples).

        Args:
            record_length (int): The current record length.
        """
        self.settings_mutex.acquire()
        self._record_length = record_length
        self._number_of_presample_points = int(record_length * self._pre_sample_ratio)
        self._previous_voltage_data = [np.zeros(record_length), np.zeros(record_length)]
        self.settings_mutex.release()

    @property
    def trigger_modes_available(self):
        """
        Get available trigger modes

        Returns:
            list: The available trigger modes as list.
        """
        return ['SINGLE', 'REPEAT', 'NONE']

    @property
    def trigger_mode(self):
        """
        Get the current trigger mode ('SINGLE', 'REPEAT' or 'NONE')

        Returns:
            str: The current trigger mode.
        """
        return self._trigger_mode

    @trigger_mode.setter
    def trigger_mode(self, trigger_mode):
        """
        Set the current trigger mode ('SINGLE', 'REPEAT' or 'NONE')

        Args:
            trigger_mode (str): The current trigger mode.

        """
        self.settings_mutex.acquire()
        self._trigger_mode = trigger_mode
        self.settings_mutex.release()

    @property
    def selected_channel(self):
        """
        Get the number of the selected channel.

        Returns:
            int: The number of the selected channel.
        """
        return self._selected_channel

    @selected_channel.setter
    def selected_channel(self, selected_channel):
        """
        Set the number of the selected channel.

        Args:
            selected_channel (int): The number of the selected channel.

        """
        self.settings_mutex.acquire()
        self._selected_channel = selected_channel
        self.settings_mutex.release()
