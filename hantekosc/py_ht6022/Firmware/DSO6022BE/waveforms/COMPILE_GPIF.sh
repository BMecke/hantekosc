#!/bin/sh

# use "gpif_compiler" from https://github.com/Ho-Ro/ezusb_gpif_compiler

for WVF in *.wvf; do
	gpif_compiler < ${WVF} > $(basename ${WVF} .wvf).inc
done

cat gpif_*.inc > waveforms.inc
cp waveforms.inc ..
