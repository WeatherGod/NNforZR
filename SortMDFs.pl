#!/usr/bin/perl -w

use strict;
use File::Path;	# for mkpath

opendir(BASEDIR, ".") or die "Could not open this directory: $!\n";

while (defined(my $filename = readdir(BASEDIR)))
{
	if ($filename =~ m/(\d{4})(\d\d)(\d\d)\d{4}\.mdf$/)
	{
		mkpath("./$1/$2/$3/", {mask => 0755});
		rename("./$filename", "./$1/$2/$3/$filename") or print STDERR "$filename\n";
	}
}

closedir(BASEDIR);

print "Done!\n";
exit;

