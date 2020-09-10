# Build all the hourglasses

HOURGLASSES = artrayd1 artrayd1-filled artrayd1-bordered \
			  artrayd2 artrayd2-filled \
			  cog cog-bordered

ARTIFACTS = $(shell pwd)/artifacts

all: ${HOURGLASSES:%=%.hg-build}
clean: ${HOURGLASSES:%=%.hg-clean}

%.hg-build:
	mkdir -p "${ARTIFACTS}"
	cd $* && make MODULE_NAME=$*
	cp $*/rm32/Hourglass,ffa "${ARTIFACTS}/Hourglass-$*,ffa"
%.hg-clean:
	cd $* && make clean
