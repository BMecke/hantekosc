;;
;; This file is part of the sigrok-firmware-fx2lafw project.
;;
;; Copyright (C) 2016 Uwe Hermann <uwe@hermann-uwe.de>
;;
;; This program is free software; you can redistribute it and/or modify
;; it under the terms of the GNU General Public License as published by
;; the Free Software Foundation; either version 2 of the License, or
;; (at your option) any later version.
;;
;; This program is distributed in the hope that it will be useful,
;; but WITHOUT ANY WARRANTY; without even the implied warranty of
;; MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
;; GNU General Public License for more details.
;;
;; You should have received a copy of the GNU General Public License
;; along with this program; if not, see <http://www.gnu.org/licenses/>.
;;

VID = 0xB504	; Manufacturer ID (0x04B5)
PID = 0x2001	; Product ID (0x0120) = DDS120

; Version and Power -> descriptor.inc
;VER = 0x0902	; FW version 0x0209
;POWER = 500/2	; Max 500 mA (1=2mA)

.include "../../DSO6022BE/descriptor.inc"


; -----------------------------------------------------------------------------
; Strings
; -----------------------------------------------------------------------------

.globl _serial_num

_dev_strings:

; See http://www.usb.org/developers/docs/USB_LANGIDs.pdf for the full list.
string_descriptor_lang 0 0x0409 ; Language code 0x0409 (English, US)

; Manufacturer string
string_descriptor_a 1,^"OpenHantek"
; Product string
string_descriptor_a 2,^"DDS120"
; Serial number string template for unique FX2LP id
; must be 12 byte long -> Cypress KBA212789
_serial_num:
string_descriptor_a 3,^"000000000000"
_dev_strings_end:
	.dw	0x0000
