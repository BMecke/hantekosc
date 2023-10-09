/*
 * This file is part of the sigrok-firmware-fx2lafw project.
 *
 * Copyright (C) 2009 Ubixum, Inc.
 * Copyright (C) 2015 Jochen Hoenicke
 *
 * This library is free software; you can redistribute it and/or
 * modify it under the terms of the GNU Lesser General Public
 * License as published by the Free Software Foundation; either
 * version 2.1 of the License, or (at your option) any later version.
 *
 * This library is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
 * Lesser General Public License for more details.
 *
 * You should have received a copy of the GNU Lesser General Public
 * License along with this library; if not, see <http://www.gnu.org/licenses/>.
 */

#include <autovector.h>
#include <delay.h>
#include <eputils.h>
#include <fx2ints.h>
#include <fx2macros.h>
#include <i2c.h>
#include <setupdat.h>

/* Port A
 * PA7 - calibration out
 * PA6 - AC CH1 out
 * PA5..4 - gain CH1 out
 * PA3 - LED green out
 * PA2 - AC CH0 out
 * PA1..0 - gain CH1 out
 */

/* A and C and E set to PORT */
#define INIT_PORTACFG 0
#define INIT_PORTCCFG 0
#define INIT_PORTECFG 0

/* Set port A that a 6021 will start in DC mode like the original */
#define INIT_IOA 0x00
#define INIT_IOC 0x00
#define INIT_IOE 0x00

/* set PORT A as output, unavailable C and E as input */
#define INIT_OEA 0xFF
#define INIT_OEC 0x00
#define INIT_OEE 0x00


#define SET_ANALOG_MODE()

// Resetting PA2 disables AC coupling capacitor on CH0.
// Resetting PA6 disables AC coupling capacitor on CH1.

#define CH0_DC()     \
    do { \
        IOA &= ~0x04; \
    } while ( 0 )
#define CH0_AC() \
    do { \
        IOA |= 0x04; \
    } while ( 0 )
#define CH1_DC() \
    do { \
        IOA &= ~0x40; \
    } while ( 0 )
#define CH1_AC() \
    do { \
        IOA |= 0x40; \
    } while ( 0 )


/**
 * Each LSB in the nibble of the byte controls the coupling per channel.
 * 0: AC, 1: DC
 */
static BOOL set_coupling( BYTE coupling_cfg ) {
    if ( coupling_cfg & 0x01 )
        IOA &= ~0x04;
    else
        IOA |= 0x04;
    if ( coupling_cfg & 0x10 )
        IOA &= ~0x40;
    else
        IOA |= 0x40;
    return TRUE;
}


#define TOGGLE_CALIBRATION_PIN() \
    do {                         \
        PA7 = !PA7;              \
    } while ( 0 )

#define LED_CLEAR() \
    do {            \
        PA3 = 0;    \
    } while ( 0 )
#define LED_GREEN() \
    do {            \
        PA3 = 1;    \
    } while ( 0 )
#define LED_RED()
#undef LED_RED_TOGGLE

/*
 * This sets two bits for each channel, one channel at a time.
 * For channel 0 we want to set bits 0, 1 ( ......XX => mask 0x03 )
 * For channel 1 we want to set bits 4, 5 ( ..XX.... => mask 0x30 )
 *
 * We convert the input values that are strange due to original
 * firmware code into the value of the three bits as follows:
 *
 * val -> bits
 * 1  -> 010b
 * 2  -> 001b
 * 5  -> 000b
 * 10 -> 011b
 * *
 * The multiplication of the converted value by 0x11 sets the relevant bits in
 * both channels and then we mask it out to only affect the channel currently
 * requested.
 */
static BOOL set_voltage( BYTE channel, BYTE val ) {
    BYTE bits, mask;

    switch ( val ) {
    case 1:
        bits = 0x11 * 2;
        break;
    case 2:
        bits = 0x11 * 1;
        break;
    case 5:
        bits = 0x11 * 0;
        break;
    case 10:
        bits = 0x11 * 3;
        break;
    default:
        return FALSE;
    }

    mask = ( channel ) ? 0x30 : 0x03;
    IOA = ( IOA & ~mask ) | ( bits & mask );

    return TRUE;
}

#include "../DSO6022BE/scope6022.inc"
