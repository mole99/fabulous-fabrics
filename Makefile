PDK ?= ihp-sg13g2
PDK_ROOT ?= ~/.ciel

# A rule for all tiles
fabric:
	librelane --pdk ${PDK} fabrics/basic/config.yaml
.PHONY: fabric

fabric-openroad:
	librelane --pdk ${PDK} fabrics/basic/config.yaml --last-run --flow OpenInOpenROAD
.PHONY: fabric-openroad

fabric-klayout:
	librelane --pdk ${PDK} fabrics/basic/config.yaml --last-run --flow OpenInKLayout
.PHONY: fabric-klayout
