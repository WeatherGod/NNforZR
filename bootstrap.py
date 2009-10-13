"""Bootstrap statistics package.
Given an experimentally determined random distribution, estimates
a desired parameter and its uncertainty.  
by Michael J.T. O'Kelly  <mokelly@mit.edu>
Version 0.1, 3-08-06"""

import scipy

def fast_bootstrap(function, distribution,
				   rel_tol = 0.001, abs_tol = 0,
				   min_samples = 10, max_samples = 1000,
				   verbose = 0, report_interval=10000):
	"""Bootstrap determination of value/error of function applied to
	distribution.  Distribution must be in format compatible with
	numpy.  (Any acceptable argument to scipy.array() will work.)
	Function should be written to act efficiently on
	numpy arrays.  
	rel_tol gives maximum sufficient std/mean ratio of answer.
	abs_tol gives maximum sufficient std of answer.
	min_samples is minimum number before completion-checking begins
	max_samples gives maximimum # of resamplings of distribution.  Set
	to <=0 for no limit.
	Returns result when any of rel_tol, abs_tol or max_samples reached.  
	verbose = 1 prints progress info and final state info
	Returns a tuple of form ( E(f(D)), std(f(D)) where D is a random
	resampling of the distribution argument."""

	x_cumulant = 0
	x2_cumulant = 0
	n_samples = 0
	d = scipy.array(distribution, copy = 0) # Don't copy if possible
	sample_size = len(d)

	while 1:
		# Choose #sample_size members of d at random, with replacement
		choices = scipy.random.random_integers(0, sample_size-1, sample_size)
		sample = d[choices]
		# Apply function to sample of random distribution
		f_of_d = function(sample)
		x_cumulant += f_of_d
		x2_cumulant += f_of_d**2
		n_samples += 1
		if n_samples>=min_samples:
			mu = x_cumulant / n_samples # E(f(D))
			sigma = ((x2_cumulant*n_samples - x_cumulant**2) /
					 (n_samples * (n_samples-1)) )**.5   # std(f(d))
			error = sigma / n_samples**.5
			if (verbose and n_samples % report_interval == 0):
				print "Mean", mu, "Std", sigma, "found after", n_samples, "samples"
			if ((n_samples >= max_samples and max_samples>0) or
				error <= abs_tol or
				error/mu <= rel_tol):
				if verbose:
					print "Mean", mu, "Std", sigma, "found after", n_samples, "samples"
				return (mu, sigma)
			

if __name__ == '__main__':
	dist = scipy.randn(40) + 10
	print dist
	result = fast_bootstrap(scipy.std, dist, verbose = 1, max_samples = 0, rel_tol = .0005)
	print "(Estimate, uncertainty)"
	print result
	print "Actual measured standard deviation:", dist.std()


	