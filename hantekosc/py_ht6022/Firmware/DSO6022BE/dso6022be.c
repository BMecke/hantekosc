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


/* A and C set to PORT */
#define INIT_PORTACFG 0
#define INIT_PORTCCFG 0
/* PE2: T2OUT for HW calibration output, other bits are port E output */
#define INIT_PORTECFG 0x04

/* Set port E that a 6022 with AC/DC HW mod will start in DC mode like the original */
#define INIT_IOA 0x00
#define INIT_IOC 0x00
#define INIT_IOE 0x09

/* set PORT A, C, E as output */
#define INIT_OEA 0xFF
#define INIT_OEC 0xFF
#define INIT_OEE 0xFF

/* not needed for 6022BE (only 6022BL) */
#define SET_ANALOG_MODE()


/**
 * Each LSB in the nibble of the byte controls the coupling per channel.
 * 0: AC, 1: DC
 *
 * Setting PE3 disables AC coupling capacitor on CH1.
 * Setting PE0 disables AC coupling capacitor on CH2.
 * Register IOE is not bit-addressable (only IOA and IOC).
 */
static BOOL set_coupling( BYTE coupling_cfg ) {
    if ( coupling_cfg & 0x01 )
        IOE |= 0x08;  // set IOE.3
    else
        IOE &= ~0x08; // reset IOE.3
    if ( coupling_cfg & 0x10 )
        IOE |= 0x01;  // set IOE.0
    else
        IOE &= ~0x01; // reset IOE.1
    return TRUE;
}


#define TOGGLE_CALIBRATION_PIN() \
    do {                         \
        PA7 = !PA7;              \
    } while ( 0 )

#define LED_CLEAR() \
    do {            \
        PC0 = 1;    \
        PC1 = 1;    \
    } while ( 0 )
#define LED_GREEN() \
    do {            \
        PC0 = 1;    \
        PC1 = 0;    \
    } while ( 0 )
#define LED_RED() \
    do {          \
        PC0 = 0;  \
        PC1 = 1;  \
    } while ( 0 )
#define LED_RED_TOGGLE() \
    do {                 \
        PC0 = !PC0;      \
        PC1 = 1;         \
    } while ( 0 )

/*
 * This sets three bits for each channel, one channel at a time.
 * For channel 0 we want to set bits 2, 3 & 4 ( ...XXX.. => mask 0x1c )
 * For channel 1 we want to set bits 5, 6 & 7 ( XXX..... => mask 0xe0 )
 *
 * We convert the input values that are strange due to original
 * firmware code into the value of the three bits as follows:
 *
 * val -> bits
 * 1  -> 010b
 * 2  -> 001b
 * 5  -> 000b
 * 10 -> 011b
 *
 * The third bit is always zero since there are only four outputs connected
 * in the serial selector chip.
 *
 * The multiplication of the converted value by 0x24 sets the relevant bits in
 * both channels and then we mask it out to only affect the channel currently
 * requested.
 */
static BOOL set_voltage( BYTE channel, BYTE val ) {
    BYTE bits, mask;

    switch ( val ) {
    case 1:
        bits = 0x24 * 2;
        break;
    case 2:
        bits = 0x24 * 1;
        break;
    case 5:
        bits = 0x24 * 0;
        break;
    case 10:
        bits = 0x24 * 3;
        break;
    default:
        return FALSE;
    }

    mask = ( channel ) ? 0xe0 : 0x1c;
    IOC = ( IOC & ~mask ) | ( bits & mask );

    return TRUE;
}

#include "scope6022.inc"
