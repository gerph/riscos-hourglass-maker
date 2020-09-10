# Build all the hourglasses

HOURGLASSES = artrayd1 artrayd1-bordered artrayd2

all: ${HOURGLASSES:%=%.hg-build}
clean: ${HOURGLASSES:%=%.hg-clean}

%.hg-build:
	cd $* && make
%.hg-clean:
	cd $* && make clean
