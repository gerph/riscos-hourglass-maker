# Build all the hourglasses

HOURGLASSES = artrayd1 artrayd1-filled artrayd1-bordered \
			  artrayd2 artrayd2-filled \
			  cog cog-bordered \
			  nkozin nkozin-filled \
			  catgbp1990-world

ARTIFACTS = $(shell pwd)/artifacts

ifeq (${BUILD64},1)
ARCHSUFFIX=64
else
ARCHSUFFIX=32
endif

all: ${HOURGLASSES:%=%.hg-build}
clean: ${HOURGLASSES:%=%.hg-clean}

%.hg-build:
	mkdir -p "${ARTIFACTS}"
	cd $* && make MODULE_NAME=$* BUILD64=${BUILD64}
	cp $*/rm${ARCHSUFFIX}/Hourglass,ffa "${ARTIFACTS}/Hourglass-$*,ffa"
	for rm in $*/rm32/Hourglass*,ffa ; do suffix=$$(echo "$$rm" | sed -Ee 's/.*Hourglass(.*),ffa/\1/') ; if [ "$$suffix" != '' ] ; then cp "$$rm" "${ARTIFACTS}/Hourglass-$*-$$suffix,ffa" ; fi ; done
	cp $*/example.png "${ARTIFACTS}/Example-$*.png"
%.hg-clean:
	cd $* && make clean
