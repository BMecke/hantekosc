;; include file "descriptor.inc"
;;
;; This file is part of the sigrok-firmware-fx2lafw project.
;;
;; Copyright (C) 2009 Ubixum, Inc. 
;;
;; This library is free software; you can redistribute it and/or
;; modify it under the terms of the GNU Lesser General Public
;; License as published by the Free Software Foundation; either
;; version 2.1 of the License, or (at your option) any later version.
;;
;; This library is distributed in the hope that it will be useful,
;; but WITHOUT ANY WARRANTY; without even the implied warranty of
;; MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
;; Lesser General Public License for more details.
;;
;; You should have received a copy of the GNU Lesser General Public
;; License along with this library; if not, see <http://www.gnu.org/licenses/>.
;;
;;
;; This file is part of the sigrok-firmware-fx2lafw project.
;;
;; Copyright (C) 2016 Stefan Brüns <stefan.bruens@rwth-aachen.de>
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

; Firmware version, sync with "__version__" in "setup.py" and "FIRMWARE_VERSION" in "PyHT6022/LibUsbScope.py"
FIRMWARE_VERSION = 0x1002	; FW version '2.10' (byte swapped)

; USB power requirement
USB_POWER = 500/2		; Max 500 mA (1=2mA)


.macro string_descriptor_a n,str
_string'n:
	.nchr	len,"'str"
	.db	len * 2 + 2
	.db	3
	.irpc	i,^"'str"
		.db	''i, 0
	.endm
.endm

.macro string_descriptor_lang n,l
_string'n:
	.db	4
	.db	3
	.dw	>l + (<l * 0x100)
.endm


.module DEV_DSCR

; Descriptor types
DSCR_DEVICE_TYPE	= 1
DSCR_CONFIG_TYPE	= 2
DSCR_STRING_TYPE	= 3
DSCR_INTERFACE_TYPE	= 4
DSCR_ENDPOINT_TYPE	= 5
DSCR_DEVQUAL_TYPE	= 6

; Descriptor lengths
DSCR_INTERFACE_LEN	= 9
DSCR_ENDPOINT_LEN	= 7

; Endpoint types
ENDPOINT_TYPE_CONTROL	= 0
ENDPOINT_TYPE_ISO	= 1
ENDPOINT_TYPE_BULK	= 2
ENDPOINT_TYPE_INT	= 3

.globl _dev_dscr, _dev_qual_dscr, _highspd_dscr, _fullspd_dscr, _dev_strings, _dev_strings_end
.area DSCR_AREA (CODE)

; -----------------------------------------------------------------------------
; Device descriptor
; -----------------------------------------------------------------------------
_dev_dscr:
	.db	dev_dscr_end - _dev_dscr
	.db	DSCR_DEVICE_TYPE
	.dw	0x0002			; USB 2.0
	.db	0xff			; Class (vendor specific)
	.db	0xff			; Subclass (vendor specific)
	.db	0xff			; Protocol (vendor specific)
	.db	64			; Max. EP0 packet size
	.dw	VID			; Manufacturer ID
	.dw	PID			; Product ID
	.dw	FIRMWARE_VERSION	; Product version/type
	.db	1			; Manufacturer string index
	.db	2			; Product string index
	.db	3			; Serial number string index, 0 if none
	.db	1			; Number of configurations
dev_dscr_end:

; -----------------------------------------------------------------------------
; Device qualifier (for "other device speed")
; -----------------------------------------------------------------------------
_dev_qual_dscr:
	.db	dev_qualdscr_end - _dev_qual_dscr
	.db	DSCR_DEVQUAL_TYPE
	.dw	0x0002			; USB 2.0
	.db	0			; Class (0)
	.db	0			; Subclass (0)
	.db	0			; Protocol (0)
	.db	64			; Max. EP0 packet size
	.db	1			; Number of configurations
	.db	0			; Extra reserved byte
dev_qualdscr_end:

; -----------------------------------------------------------------------------
; High-Speed configuration descriptor
; -----------------------------------------------------------------------------
_highspd_dscr:
	.db	highspd_dscr_end - _highspd_dscr
	.db	DSCR_CONFIG_TYPE
	; Total length of the configuration (1st line LSB, 2nd line MSB)
	.db	(highspd_dscr_realend - _highspd_dscr) % 256
	.db	(highspd_dscr_realend - _highspd_dscr) / 256
	.db	1			; Number of interfaces
	.db	1			; Configuration number
	.db	0			; Configuration string (none)
	.db	0x80			; Attributes (bus powered, no wakeup)
	.db	USB_POWER		; Max. power, defined in descriptor.asm
highspd_dscr_end:

	; Bulk interface 0, alt 0
	.db	DSCR_INTERFACE_LEN
	.db	DSCR_INTERFACE_TYPE
	.db	0			; Interface index
	.db	0			; Alternate setting index
	.db	1			; Number of endpoints
	.db	0xff			; Class (vendor specific)
	.db	0			; Subclass (0)
	.db	0			; Protocol (0)
	.db	0			; String index (none)

	; Endpoint 6 (IN)
	.db	DSCR_ENDPOINT_LEN
	.db	DSCR_ENDPOINT_TYPE
	.db	0x86			; EP number (6), direction (IN)
	.db	ENDPOINT_TYPE_BULK	; Endpoint type (bulk)
	.db	0x00			; Max. packet size, LSB (512 bytes)
	.db	0x02			; Max. packet size, MSB (512 bytes)
	.db	0x00			; Polling interval (ignored for bulk)

	; Isochronous interface 0, alt 1
	.db	DSCR_INTERFACE_LEN
	.db	DSCR_INTERFACE_TYPE
	.db	0			; Interface index
	.db	1			; Alternate setting index
	.db	1			; Number of endpoints
	.db	0xff			; Class (vendor specific)
	.db	0			; Subclass (0)
	.db	1			; Protocol (1)
	.db	0			; String index (none)

	; Endpoint 2 (IN)
	.db	DSCR_ENDPOINT_LEN
	.db	DSCR_ENDPOINT_TYPE
	.db	0x82			; EP number (2), direction (IN)
	.db	ENDPOINT_TYPE_ISO	; Endpoint type (iso)
	.db	0x00			; Max. packet size, LSB (3*1024 bytes)
	.db	0x14			; Max. packet size, MSB (3*1024 bytes)
					; 12:11 = 0b10 (3 tr. per microframe)
					; 10:00 = 1024
	.db	0x01			; Polling interval (1 microframe)

	; Isochronous interface 0, alt 2, 16MB/s
	.db	DSCR_INTERFACE_LEN
	.db	DSCR_INTERFACE_TYPE
	.db	0			; Interface index
	.db	2			; Alternate setting index
	.db	1			; Number of endpoints
	.db	0xff			; Class (vendor specific)
	.db	0			; Subclass (0)
	.db	1			; Protocol (1)
	.db	0			; String index (none)

	; Endpoint 2 (IN)
	.db	DSCR_ENDPOINT_LEN
	.db	DSCR_ENDPOINT_TYPE
	.db	0x82			; EP number (2), direction (IN)
	.db	ENDPOINT_TYPE_ISO	; Endpoint type (iso)
	.db	0x00			; Max. packet size, LSB (2*1024 bytes)
	.db	0x0c			; Max. packet size, MSB (2*1024 bytes)
					; 12:11 = 0b01 (2 tr. per microframe)
					; 10:00 = 1024
	.db	0x01			; Polling interval (1 microframe)

	; Isochronous interface 0, alt 3, 8MB/s
	.db	DSCR_INTERFACE_LEN
	.db	DSCR_INTERFACE_TYPE
	.db	0			; Interface index
	.db	3			; Alternate setting index
	.db	1			; Number of endpoints
	.db	0xff			; Class (vendor specific)
	.db	0			; Subclass (0)
	.db	1			; Protocol (1)
	.db	0			; String index (none)

	; Endpoint 2 (IN)
	.db	DSCR_ENDPOINT_LEN
	.db	DSCR_ENDPOINT_TYPE
	.db	0x82			; EP number (2), direction (IN)
	.db	ENDPOINT_TYPE_ISO	; Endpoint type (iso)
	.db	0x00			; Max. packet size, LSB (1024 bytes)
	.db	0x04			; Max. packet size, MSB (1024 bytes)
	.db	0x01			; Polling interval (1 microframe)

	; Isochronous interface 0, alt 4, 4MB/s
	.db	DSCR_INTERFACE_LEN
	.db	DSCR_INTERFACE_TYPE
	.db	0			; Interface index
	.db	4			; Alternate setting index
	.db	1			; Number of endpoints
	.db	0xff			; Class (vendor specific)
	.db	0			; Subclass (0)
	.db	1			; Protocol (1)
	.db	0			; String index (none)

	; Endpoint 2 (IN)
	.db	DSCR_ENDPOINT_LEN
	.db	DSCR_ENDPOINT_TYPE
	.db	0x82			; EP number (2), direction (IN)
	.db	ENDPOINT_TYPE_ISO	; Endpoint type (iso)
	.db	0x00			; Max. packet size, LSB (1024 bytes)
	.db	0x04			; Max. packet size, MSB (1024 bytes)
	.db	0x02			; Polling interval (2 microframes)

	; Isochronous interface 0, alt 5, 2MB/s
	.db	DSCR_INTERFACE_LEN
	.db	DSCR_INTERFACE_TYPE
	.db	0			; Interface index
	.db	5			; Alternate setting index
	.db	1			; Number of endpoints
	.db	0xff			; Class (vendor specific)
	.db	0			; Subclass (0)
	.db	1			; Protocol (1)
	.db	0			; String index (none)

	; Endpoint 2 (IN)
	.db	DSCR_ENDPOINT_LEN
	.db	DSCR_ENDPOINT_TYPE
	.db	0x82			; EP number (2), direction (IN)
	.db	ENDPOINT_TYPE_ISO	; Endpoint type (iso)
	.db	0x00			; Max. packet size, LSB (1024 bytes)
	.db	0x04			; Max. packet size, MSB (1024 bytes)
	.db	0x03			; Polling interval (4 microframes)

	; Isochronous interface 0, alt 6, 1MB/s
	.db	DSCR_INTERFACE_LEN
	.db	DSCR_INTERFACE_TYPE
	.db	0			; Interface index
	.db	6			; Alternate setting index
	.db	1			; Number of endpoints
	.db	0xff			; Class (vendor specific)
	.db	0			; Subclass (0)
	.db	1			; Protocol (1)
	.db	0			; String index (none)

	; Endpoint 2 (IN)
	.db	DSCR_ENDPOINT_LEN
	.db	DSCR_ENDPOINT_TYPE
	.db	0x82			; EP number (2), direction (IN)
	.db	ENDPOINT_TYPE_ISO	; Endpoint type (iso)
	.db	0x00			; Max. packet size, LSB (1024 bytes)
	.db	0x04			; Max. packet size, MSB (1024 bytes)
	.db	0x04			; Polling interval (8 microframes)

	; Isochronous interface 0, alt 7, 500kB/s
	.db	DSCR_INTERFACE_LEN
	.db	DSCR_INTERFACE_TYPE
	.db	0			; Interface index
	.db	7			; Alternate setting index
	.db	1			; Number of endpoints
	.db	0xff			; Class (vendor specific)
	.db	0			; Subclass (0)
	.db	1			; Protocol (1)
	.db	0			; String index (none)

	; Endpoint 2 (IN)
	.db	DSCR_ENDPOINT_LEN
	.db	DSCR_ENDPOINT_TYPE
	.db	0x82			; EP number (2), direction (IN)
	.db	ENDPOINT_TYPE_ISO	; Endpoint type (iso)
	.db	0x00			; Max. packet size, LSB (512 bytes)
	.db	0x02			; Max. packet size, MSB (512 bytes)
	.db	0x04			; Polling interval (8 microframes)

highspd_dscr_realend:

	.even

; -----------------------------------------------------------------------------
; Full-Speed configuration descriptor
; -----------------------------------------------------------------------------
_fullspd_dscr:
	.db	fullspd_dscr_end - _fullspd_dscr
	.db	DSCR_CONFIG_TYPE
	; Total length of the configuration (1st line LSB, 2nd line MSB)
	.db	(fullspd_dscr_realend - _fullspd_dscr) % 256
	.db	(fullspd_dscr_realend - _fullspd_dscr) / 256
	.db	2			; Number of interfaces
	.db	1			; Configuration number
	.db	0			; Configuration string (none)
	.db	0x80			; Attributes (bus powered, no wakeup)
	.db	USB_POWER		; Max. power, defined in descriptor.asm
fullspd_dscr_end:

	; Bulk interface 0, alt 0
	.db	DSCR_INTERFACE_LEN
	.db	DSCR_INTERFACE_TYPE
	.db	0			; Interface index
	.db	0			; Alternate setting index
	.db	1			; Number of endpoints
	.db	0xff			; Class (vendor specific)
	.db	0			; Subclass (0)
	.db	0			; Protocol (0)
	.db	0			; String index (none)

	; Endpoint 6 (IN)
	.db	DSCR_ENDPOINT_LEN
	.db	DSCR_ENDPOINT_TYPE
	.db	0x86			; EP number (6), direction (IN)
	.db	ENDPOINT_TYPE_BULK	; Endpoint type (bulk)
	.db	0x40			; Max. packet size, LSB (64 bytes)
	.db	0x00			; Max. packet size, MSB (64 bytes)
	.db	0x00			; Polling interval (ignored for bulk)

	; Isochronous interface 0, alt 1, 1MB/s
	.db	DSCR_INTERFACE_LEN
	.db	DSCR_INTERFACE_TYPE
	.db	0			; Interface index
	.db	1			; Alternate setting index
	.db	1			; Number of endpoints
	.db	0xff			; Class (vendor specific)
	.db	0			; Subclass (0)
	.db	1			; Protocol (1)
	.db	0			; String index (none)

	; Endpoint 2 (IN)
	.db	DSCR_ENDPOINT_LEN
	.db	DSCR_ENDPOINT_TYPE
	.db	0x82			; EP number (2), direction (IN)
	.db	ENDPOINT_TYPE_ISO	; Endpoint type (iso)
	.db	0xff			; Max. packet size, LSB (1023 bytes)
	.db	0x03			; Max. packet size, MSB (1023 bytes)
	.db	0x01			; Polling interval (1 frame)

	; Isochronous interface 0, alt 2, 500kB/s
	.db	DSCR_INTERFACE_LEN
	.db	DSCR_INTERFACE_TYPE
	.db	0			; Interface index
	.db	2			; Alternate setting index
	.db	1			; Number of endpoints
	.db	0xff			; Class (vendor specific)
	.db	0			; Subclass (0)
	.db	1			; Protocol (1)
	.db	0			; String index (none)

	; Endpoint 2 (IN)
	.db	DSCR_ENDPOINT_LEN
	.db	DSCR_ENDPOINT_TYPE
	.db	0x82			; EP number (2), direction (IN)
	.db	ENDPOINT_TYPE_ISO	; Endpoint type (iso)
	.db	0x00			; Max. packet size, LSB (512 bytes)
	.db	0x02			; Max. packet size, MSB (512 bytes)
	.db	0x01			; Polling interval (1 frame)

fullspd_dscr_realend:

	.even

