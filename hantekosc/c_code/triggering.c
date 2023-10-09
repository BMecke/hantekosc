#include "triggering.h"

/**
 * @brief Find the first value equal or above/below a specified threshold
 * @param data_array
 * @param length
 * @param threshold
 * @param rising_edge
 * @param number_of_values_before_and_after_threshold
 * @return
 */
int find_trigger_position(double *data_array, int length, double threshold, int rising_edge){
    if(length < 1){
        return -1;
    }
    for(int i=1; i<length; i++){
        if(rising_edge){
            if(data_array[i-1] < threshold && data_array[i] >= threshold){
                return i;
            }
        }
        else{
            if(data_array[i-1] > threshold && data_array[i] <= threshold){
                return i;
            }
        }


    }
    return -1;
}


double* create_timing_data(double *data_array, int number_of_points, int sample_rate){
    for(int i=0; i<number_of_points; i++){
        data_array[i] = (float) i/sample_rate;
    }
    return data_array;
}

double* create_pretrigger_timing_data(double *data_array, int number_of_points, int sample_rate){
    int i=0;
    for(int j=-number_of_points; j<0; j++){
        data_array[i] = (float) j/sample_rate;
        i++;
    }
    return data_array;
}


double* create_voltage_data(double *data_array, int length, double scale_factor, double offset){
    for(int i=0; i<length; i++){
        data_array[i] = (data_array[i]-128-offset)*scale_factor;
    }
    return data_array;
}

