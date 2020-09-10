# Build all the hourglasses

HOURGLASSES = artrayd1 artrayd1-filled artrayd1-bordered \
			  artrayd2 artrayd2-filled \
			  cog cog-bordered

all: ${HOURGLASSES:%=%.hg}

%.hg:
	cd $* && make
