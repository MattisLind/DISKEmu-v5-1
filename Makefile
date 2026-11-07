.DEFAULT_GOAL := help
TOOLCHAIN := tools/atf15xx-yosys-docker

.PHONY: help toolchain jed-cupl cpld cpld-main cpld-dma cpld-verify tool-versions toolchain-test
help:
	@echo "make toolchain       Build the CUPL/VHDL Docker image"
	@echo "make jed-cupl        Compile and fit both original Q-bus CPLDs"
	@echo "make jed-vhdl        Build both independent VHDL sources"
	@echo "make compare-jed     Require byte-identical PLD/VHDL outputs"
	@echo "make check-equations Prove VHDL equations against original CUPL TT2"
	@echo "make cpld-verify     Check both generated JEDEC files"
	@echo "make tool-versions   Show compiler/fitter identities"
	@echo "make toolchain-test  Run parser tests and a VHDL-to-JEDEC smoke test"

toolchain:
	"$(TOOLCHAIN)/build-docker.sh"

jed-cupl cpld:
	$(MAKE) -C DISKEmu-v5-1-CPLD jed-cupl

cpld-main:
	$(MAKE) -C DISKEmu-v5-1-CPLD main

cpld-dma:
	$(MAKE) -C DISKEmu-v5-1-CPLD dma

cpld-verify:
	$(MAKE) -C DISKEmu-v5-1-CPLD verify

tool-versions:
	$(MAKE) -C DISKEmu-v5-1-CPLD tool-versions

toolchain-test:
	"$(TOOLCHAIN)/smoke-test.sh"

.PHONY: jed-vhdl compare-jed
jed-vhdl:
	$(MAKE) -C DISKEmu-v5-1-CPLD jed-vhdl
compare-jed:
	$(MAKE) -C DISKEmu-v5-1-CPLD compare-jed

.PHONY: check-equations
check-equations:
	$(MAKE) -C DISKEmu-v5-1-CPLD check-equations

.PHONY: cpld-test
cpld-test:
	$(MAKE) -C DISKEmu-v5-1-CPLD test check-equations compare-jed
