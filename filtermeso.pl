#!/usr/bin/perl -w

use strict;

use Math::Trig qw(great_circle_distance deg2rad);


my $radarLat = deg2rad(90.0 - 35.329);
my $radarLon = deg2rad(-97.274);

my $distThreshold = 160.0;	# kilometers, ~100 miles


open(STATLIST, "<geomeso_old.csv") or die "Could not open file!\n";


my $LineRead = '';

while (defined($LineRead = <STATLIST>))
{
        chomp($LineRead);
	my @lineVals = split(/,/, $LineRead);

	if (great_circle_distance((deg2rad($lineVals[3]), deg2rad(90.0 - $lineVals[2])),
				  ($radarLon, $radarLat), 6378) <= $distThreshold)
	{
		print "$LineRead\n";
	}
}

exit(0);
