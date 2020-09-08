##
# Build the hourglass RISC OS source files.
#

all: hourglass_basic,fd1

clean:
	-rm frame*.png
	-rm simple*.png
	-rm palette.ppm
	-rm *.pyc

shape.py: source.gif build-shape.sh
	./build-shape.sh

hourglass_basic,fd1: shape.py ../makehourglass.py
	../makehourglass.py
