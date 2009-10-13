#!/usr/bin/perl -w

use strict;
use DateTime;
use NetCDF;
use File::Path qw(mkpath);
use Math::Trig qw(great_circle_distance deg2rad);
use Math::Round qw(nearest round);

# This program will read the NCDC NEXRAD data exporter's
# gridded netcdf files and build a training set from
# the data contained within them.
# This program requires a list of mesonet stations
# with the lat and lons in the format of:
#
# StatNum,StatName,lat,lon
#
# Where latitudes and longitudes are in degrees North and East.
#
# The training data is appended to the file 'trainingData.csv'
# and must be put through 'filtertraining.pl' before the
# training data is used in WEKA.
#
# Also, this program will automatically download any needed
# mesonet data files in order to build the training set.
#
# Finally, it is assumed that the radar data is named such that
# it matches 'KTLX%Y%m%d_%H%M%S.nc'
#
# Input arguements to this program is a list of the netcdf files
# to process.


sub GetRadarTime($);
sub GetReflectivities($\%\%);
sub GetDataLocations($$);
sub FindClosest($\@);
sub GrabMesonetFile($$);
sub GetMesonetData($$);
sub ScanMesonetData($);
sub MergeData(\%\%);
sub LoadStationList($);
sub NearestMinute($$);
sub GetRainfall($);


#my $fakeFile = "/tint/netCDF/1995/05/26/KTLX/6500KTLX19950526_000219.nc";
#my $fakeRadarTime = GetRadarTime($fakeFile);
#my $fakeMainTime = NearestMinute($fakeRadarTime, 5);
#my %fakeMesonet1 = GetMesonetData(($fakeMainTime >= $fakeRadarTime), $fakeMainTime);
#my %fakeMesonet2 = GetMesonetData(!($fakeMainTime >= $fakeRadarTime), $fakeMainTime);

#print "\nMerging...\n";
#my %fakeMesonet = MergeData(%fakeMesonet1, %fakeMesonet2);

#exit;


# Get all of the mesonet stations and their locations.
my %statLocs = LoadStationList("geomeso.csv");

# This variable is for seeing if there is a change in
# the grid.  If not, then don't recompute the station
# grid locations.  If yes, then do recompute the station
# locations.
my %lastGrid = (
		xSize => 0,
		ySize => 0
	       );


# now open the training file for writing.
#open(TRAINSTREAM, ">>trainingData_retry.csv");

print STDERR "Processing radar files:\n";
# Now process each radar file
foreach my $radarFile (@ARGV)
{

	print STDERR "$radarFile\n";
	# Need to get radar time for this file
	my $radarTime = GetRadarTime($radarFile);

        my $trainingFile = sprintf("trainingDir/%s_%s.csv", $radarTime->ymd(), $radarTime->hms());
        open(TRAINSTREAM, ">$trainingFile");

	if (!defined($radarTime))
	{
		print STDERR "ERROR: Invalid filename: $radarFile\n";
		next;
	}

	my $yearFraction = sprintf("%.4f", ($radarTime->day_of_year() + (($radarTime->hour()*60 + $radarTime->minute()) / (24*60)))
						 / ($radarTime->is_leap_year() ? 366 : 365));

	print STDERR "Getting reflectivities...\n";
	my %stationReflects = GetReflectivities($radarFile, %statLocs, %lastGrid);
	print STDERR "done\n";

	if (!defined(%stationReflects))
	{
		print STDERR "ERROR: Could not open file: $radarFile\n";
		next;
	}

	my $mainTime = NearestMinute($radarTime, 5);

	# Now need to get the mesonet data to go with that time
	#print "Getting Mesonet1 data\n";
	my %mesonetData1 = GetMesonetData(($mainTime >= $radarTime), $mainTime);
	#print "Getting Mesonet2 data\n";
	my %mesonetData2 = GetMesonetData(!($mainTime >= $radarTime), $mainTime);

	#print "Merging mesonet data\n";
	my %mesonetData = MergeData(%mesonetData1, %mesonetData2);	

	# Now save that data!
	foreach my $station (keys %statLocs)
	{
		next if (!exists($mesonetData{$station}));
		next if ($stationReflects{$station} eq 'nan');

		my $stationData = $mesonetData{$station};

		my $badRec = 0;
		foreach my $varName (keys %$stationData)
		{
			if ($stationData->{$varName} eq 'nan')
			{
				$badRec = 1;
			}
		}

		next if ($badRec == 1);

		my $tair = sprintf("%.1f", $stationData->{'tair'}); # if ($stationData->{'tair'} ne 'nan');
		my $relh = sprintf("%d", $stationData->{'relh'}); #if ($stationData->{'relh'} ne 'nan');
		my $press = sprintf("%.2f", $stationData->{'press'}); #if ($stationData->{'press'} ne 'nan');
		my $reflect = sprintf("%.3f", $stationReflects{$station}); #if ($stationReflects{$station} ne 'nan');
		my $rain = sprintf("%.5f", $stationData->{'rate'});


		my $uwnd = sprintf("%.4f", $stationData->{'uwnd'}); # if ($stationData->{'wvec'} ne 'nan'
		my $vwnd = sprintf("%.4f", $stationData->{'vwnd'}); # if ($stationData->{'wvec'} ne 'nan'
		

		print TRAINSTREAM "$tair,$relh,$press,$uwnd,$vwnd,$reflect,$rain\n";
	}

        close(TRAINSTREAM);
}


# finished!  close the training file.
#close(TRAINSTREAM);

exit(0);





###############################################################
sub GetRadarTime($)
{
	my $filename = shift;
	# TODO: Maybe change this to utilize the time in the file?

	my $radarTime = undef;

	if ($filename =~ m/KTLX(\d\d\d\d)(\d\d)(\d\d)_(\d\d)(\d\d)(\d\d).nc$/)
	{
		$radarTime = DateTime->new( year	=> $1,
					    month	=> $2,
					    day		=> $3,
					    hour	=> $4,
					    minute	=> $5,
					    second	=> $6,
					    time_zone	=> 'UTC' );
	}

	return $radarTime;
}


sub GetReflectivities($\%\%)
{
	my $radarFile = shift;
	my $stationsRef = shift;
	my $gridRef = shift;

	# Now create an empty hash
	my %reflectivites = ();

	# open the file
	my $ncid;
	if (($ncid = NetCDF::open($radarFile, NetCDF::NOWRITE)) == -1)
	{
		undef %reflectivites;
		return %reflectivites;
	}

	my $varid;
	if (($varid = NetCDF::varid($ncid, "value")) == -1)
	{
		undef %reflectivites;
		return %reflectivites;
	}

	my @dataLocs = GetDataLocations($ncid, $gridRef);

	print STDERR "Finding closest points...\n";


	# Now go through each station's location
	while (my($statName, $locRef) = each(%$stationsRef))
	{
#		print STDERR "   $statName   $locRef->{'lat'}  $locRef->{'lon'}";
		# Find the closest grid point to location specified in hash
		# pointed to by $locRef and save it in that hash.
		# But only do so if needed.
		FindClosest($locRef, @dataLocs) if ($#dataLocs != 0);

#		print STDERR "GridLocs: $locRef->{'coords'}{'xLoc'}, $locRef->{'coords'}{'yLoc'}\n";


		# Grab that grid point's reflectivity and save it!
		my @dataVals = ();
		my @startVect = (0, $locRef->{'coords'}{'yLoc'}, $locRef->{'coords'}{'xLoc'});
		my @reachVect = (1, 1, 1);

		NetCDF::varget($ncid, $varid, \@startVect, \@reachVect, \@dataVals);
		$reflectivites{$statName} = $dataVals[0];
	}

	print STDERR "done!\n";
	
	# now close the file
	NetCDF::close($ncid);


	return %reflectivites;
}


sub FindClosest($\@)
{
#	print "In FindClosest!\n";
	my $locRef = shift;
	my $datalocsRef = shift;

	my $smallestDist = 10000000;

	my $statLon = $locRef->{'lon'};
	my $statLat = $locRef->{'lat'};

	foreach my $loc (@$datalocsRef)
	{
		my $theDist = great_circle_distance(($locRef->{'lon'}, $locRef->{'lat'}),
						    ($loc->{'lon'}, $loc->{'lat'}),
						    6378);
		if ($theDist < $smallestDist)
		{
			$smallestDist = $theDist;
			$locRef->{'coords'} = $loc->{'coords'};
		}
	}
}

sub GetDataLocations($$)
{
	my $ncid = shift;
	my $gridRef = shift;

	my $latid = NetCDF::dimid($ncid, "lat");

	my $latSize = 0;
	my $latName = '';

	# assume error-free...
	NetCDF::diminq($ncid, $latid, \$latName, \$latSize);
	# now getting the varid of the variable version of the dimension.
	$latid = NetCDF::varid($ncid, "lat");	
	print "LatID: $latid\n";

	my $lonid = NetCDF::dimid($ncid, "lon");

	my $lonSize = 0;
	my $lonName = '';

	# assume error-free...
	NetCDF::diminq($ncid, $lonid, \$lonName, \$lonSize);
	# now getting the varid of the variable version of the dimension.
	$lonid = NetCDF::varid($ncid, "lon");
	print "LonID: $lonid\n";

	my @dataLocs = ();

	if ($gridRef->{'xSize'} == $lonSize && $gridRef->{'ySize'} == $latSize)
	{
		# This empty array should signal that we don't need to recompute.
		return(@dataLocs);
	}
	
	# The grid is different from last time...
	# recompute the information.
	$gridRef->{'xSize'} = $lonSize;
	$gridRef->{'ySize'} = $latSize;

	# Obtain the dimension values
	my @lats = ();
	my @lons = ();

	print STDERR "Getting dimension data...";
	NetCDF::varget($ncid, $latid, ( 0 ), ( $latSize ), \@lats);
	NetCDF::varget($ncid, $lonid, ( 0 ), ( $lonSize ), \@lons);
	print STDERR "done\nBuilding locations array...";



	for (my $yIndex = 0; $yIndex < $#lats; $yIndex++)
	{
		my $latRad = deg2rad(90.0 - $lats[$yIndex]);
		for (my $xIndex = 0; $xIndex < $#lons; $xIndex++)
		{
			push(@dataLocs, { lat => $latRad, 
					  lon => deg2rad($lons[$xIndex]),
					  coords => {
							xLoc => $xIndex,
							yLoc => $yIndex}
					});
		}
	}

	# Returning a filled array.
	return(@dataLocs);
}

sub ScanMesonetData($)
{
	my $mesoFile = shift;

	# TODO: Maybe a better error handling?
	open(MESODATA, "<$mesoFile") or die "Could not open file: $mesoFile. $!\n";
	
	
	my %mesoData = ();
	my $lineRead;

	# Read the file... grabbing relevant datapoints.
	while (defined($lineRead = <MESODATA>))
	{
		if ($lineRead =~ m/^ ([A-Z]{3}[A-Z2])\s+\d+\s+\d+\s+(\S+)\s+(\S+)\s+\S+\s+(\S+)\s+(\S+)\s+\S+\s+\S+\s+\S+\s+(\S+)\s+(\S+)/)
		{
			# don't bother recording any stations where they don't have data for rain
			# because that is the verification datapoint I need for training.
			if ($6 >= 0.0)
			{
				my $wdir = ($5 < -900.0 ? 'nan' : $5 * (3.14 / 180.0));
				my $wspd = ($4 < -900.0 || $wdir eq 'nan' ? 'nan' : $4);

				$mesoData{$1} = {
							relh => ($2 < -900.0 ? 'nan' : $2),
							tair => ($3 < -900.0 ? 'nan' : $3),
							uwnd => ($wspd eq 'nan' ? 'nan' : -sin($wdir)*$wspd),
							vwnd => ($wspd eq 'nan' ? 'nan' : -cos($wdir)*$wspd),
							rain => $6,
							press => ($7 < 700.0 ? 'nan' : $7)
						};
			}
		}
	}

	close(MESODATA);

	return(%mesoData);
}

sub GetMesonetData($$)
{
	my $isAfter = shift;
	my $mainTime = shift;	

	my $baseURL = 'http://www.mesonet.org/data/public/mesonet/mdf';

	my $mesoFile1 = GrabMesonetFile($baseURL, $mainTime);

	if ($mesoFile1 eq "")
	{
		# TODO: better error handling?
		# TODO: ABSOLUTELY!!!  This won't work as expected.
		return undef;
	}

	my %mesoData = ScanMesonetData($mesoFile1);
	
	if ($mainTime->hms() eq "00:00:00" && !$isAfter)
	{
		# Need to reset all the rain info...
		foreach my $statName (keys %mesoData)
		{
			$mesoData{$statName}->{'rain'} = 0.0;
		}
	}


	my $otherTime = ($isAfter ? $mainTime->clone->subtract( minutes => 5 )	# Time was rounded up
				  : $mainTime->clone->add( minutes => 5 ));	# Time was rounded down

	my $otherFile = GrabMesonetFile($baseURL, $otherTime);

	if ($otherFile eq "")
	{
		# TODO: better error handling?
		# TODO: ABSOLUTELY!  This won't work as expected
		return undef;
	}

	my %otherData = ScanMesonetData($otherFile);

	if ($otherTime->hms() eq "00:00:00" && $isAfter)
	{
		# need to reset the rainfall info...
		foreach my $statName (keys %otherData)
		{
			$otherData{$statName}->{'rain'} = 0.0;
		}
	}
	
	# The above is to handle a special case situation.
	# When the data is at the reset (midnight), then it is effectively
	# reporting the rainfall since midnight of the day before.
	# In the case for calculating a rainfall rate, using this datapoint
	# the one five minutes from now will (likely) yield a negative rainrate.
	# This is the "reset" for the mesonet data.  Therefore, if we are at the
	# reset and the other datapoint will be a point in the future, not the past,
	# then reset the rainfall value to zero.
	# The other case would be if the time is at 5 minutes after midnight and the
	# other datapoint is the point that is 5 minutes before, at midnight!
	

	my %mergedData = MergeData(%mesoData, %otherData);

	return(%mergedData);
}


sub nanmean
{
	my $valsSum = 0.0;
	my $arrayCnt = 0;

	#print "nanmean: ";

	while (defined(my $val = shift))
	{
	#	print "$val ";
		next if ($val eq 'nan');
		$valsSum = $val + $valsSum;
		$arrayCnt++;
	}

	#print "    $valsSum / $arrayCnt\n";

	return($arrayCnt == 0 ? 'nan' : ($valsSum / $arrayCnt));
}

sub MergeData(\%\%)
{
	my $mainDataRef = shift;
	my $otherDataRef = shift;

	my %mergedData = ();

	while (my ($statName, $dataRef) = each(%$mainDataRef))
	{
		next if (!exists($otherDataRef->{$statName}));

		my $mainStatData = $dataRef;
		my $otherStatData = $otherDataRef->{$statName};

		my %mergedStatData = ();

		# Assimilate each variable...
		foreach my $varName (keys %$mainStatData)
		{
			if ($varName ne 'rain')
			{
				#print "$varName - $mainStatData->{$varName}  $otherStatData->{$varName} ";
				$mergedStatData{$varName} = nanmean($mainStatData->{$varName}, 
								    $otherStatData->{$varName});
			}
			else
			{
				$mergedStatData{'rate'} = abs($mainStatData->{'rain'} - $otherStatData->{'rain'}) 
								/ 0.08333333;
			}
		}

		$mergedData{$statName} = \%mergedStatData;
	}

	return(%mergedData);
}



sub GrabMesonetFile($$)
{
	my $baseURL = shift;
	my $dataTime = shift;

	my $mesoFile = $dataTime->strftime('%Y%m%d%H%M.mdf');
	my $directoryLoc = $dataTime->strftime('%Y/%m/%d');

	mkpath($directoryLoc, {mask => 0755});

	if (!(-e "$directoryLoc/$mesoFile"))
	{
		if (system("/usr/bin/wget -P $directoryLoc -nc $baseURL/$directoryLoc/$mesoFile") != 0)
		{
			print STDERR "ERROR: Could not download file: $directoryLoc/$mesoFile\n";
			return "";
		}
	}

	return "$directoryLoc/$mesoFile";
}

sub GetRainfall($)
{
	my $mesoFile = shift;

	# may still need better error handling here...
       	open(MESODATA, "<$mesoFile") or die "Could not open file: $mesoFile\n";

	my %statData = ();

	my $lineRead = '';

	# obtaining the stations' rain since midnight data
        while (defined($lineRead = <MESODATA>))
	{
                if ($lineRead =~ m/^ ([A-Z]{3}[A-Z2])\s+\d+\s+\d+\s+(?:\S+\s+){8}(\S+)/)
               	{
			# Don't bother recording any stations that don't have rain info...
			if ($2 >= 0.0)
			{
                       		$statData{$1} = $2;
			}
               	}
        }

	close(MESODATA);

	return %statData;
}

sub LoadStationList($)
{
	my $filename = shift;

	open(STATLIST, "<$filename") or die "Could not open file '$filename'\n";

	my %statLocs = ();
	my $LineRead = '';

	while (defined($LineRead = <STATLIST>))
	{
		chomp($LineRead);
		# load up the statLat and statLon hashes.
		my @lineVals = split(/,/, $LineRead);

		# Get rid of the quotes in the Station name field
		$lineVals[1] =~ s/^\"|\"$//g;

		$statLocs{$lineVals[1]} = {
					    lat => deg2rad(90.0 - $lineVals[2]),
					    lon => deg2rad($lineVals[3]),
					    coords => {
							xLoc => -1,
							yLoc => -1
						      }
					  };
	}

	close(STATLIST);

	return(%statLocs);
}

sub NearestMinute($$)
{
	my $dateTime = shift;
	my $nearestMinute = shift;

	# calculate fractional minutes
	my $fracMin = $dateTime->minute() + ($dateTime->fractional_second() / 60.0);

	my $roundedMin = nearest($nearestMinute, $fracMin);

	# use round(), not int() because the result might be something like -3.999999999999
	# for which int()'ing will yield the wrong answer.
	return($dateTime->clone->add(seconds => round(60.0 * ($roundedMin - $fracMin))));
}


