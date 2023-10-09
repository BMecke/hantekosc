#ifndef TRIGGERING_H
#define TRIGGERING_H

#include <stdio.h>
#include <stdlib.h>

#define BLOCKSIZE = 10;

int find_trigger_position(double *data_array, int length, double threshold, int rising_edge);

double* create_timing_data(double *data_array, int number_of_points, int sample_rate);
double* create_pretrigger_timing_data(double *data_array, int number_of_points, int sample_rate);
double* create_voltage_data(double *data_array, int length, double scale_factor, double offset);

#endif // TRIGGERING_H
