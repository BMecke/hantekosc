#!/bin/sh

# Script to disassemble the firmware of 6022BE scope.
# Disassembler: dis51 version 0.5 
# Attached is a small patch dis51-0.5.diff
# to use hex addresses instead of decimal values.
# The hex values are code sections that are reached
# only by indirect jumps, e.g. LJMP @A+DPTR.

NAME=mod_fw_01
HEX=$NAME.ihex
A51=$NAME.a51
LST=$NAME.lst


cat > $A51 <<END
;---------------------------------
;   Mod 6022BE Firmware
;   for FX2LP chip (Enhanced 8051)
;
;   Disassembled with Dis51
;
;---------------------------------


END

cp $A51 $LST

dis51 \
    0 2a 2b 2e 33 43 4b 53 8f 92 95 98 9b 9e a1 a4 24b 296 2dc \
    31d 321 328 330 338 340 348 350 358 360 368 370 38c 3af 3c2 \
    446 465 95d 95e 960 968 971 96a a60 a73 b7b \
    c00 c04 c08 c0c c10 c14 c18 c1c c20 c24 c28 c2c c30 c34 c38 c3c \
    c40 c44 c48 c4c c50 c54 c58 c5c c60 c64 c68 c6c c70 c74 c78 c7c \
    c80 c84 c88 c8c c90 c94 c98 c9c ca0 ca4 ca8 cac cb0 cb4 \
    e92 ebf 104c 1089 10c0 1281 1299 12b1 12c7 \
    < $HEX >> $A51

dis51 -l \
    0 2a 2b 2e 33 43 4b 53 8f 92 95 98 9b 9e a1 a4 24b 296 2dc \
    31d 321 328 330 338 340 348 350 358 360 368 370 38c 3af 3c2 \
    446 465 95d 95e 960 968 971 96a a60 a73 b7b \
    c00 c04 c08 c0c c10 c14 c18 c1c c20 c24 c28 c2c c30 c34 c38 c3c \
    c40 c44 c48 c4c c50 c54 c58 c5c c60 c64 c68 c6c c70 c74 c78 c7c \
    c80 c84 c88 c8c c90 c94 c98 c9c ca0 ca4 ca8 cac cb0 cb4 \
    e92 ebf 104c 1089 10c0 1281 1299 12b1 12c7 \
    < $HEX >> $LST
