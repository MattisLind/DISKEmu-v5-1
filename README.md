# DISK Emulator

## Introduction
The Q-BUS is a bus invented by DEC and was first used for small PDP-11 systems like the LSI-11. There were several backplanes available from DEC
and 3rd parties. For a complete PDP-11 system you needed a CPU card, memory, at least a console and some sort of mass storage device. Depending
on the operation sytem you needed additional cards like a line time clock and others.

## Controller Card
This is a Q-BUS PCB for a Q-BUS PDP-11 system that emulates disk controllers depending on the firmware of the microcontroller and the CPLD design files.
Currently there are two disk controller emulation, a RLV12 controller with four RL01/02 disks attached and a MSCP controller with four units.
The Q-BUS controller provides a command line interface to control the functions and configuration and a SD-Card to store the PDP-11 disk images.

[Assembled DISK Emulator for the Q-Bus](https://www.5volts.ch/pages/mscpemulator/images/IMG_0579.jpeg)
