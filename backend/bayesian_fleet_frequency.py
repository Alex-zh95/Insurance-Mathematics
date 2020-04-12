"""
Filename:   bayes_freq.py
Author:     Alex-zh

Date:       2020-04-12

The Bayesian approach to estimating claims frequency combines collateral information to generate a prior distribution and then calulates a posterior frequency claims expectation with credibility factor.

The approach implemented here is the Poisson/Gamma model as the prior distribution (collateral data) is assumed to be Gamma distributed.

Required format of risk data: (nx2)-table with column names "Year", "Claim_count", "Vehicle_Year"
Required format of collateral data: (nx2)-table with column names "Client", "Claim_frequency", "Vehicle_Year"
"""

import pandas as pd

from scipy import stats
from scipy.optimize import minimize

# Display format for dataframes
pd.options.display.float_format = '{:,.2f}'.format

# 1. IMPORT AND PRESENT RISKS
risk_file = "./Fakedata/RISK_FILE.csv"
collateral_file = "./Fakedata/COLLATERAL_FILE.csv"
decimal_encoding = "," # Depends on if using decimal commas or points

risk_data = pd.read_csv(risk_file, decimal=decimal_encoding)
collateral_data = pd.read_csv(collateral_file, decimal=decimal_encoding)

# Calculate the own frequency distribution from risk
risk_data["Claim_frequency"] = risk_data["Claim_count"] / risk_data["Vehicle_Year"]

# Present the raw risk data (comparatively will not be large)
print(risk_data)

# Print summary statistics of the collateral frequency
print("Summary statistics of collateral frequency")
print(collateral_data["Claim_frequency"].describe())

# 2. GENERATE GAMMA PRIOR DISTRIBUTION FROM COLLATERAL
def gnlogl(theta, x):
    """
    Negative of the loglikelihood function for Gamma distribution.
    """
    s = 0
    alpha = theta[0]
    beta = theta[1]
    for i in range(len(x)):
        s -= stats.gamma.logpdf(x[i], a=alpha, loc=0, scale=1/beta) # Python "scale" is actually rate
    return s

# Get initial guess with method of moments
alpha_start = collateral_data["Claim_frequency"].mean()**2 / collateral_data["Claim_frequency"].var()
beta_start = collateral_data["Claim_frequency"].mean() / collateral_data["Claim_frequency"].var()
theta_start = [alpha_start, beta_start]

# To obtain maximum loglikelihood, we can equivalently minimize gnlogl
output = minimize(gnlogl, x0=theta_start, args=(collateral_data["Claim_frequency"]), method="Nelder-Mead")
print("MLE Completion Results")
print(output)

params = [output.x[0], 0, 1/output.x[1]]

# Test the fit with the supplied data at 95% conf
ks_result = stats.kstest(collateral_data["Claim_frequency"], "gamma", params)

print("1-sample Komolgorov-Smirnoff test of Gamma distribution of the collateral claims frequency.")
print("Test statistic:", format(ks_result.statistic, ".2f"))
print("p value:", format(ks_result.pvalue, ".5f"))

if ks_result.pvalue <= 0.05:
    print("Warning: strong significance to reject the Gamma fit at 95%!")

# 3. GENERATE CREDIBILITY FACTOR AND BAYESIAN FREQUENCY ESTIMATE
alpha = params[0]
beta = 1/params[2] # Python prodces (shape, rate) rather than (shape, scale), but scale = 1/rate
z = len(risk_data) / (beta + len(risk_data))

print("Credibility factor:", format(z, ".3f"))

# Print the Bayesian average
bayes_freq = z*risk_data["Claim_frequency"].mean() + (1-z)*(alpha/beta)
print("Bayesian expected frequency:", format(bayes_freq, ".2f"))
