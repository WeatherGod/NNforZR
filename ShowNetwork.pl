#!/usr/bin/perl -w


use strict;

sub DisplayStructure(\%);
sub ShowNode($$$$$);
sub GatherModelInfo($);
sub GatherModelResults($);
sub GetNode($);

my $inputfile = shift @ARGV;

if (!defined($inputfile))
{
	print STDERR "ERROR: missing command-line arguement\n";
	exit(1);
}

open(DATASTREAM, "<$inputfile") or die "Could not open NN description file, $inputfile, for reading: $!\n";

my %nnStructure = ();
my @modelResults = ();

while (my $lineRead = <DATASTREAM>)
{
	chomp($lineRead);

	if ($lineRead =~ m/=== Run information ===/)
	{
		next; #  %runData = GatherRunData(\*DATASTREAM);
	}
	elsif ($lineRead =~ m/=== Classifier model/)
	{
		print "Reading ModelInfo...\n";
		%nnStructure = GatherModelInfo(\*DATASTREAM);
	}
	elsif ($lineRead =~ m/=== Predictions on training set ===/)
	{
		next; #  @modelResults = GatherModelResults(\*DATASTREAM);
	}
	elsif ($lineRead =~ m/=== Summary ===/)
	{
		next;
	}
}


close DATASTREAM;

DisplayStructure(%nnStructure);


exit;


sub DisplayStructure(\%)
{
	my $nnStruct = shift;
#	my %nnStruct = %$tempRef;

	my $nodeListRef = $nnStruct->{outputNodes};
	my @nodeList = sort(@$nodeListRef);
	foreach my $outNode (@nodeList)
	{
		print "$outNode ".$nnStruct->{nodes}." ".$nnStruct->{nodes}->{$outNode}."\n";
		ShowNode($nnStruct->{nodes}->{$outNode}, $outNode, $nnStruct->{nodes}, 0, 0);
		print "\n\n";
	}
}

sub ShowNode($$$$$)
{
	my $nodeRef = shift;
	my $nodeName = shift;
	my $hiddenRef = shift;
	my $layerCnt = shift;
	my $isNewLine = shift;

	my $weightsHash = $nodeRef->{weights};

	my @nodeList = sort(keys(%$weightsHash));

	foreach my $linkedNode (@nodeList)
	{
		if ($isNewLine)
		{
			for (my $tabIndex = 0; $tabIndex < $layerCnt; $tabIndex++)
			{
				print "                       ";
			}

			$isNewLine = 0;
		}

		printf("->%5.5s (%6.2f %6.2f)", $linkedNode, $weightsHash->{$linkedNode}, $nodeRef->{threshold});

		if (exists($hiddenRef->{$linkedNode}))
		{
			$isNewLine = ShowNode($hiddenRef->{$linkedNode}, $linkedNode, $hiddenRef, $layerCnt + 1, $isNewLine);
		}
		else
		{
			print "\n";
			$isNewLine = 1;
		}
	}

	print "\n";

	return($isNewLine);
}
	

sub GatherModelResults($)
{
	my $fileHandle = shift;

	my @modelResults = ();

	return(@modelResults);
}

sub GatherRunData($)
{
	my $fileHandle = shift;

	my $layerStruct = 'a';
	my @attribs = ();
	my $testMode = 0;

#	my %runData = ( layerStruct => 'a',
#			attribs => (),
#			testMode => 0 );

	while (my $lineRead = <$fileHandle>)
	{
		chomp($lineRead);

		if($lineRead =~ m/Scheme:\s+weka\..*MultilayerPerceptron.* -H "(.*)"/)
		{
			$layerStruct = $1;
		}
		elsif ($lineRead =~ m/Attributes:\s+(\d+)/)
		{
			my $attrCnt = $1;
			my $index = 0;

			while (($index < $attrCnt) && ($lineRead = <$fileHandle>))
			{
				$lineRead =~ s/^\s*(\S*)\s*/$1/;

				push(@attribs, $lineRead);
				$index++;
			}
		}
		elsif ($lineRead =~ m/Test mode:\s+(.*)$/)
		{
			# Don't care right now...
			$testMode = 0;
		}
	}

	return( layerStruct => $layerStruct,
		attribs	    => @attribs,
		testMode    => $testMode );
}


sub GatherModelResults($)
{
	my $fileHandle = shift;

	my @modelResults = ();

	my $lineRead = <$fileHandle>;

	while (my $lineRead = <$fileHandle>)
	{
		chomp($lineRead);

		if ($lineRead =~ m/=== .* ===/)
		{
			last;
		}

		if ($lineRead =~ m/^\s+(\S+)\s+(\S+)\s+(\S+)\s+(\S+)/)
		{
			push(@modelResults, $3);
		}
	}

	return(@modelResults);
}

sub GatherModelInfo($)
{
	my $fileHandle = shift;

#	my %nnStructure = ( nodes => () );

	my %nodes = ();
	my @hiddenNodes = ();
	my @outputNodes = ();

	my $lineRead = <$fileHandle>;

	while (defined($lineRead))
	{
		chomp($lineRead);

#		print "$lineRead\n";

		if ($lineRead =~ m/Linear Node (\d+)/)
		{
			my $nodeNum = $1;
			print "NodeNum: $nodeNum\n";
			push(@outputNodes, $nodeNum);
			($lineRead, $nodes{$nodeNum}) = GetNode($fileHandle);
			print "LineRead: $lineRead\n";

		}
		elsif ($lineRead =~ m/Sigmoid Node (\d+)/)
		{
			my $nodeNum = $1;
			print "SigNodeNum: $nodeNum\n";
			push(@hiddenNodes, $nodeNum);
			($lineRead, $nodes{$nodeNum}) = GetNode($fileHandle);
		}
		elsif ($lineRead =~ m/^\s*$/)
		{
			$lineRead = <$fileHandle>;
		}
		else
		{
			last;
		}
	}
	
	
#	$nnStructure{hiddenNodes} = @hiddenNodes;
#	$nnStructure{outputNodes} = @outputNodes;

	print "nodes ref: ".\%nodes."\n";

	return( nodes => \%nodes,
		hiddenNodes => \@hiddenNodes,
		outputNodes => \@outputNodes );
}

sub GetNode($)
{
	my $fileHandle = shift;
#	my $tempRef = shift;
#	my $lineRead = $$tempRef;

	my $threshold = undef;
	my %weights = ();
	my %nodeHash = ();


	while (my $lineRead = <$fileHandle>)
	{
		chomp($lineRead);

				
		if ($lineRead =~ m/Inputs\s+Weights/)
		{
			next;
		}
		elsif ($lineRead =~ m/Threshold\s+(\S+)/)
		{
			$threshold = $1;
		}
		elsif ($lineRead =~ m/Node (\d+)\s+(\S+)/)
		{
			$weights{$1} = $2;
		}
		elsif ($lineRead =~ m/Attrib (\w+)\s+(\S+)/)
		{
			$weights{$1} = $2;
		}
		else
		{
			%nodeHash = ( threshold => $threshold,
				      weights => \%weights );
			return($lineRead, \%nodeHash);
		}
	}

	print STDERR "Unexpected end of file while reading a node!\n";

	%nodeHash = ( threshold => $threshold,
		      weights => \%weights);

	return(undef, \%nodeHash);
}
