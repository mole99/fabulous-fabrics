PDK ?= ihp-sg13g2
FABULOUS_ROOT ?= $(abspath ../fabrics/fabric_10x10/macro/$(PDK)/fabulous)

$(info $(FABULOUS_ROOT))

# Get the design names
DESIGNS :=  $(patsubst designs/%/,%,$(wildcard designs/*/)) 

DESIGNS_CLEAN := $(addsuffix -clean,$(DESIGNS))
DESIGNS_SYNTH := $(addsuffix -synth,$(DESIGNS))
DESIGNS_PNR := $(addsuffix -pnr,$(DESIGNS))
DESIGNS_BIT := $(addsuffix -bit,$(DESIGNS))
DESIGNS_HEX := $(addsuffix -hex,$(DESIGNS))

all: $(DESIGNS)
.PHONY: all

clean: $(DESIGNS_CLEAN)
.PHONY: clean

$(DESIGNS):
	cd designs/$@; FABULOUS_ROOT=$(abspath $(FABULOUS_ROOT)) make
.PHONY: $(DESIGNS)

$(DESIGNS_CLEAN):
	cd designs/$(subst -clean,,$@); make clean
.PHONY: $(DESIGNS_CLEAN)

$(DESIGNS_SYNTH):
	cd designs/$(subst -synth,,$@); make synth
.PHONY: $(DESIGNS_SYNTH)

$(DESIGNS_PNR):
	cd designs/$(subst -synth,,$@); make pnr
.PHONY: $(DESIGNS_PNR)

$(DESIGNS_BIT):
	cd designs/$(subst -synth,,$@); make bitstream
.PHONY: $(DESIGNS_BIT)

$(DESIGNS_HEX):
	cd designs/$(subst -synth,,$@); make hex
.PHONY: $(DESIGNS_HEX)
