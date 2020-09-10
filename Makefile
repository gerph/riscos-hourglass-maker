# Build all the hourglasses

HOURGLASSES = artrayd1 artrayd1-bordered artrayd2
ARTIFACTS = $(shell pwd)/artifacts

all: ${HOURGLASSES:%=%.hg-build}
clean: ${HOURGLASSES:%=%.hg-clean}

%.hg-build:
	mkdir -p "${ARTIFACTS}"
	cd $* && make
	cp $*/rm32/Hourglass,ffa "${ARTIFACTS}/Hourglass-$*,ffa"
%.hg-clean:
	cd $* && make clean
