#!/usr/bin/perl -w

use strict;

sub Decimate($$$$\%);

# This program reads the CSV file produced by 'buildtraining.pl' and creates
# an ARFF file. It also attempts to 'balance' the training set so that
# it doesn't have a severe bias of low rainfall rate cases.

my $inputFilename = "trainingData2.csv";
my $outputFilename = "filttest_rate_trainingData";
my $altoutputFilename = "filt_reflect_trainingData";


open(TRAIN_IN, "<$inputFilename") or die "Could not open CSV training file! $!\n";



my $lineRead;

#my %rainhash = ();
#my %reflecthash = ();
my %joinhash;
my $obsTotal = 0;

while ($lineRead = <TRAIN_IN>)
{
	chomp($lineRead);
	my @lineVals = split(/,/, $lineRead);

#	$rainhash{int($lineVals[5])}++;
#	$reflecthash{int($lineVals[4])}++;

	next unless ($lineVals[3] ne 'nan' && $lineVals[4] ne 'nan' && $lineVals[3] <= 53);
#	my $tempVal = int($lineVals[4]) . ' ' . int($lineVals[5]);
	#print "$tempVal\n";
	my $keyVal = sprintf("%d", $lineVals[4]);
	$joinhash{$keyVal}++;
	$obsTotal++;
}

close TRAIN_IN;

#Decimate(0.05, $obsTotal, $outputFilename, $inputFilename, 5, %rainhash);
Decimate(0.05, $obsTotal, $outputFilename, $inputFilename, %joinhash);

exit;



sub Decimate($$$$\%)
{
	my $decimation = shift;
	my $obsTotal = shift;
	my $outfileName = shift;
	my $inputFilename = shift;
#	my $decimateIndex = shift;
	my $hashRef = shift;

	my %newValhash = ();
	my @sortedKeys = sort {$a <=> $b} keys(%$hashRef);

	my $binCount = scalar(@sortedKeys);
	foreach my $keyVal (@sortedKeys)
	{
		$newValhash{$keyVal} = 0;
	}

	print "BinCount: $binCount\n";

#exit;

	open(TRAIN_OUT_ARFF, ">$outfileName.arff") or die "Could not open ARFF training file! $!\n";
	open(TRAIN_OUT_CSV, ">$outfileName.csv") or die "Could not open CSV training file! $!\n";


	print TRAIN_OUT_ARFF q/@relation Z-R

@attribute temperature NUMERIC
@attribute relHumidity NUMERIC
@attribute pressure NUMERIC
@attribute reflectivity NUMERIC
@attribute rainrate NUMERIC

@data/;

	print TRAIN_OUT_ARFF "\n";

	my $newObsTotal = 0;

	open(TRAIN_IN, "<$inputFilename") or die "Could not re-open CSV training file! $!\n";

	while ($lineRead = <TRAIN_IN>)
	{
		chomp($lineRead);
		my @lineVals = split(/,/, $lineRead);

		next unless ($lineVals[3] ne 'nan' && $lineVals[4] ne 'nan' && $lineVals[3] <= 53);
		
		#print "$lineVals[0], $lineVals[4], $lineVals[5]\n";

	        # This if-statement has the effect of only printing out a percentage
        	# of the total number of records in the complete training set
		# produced by 'buildtraining.pl'. The percentage of records to print
		# is a function of the record's rainfall rate value.
		# This allows for only a small percentage of the
		# low rainfall rate cases to get through, effectively
		# balancing the training set.

		# The printing statement also converts any NaNs into '?',
		# which is what ARFF format uses for missing values.

	        # If the rainfall rate is 0.0, then use a fixed value,
        	# otherwise, use the equation which gives a value based
	        # the data's rainfall rate value.
        	#my $promoterCoeff = (($lineVals[4] + 15) / 20)**2.0;

#		my $keyValue = int($lineVals[4]) . ' ' . int($lineVals[5]);
		my $keyValue = sprintf("%d", $lineVals[4]);
		my $threshold = ($obsTotal*$decimation)/($binCount*$hashRef->{$keyValue});

		#print "$threshold\n";



		if (rand() <= $threshold)   #($lineVals[5]  ? 0.001 : ($lineVals[5]/55.5)**1.5))
		{
			$newValhash{$keyValue}++;
			$newObsTotal++;	
			print TRAIN_OUT_CSV "$lineRead\n";
		        $lineRead =~ s/nan/\?/g;
			print TRAIN_OUT_ARFF "$lineRead\n";
		}
	}

	close TRAIN_IN;
	close TRAIN_OUT_ARFF;
	close TRAIN_OUT_CSV;

#	foreach my $val (@sortedKeys)
#	{
#		printf("%s %6d %6d   %.5f %.5f\n", $val, $hashRef->{$val}, $newValhash{$val},
#					    $hashRef->{$val}/$obsTotal, $newValhash{$val}/$newObsTotal);
#	}

	print "-----------------------------------------------------\n";
	printf("Summary %6d %6d   %.5f %.5f\n", $obsTotal, $newObsTotal, $obsTotal/$binCount, $newObsTotal/$binCount);
	print "Bin Count: $binCount\n";
	print "Desired Decimation: $decimation    Actual Decimation: ".$newObsTotal/$obsTotal."\n";
}
