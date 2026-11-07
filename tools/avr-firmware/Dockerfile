FROM ubuntu:22.04@sha256:076e7bf82319619f28dd0aa9c02ab34b055ad37100395b4f49a2ffba04fb5e11
ENV DEBIAN_FRONTEND=noninteractive
# Shared with the CPLD container's base layer; this image is otherwise independent.
RUN dpkg --add-architecture i386 && apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates git make python3 p7zip-full unzip wine wine32 wine64 \
    && rm -rf /var/lib/apt/lists/*
COPY sources.lock.json prepare.py /opt/avr/
COPY downloads/avrasm2.exe downloads/include.tar.gz downloads/Microchip.AVR-Dx_DFP.2.8.343.atpack /tmp/downloads/
RUN python3 /opt/avr/prepare.py /tmp/downloads && rm -rf /tmp/downloads
ENV WINEPREFIX=/opt/wine-avr WINEARCH=win32 WINEDEBUG=fixme-all,err+all TZ=UTC
RUN wineboot --init >/tmp/wine-init.log 2>&1 && wineserver -w && rm /tmp/wine-init.log
COPY build.py ihex.py /opt/avr/
WORKDIR /src
ENTRYPOINT ["python3", "/opt/avr/build.py"]
