#!/usr/bin/env python
#    Author: Benjamin Root
#    Copyright (C) 1989, 1991-2009 Free Software Foundation.
#    
#    This program is free software; you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation; either version 3 of the License, or
#    (at your option) any later version.
#    
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#    
#    You should have received a copy of the GNU General Public License
#    along with this program. If not, see http://www.gnu.org/licenses/.

import os			# for os.sep
import matplotlib.pyplot as pyplot
import numpy

def MakeErrorBars(bootMeans, bootCIs, models, axis) :
    axis.errorbar(numpy.arange(len(models)) + 1, 
		  bootMeans, yerr=numpy.array([bootMeans - bootCIs[:, 0],
                                               bootCIs[:, 1] - bootMeans]),
                  fmt='.', ecolor='k', elinewidth=1.5, capsize=10, markersize=16, color='k')
    axis.set_xticks(numpy.arange(len(models)) + 1)
    axis.set_xticklabels(models, fontsize='medium')
    axis.set_xlim((0.5, len(models) + 0.5))

if __name__ == '__main__':
    from optparse import OptionParser   # Command-line parsing

    parser = OptionParser()
    parser.add_option("-r", "--run", dest="projectName", type="string",
                      help="Use data from PROJECT run", metavar="PROJECT")
    parser.add_option("-d", "--dir", dest="dataDir", type="string",
                      help="Data exists at SRC", metavar="SRC", default=".")
    parser.add_option("-m", "--model", dest="models", action="append", type="string",
                      help="Use MODEL in the images", metavar="MODEL")
    parser.add_option("-f", "--format", dest="outputFormat", type="string",
                      help="Desired FORMAT for the output images", metavar="FORMAT", default="png")
    parser.add_option("-s", "--stat", dest="stats", action="append", type="string",
		      help="Create images for STAT", metavar="STAT")

    (options, args) = parser.parse_args()
    destDir = '.'

    if options.projectName is None : parser.error("Missing PROJECT!")
    if len(options.models) == 0 : parser.error("No models given!")
    if len(options.stats) == 0 : parser.error("No Stats given!")



    statNamesFull = {'Corr': 'Correlation Coefficient',
                     'RMSE': 'Root Mean Squared Error [mm/hr]',
                     'MAE': 'Mean Absolute Error [mm/hr]'}

    statNamesTitle = {'Corr': 'Correlations',
		      'RMSE': 'RMSEs',
		      'MAE': 'MAEs'}

    fig = pyplot.figure(figsize=(18.75, 5))

    for statIndex, statName in enumerate(options.stats) :


        bootCIs = numpy.loadtxt(os.sep.join([options.dataDir, options.projectName, 'bootstrap_CI_%s.txt' % statName]))
	bootMeans = numpy.loadtxt(os.sep.join([options.dataDir, options.projectName, 'bootstrap_Mean_%s.txt' % statName]))
        

	print bootCIs
        print bootMeans

        ax = fig.add_subplot(1, len(options.stats), statIndex + 1)
        MakeErrorBars(bootMeans, bootCIs, options.models, ax);

        ax.set_ylabel(statNamesFull[statName], fontsize='large');
        ax.set_xlabel('Models', fontsize='large');
        ax.set_title('Mean Model %s' % statNamesTitle[statName], fontsize='large');
                                           
#        saveas(gcf, ['Models' statFileStems{statIndex} '_Raw.' outputFormat]);


    fig.savefig('%s%sModelPerformances.%s' % (destDir, os.sep, options.outputFormat),
		transparent=True, bbox_inches='tight')



    


