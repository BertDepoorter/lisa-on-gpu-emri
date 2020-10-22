import numpy as np
cimport numpy as np

from pointer_adjust import pointer_adjust

assert sizeof(int) == sizeof(np.int32_t)


cdef extern from "GeometricProjections.hh":
    ctypedef void* cmplx 'cmplx'
    void get_response(double *y_gw, double *k_in, double *u_in, double *v_in, double dt,
                  int num_delays, int *link_space_craft_0_in, int *link_space_craft_1_in,
                  cmplx *input_in, int num_inputs, int order,
                  double sampling_frequency, int buffer_integer, double *factorials_in,
                  int num_factorials, double input_start_time,
                  double *interp_array, int init_len, double* h_t);

@pointer_adjust
def get_response_wrap(y_gw, k_in, u_in, v_in, dt,
              num_delays, link_space_craft_0_in, link_space_craft_1_in,
              input_in, num_inputs, order, sampling_frequency, buffer_integer,
              factorials_in, num_factorials, input_start_time,
              interp_array, init_len, h_t):

    cdef size_t y_gw_in = y_gw
    cdef size_t k_in_in = k_in
    cdef size_t u_in_in = u_in
    cdef size_t v_in_in = v_in

    cdef size_t link_space_craft_0_in_in = link_space_craft_0_in
    cdef size_t link_space_craft_1_in_in = link_space_craft_1_in
    cdef size_t input_in_in = input_in
    cdef size_t factorials_in_in = factorials_in

    cdef size_t interp_array_in = interp_array
    cdef size_t h_t_in = h_t

    get_response(<double *>y_gw_in, <double *>k_in_in, <double *>u_in_in, <double *>v_in_in, dt,
                num_delays, <int *>link_space_craft_0_in_in, <int *>link_space_craft_1_in_in,
                <cmplx *>input_in_in, num_inputs, order, sampling_frequency, buffer_integer,
                <double *>factorials_in_in, num_factorials, input_start_time,
                <double* > interp_array_in, init_len, <double*> h_t_in)
