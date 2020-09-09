##
# Build the hourglass RISC OS source files.
#

all: hourglass_basic,fd1 aif32/hourglass_test,ff8

clean:
	-rm frame*.png
	-rm simple*.png
	-rm palette.ppm
	-rm *.pyc
	-rm -rf aif32 rm32 o32

shape.py: source.gif build-shape.sh
	./build-shape.sh

hourglass_basic,fd1 s/asm: shape.py ../makehourglass.py
	../makehourglass.py

aif32/hourglass_test,ff8: s/asm ../c/hourglass_test
	riscos-amu -f MakefileRO BUILD32=1
