# Build all the hourglasses

HOURGLASSES = artrayd1 artrayd1-bordered artrayd2

all: ${HOURGLASSES:%=%.hg}

%.hg:
	cd $* && make
