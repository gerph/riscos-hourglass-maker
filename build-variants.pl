#!/usr/bin/perl
##
# Build any variants of the Hourglass that we want.
#
# At present, only colours are supported.
#

use warnings;
use strict;

if (scalar(@_) == 1)
{
    die "Syntax: $0 {<colours> <name>}*";
}

while (1)
{
    my $colours = shift;
    my $name = shift;

    last if (!defined $name);

    my @rgbs = split /,/, $colours;
    if (scalar(@rgbs) % 3 != 0)
    {
        die "colours should be a R,G,B triple";
    }
    print "Colour name $name\n";
    for my $arch ('rm32', 'rm64')
    {
        next if (!-f "$arch/Hourglass,ffa");

        my $mod = '';
        open(my $ifh, '<', "$arch/Hourglass,ffa");
        while (<$ifh>)
        {
            $mod .= $_;
        }
        close($ifh);
        my $offset = index($mod, "PALD");
        if ($offset == -1)
        {
            die "Module does not contain PALD replacement signature";
        }
        if ($offset % 4 != 0)
        {
            die "Module contains PALD at an odd offset (not a multiple of 4)";
        }
        my $ncols = unpack "L<", substr($mod, $offset+4, 4);
        if ($ncols != scalar(@rgbs) / 3)
        {
            die "You supplied ".(scalar(@rgbs) / 3)." colours, but $ncols were needed";
        }
        my $replace = pack "C" . (scalar(@rgbs)), @rgbs;
        substr($mod, $offset+8, scalar(@rgbs), $replace);

        print "Creating hourglass '$arch/Hourglass$name,ffa'\n";
        open(my $ofh, '>', "$arch/Hourglass$name,ffa");
        print $ofh $mod;
        close($ofh);
    }
}
