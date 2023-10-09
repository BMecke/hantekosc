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


/* A and C and E set to PORT */
#define INIT_PORTACFG 0
#define INIT_PORTCCFG 0
/* PE2: T2OUT for HW calibration output, other bits are port E output */
#define INIT_PORTECFG 0x04

/* Set port E that a 6022 with AC/DC HW mod will start in DC mode like the original */
#define INIT_IOA 0x00
#define INIT_IOC 0x00
#define INIT_IOE 0x0B

/* set PORT A, C, E as output */
#define INIT_OEA 0xFF
#define INIT_OEC 0xFF
#define INIT_OEE 0xFF


#define SET_ANALOG_MODE() \
    do {                  \
        PA7 = 1;          \
    } while ( 0 )


/**
 * Each LSB in the nibble of the byte controls the coupling per channel.
 * 0: AC, 1: DC
 * 
 * @fregmented wrote in pull request #9 (https://github.com/Ho-Ro/Hantek6022API/pull/9):
 * "I added PE1 to CH1 and PE2 to Ch2 to use R40 (PE0, CH2) and R41 (PE1, CH1)
 * connected to USB-XI ports because the 6022BL does not have JP2."
 * PE2 is not needed for AC/DC switching - can be used for T2OUT
 * 
 * Setting PE1 and PE3 disables AC coupling capacitor on CH1.
 * Setting PE0 and disables AC coupling capacitor on CH2.
 */
static BOOL set_coupling( BYTE coupling_cfg ) {
    if ( coupling_cfg & 0x01 )
        IOE |= 0x0A; // PE1 | PE3
    else
        IOE &= ~0x0A;
    if ( coupling_cfg & 0x10 )
        IOE |= 0x01; // PE0
    else
        IOE &= ~0x01;
    return TRUE;
}


#define TOGGLE_CALIBRATION_PIN() \
    do {                         \
        PC2 = !PC2;              \
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
 * For channel 0 we want to set bits 1, 2 & 3 ( ....XXX. => mask 0x0e )
 * For channel 1 we want to set bits 4, 5 & 6 ( .XXX.... => mask 0x70 )
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
 * The multiplication of the converted value by 0x12 sets the relevant bits in
 * both channels and then we mask it out to only affect the channel currently
 * requested.
 */
static BOOL set_voltage( BYTE channel, BYTE val ) {
    BYTE bits, mask;

    switch ( val ) {
    case 1:
        bits = 0x12 * 2;
        break;
    case 2:
        bits = 0x12 * 1;
        break;
    case 5:
        bits = 0x12 * 0;
        break;
    case 10:
        bits = 0x12 * 3;
        break;
    default:
        return FALSE;
    }

    mask = ( channel ) ? 0x70 : 0x0e;
    IOA = ( IOA & ~mask ) | ( bits & mask );

    return TRUE;
}

#include "../DSO6022BE/scope6022.inc"
